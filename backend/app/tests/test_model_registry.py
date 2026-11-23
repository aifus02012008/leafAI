"""Unit tests for ModelRegistry: availability, lazy loading, LRU eviction, load failures."""
from dataclasses import replace

import pytest

from app.core.crops import get_crop
from app.services import model_registry as registry_module
from app.services.model_registry import ModelRegistry, ModelUnavailableError


class _StubDetector:
    instances = 0

    def __init__(self, crop):
        _StubDetector.instances += 1
        self.version = crop.model_version
        self.class_names = {0: "Healthy"}

    def detect(self, image_path):
        return []


@pytest.fixture
def weights(tmp_path):
    def _make(code: str):
        path = tmp_path / f"{code}.pt"
        path.write_bytes(b"fake")
        return replace(get_crop(code), weights_path=str(path))
    return _make


@pytest.fixture
def stub_yolo(monkeypatch):
    _StubDetector.instances = 0
    monkeypatch.setattr(registry_module, "YoloDetector", _StubDetector)


def test_crop_without_weights_is_unavailable():
    crop = replace(get_crop("durian"), weights_path="/nonexistent/durian.pt")
    registry = ModelRegistry(max_loaded=2)
    assert registry.is_available(crop) is False
    with pytest.raises(ModelUnavailableError):
        registry.get(crop)


def test_model_is_loaded_once_and_cached(weights, stub_yolo):
    registry = ModelRegistry(max_loaded=2)
    crop = weights("durian")
    first = registry.get(crop)
    second = registry.get(crop)
    assert first is second
    assert _StubDetector.instances == 1
    assert registry.is_loaded("durian")
    assert registry.class_names("durian") == {0: "Healthy"}


def test_least_recently_used_model_is_evicted(weights, stub_yolo):
    registry = ModelRegistry(max_loaded=2)
    durian, mangosteen, rambutan = weights("durian"), weights("mangosteen"), weights("rambutan")
    registry.get(durian)
    registry.get(mangosteen)
    registry.get(durian)  # durian becomes most recently used
    registry.get(rambutan)
    assert registry.is_loaded("durian")
    assert registry.is_loaded("rambutan")
    assert not registry.is_loaded("mangosteen")


def test_load_failure_is_reported(weights, monkeypatch):
    def _boom(crop):
        raise RuntimeError("corrupt weights")

    monkeypatch.setattr(registry_module, "YoloDetector", _boom)
    registry = ModelRegistry(max_loaded=2)
    with pytest.raises(ModelUnavailableError):
        registry.get(weights("durian"))
    assert "corrupt weights" in registry.load_error("durian")
    assert not registry.is_loaded("durian")


def test_registered_override_takes_precedence(weights, stub_yolo):
    registry = ModelRegistry(max_loaded=1)
    crop = replace(get_crop("mangosteen"), weights_path=None)
    override = _StubDetector(crop)
    registry.register("mangosteen", override)
    assert registry.is_available(crop)
    assert registry.get(crop) is override
    registry.unregister("mangosteen")
    assert not registry.is_available(crop)
