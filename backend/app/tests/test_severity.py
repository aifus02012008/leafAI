"""Unit tests for lesion severity measurement (% lesion area within the leaf)."""
import numpy as np
import pytest
from PIL import Image

from app.services.severity import measure_severity

GREEN = (50, 150, 50)
BROWN = (120, 70, 30)
WHITE = (245, 245, 245)


def _leaf_image(tmp_path, lesion_frac: float, name: str, scale: int = 1) -> str:
    """White background, green 200x200 leaf square, brown lesion square covering lesion_frac of the leaf."""
    size = 400 * scale
    img = np.full((size, size, 3), WHITE, dtype=np.uint8)
    leaf0, leaf1 = 100 * scale, 300 * scale
    img[leaf0:leaf1, leaf0:leaf1] = GREEN
    if lesion_frac > 0:
        side = int(round((200 * scale) * lesion_frac ** 0.5))
        img[leaf0:leaf0 + side, leaf0:leaf0 + side] = BROWN
    path = tmp_path / name
    Image.fromarray(img).save(path)
    return str(path)


def test_healthy_leaf_has_near_zero_severity(tmp_path):
    result = measure_severity(_leaf_image(tmp_path, 0.0, "healthy.png"))
    assert result is not None
    assert result.severity_pct < 1.0


@pytest.mark.parametrize("frac", [0.1, 0.25, 0.5])
def test_severity_matches_lesion_fraction(tmp_path, frac):
    result = measure_severity(_leaf_image(tmp_path, frac, f"l{frac}.png"))
    assert result is not None
    assert result.severity_pct == pytest.approx(frac * 100, abs=3.0)


def test_severity_is_independent_of_image_scale(tmp_path):
    small = measure_severity(_leaf_image(tmp_path, 0.25, "s.png", scale=1))
    big = measure_severity(_leaf_image(tmp_path, 0.25, "b.png", scale=2))
    assert small.severity_pct == pytest.approx(big.severity_pct, abs=2.0)


def test_no_leaf_returns_none(tmp_path):
    path = tmp_path / "blank.png"
    Image.new("RGB", (300, 300), WHITE).save(path)
    assert measure_severity(str(path)) is None


def test_unreadable_file_returns_none(tmp_path):
    path = tmp_path / "bad.jpg"
    path.write_bytes(b"not an image")
    assert measure_severity(str(path)) is None


def test_white_glare_inside_leaf_is_not_lesion(tmp_path):
    img = np.full((400, 400, 3), WHITE, dtype=np.uint8)
    img[100:300, 100:300] = GREEN
    img[150:170, 150:170] = (250, 250, 250)  # specular glare spot inside the leaf
    path = tmp_path / "glare.png"
    Image.fromarray(img).save(path)
    result = measure_severity(str(path))
    assert result is not None and result.severity_pct < 1.0
