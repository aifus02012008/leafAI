"""Unit tests for the crop registry (app.core.crops)."""
import pytest

from app.core.crops import (
    CropNotFoundError,
    get_crop,
    list_crops,
)

EXPECTED_CODES = {"tea", "durian", "mangosteen", "rambutan", "guava", "pomelo"}


def test_registry_lists_all_supported_crops():
    codes = {crop.code for crop in list_crops()}
    assert codes == EXPECTED_CODES


def test_tea_is_first_and_default():
    assert list_crops()[0].code == "tea"


def test_each_crop_has_vietnamese_name_and_scientific_name():
    for crop in list_crops():
        assert crop.name_vi
        assert crop.scientific_name


def test_unknown_crop_raises():
    with pytest.raises(CropNotFoundError):
        get_crop("banana")


def test_crop_lookup_is_case_insensitive_and_trimmed():
    assert get_crop("  DURIAN ").code == "durian"


def test_tea_label_mapping_matches_legacy_mapping():
    from app.core.config import map_disease_label

    tea = get_crop("tea")
    for raw in ["Brown Blight", "Gray Blight", "Helopeltis", "Unknown label"]:
        assert tea.map_label(raw) == map_disease_label(raw)


def test_durian_label_mapping_uses_crop_specific_names():
    durian = get_crop("durian")
    mapped = durian.map_label("Leaf_Phytophthora")
    assert "Phytophthora" in mapped
    assert "sầu riêng" in mapped.lower()


def test_unmapped_label_passes_through_unchanged():
    assert get_crop("rambutan").map_label("Some_New_Class") == "Some_New_Class"


def test_healthy_label_detection_is_crop_specific():
    durian = get_crop("durian")
    assert durian.is_healthy_label("Healthy_leaf")
    assert durian.is_healthy_label("no_disease")
    assert not durian.is_healthy_label("Leaf_Phytophthora")


def test_threshold_lookup_falls_back_to_default():
    crop = get_crop("mangosteen")
    assert crop.threshold_for("never-seen-label") == crop.default_threshold


def test_tea_thresholds_match_legacy_settings():
    from app.core.config import settings

    tea = get_crop("tea")
    assert tea.threshold_for("Helopeltis") == settings.CLASS_CONFIDENCE_THRESHOLDS["Helopeltis"]
    assert tea.healthy_threshold == settings.CLASS_CONFIDENCE_THRESHOLDS["Healthy"]


def test_crop_config_is_immutable():
    crop = get_crop("tea")
    with pytest.raises(Exception):
        crop.code = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        crop.label_map["x"] = "y"  # type: ignore[index]
