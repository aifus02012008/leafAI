"""Consistency checks between crop configuration and the disease library seed data."""
import re

from app.core.crops import list_crops
from app.db.seed import SEED_BY_CROP

STAGE_HEADER = re.compile(r"^Giai đoạn (\d+|cuối) — ", re.MULTILINE)
REQUIRED_FIELDS = ("class_name", "display_name", "description", "symptoms", "prevention", "treatment")


def test_every_crop_has_a_catalog():
    assert set(SEED_BY_CROP) == {crop.code for crop in list_crops()}
    assert all(len(items) > 0 for items in SEED_BY_CROP.values())


def test_label_map_targets_exist_in_catalog():
    """A detected disease must always link to a library entry for its crop (tea uses legacy names)."""
    for crop in list_crops():
        if crop.code == "tea":
            continue
        names = {item["class_name"] for item in SEED_BY_CROP[crop.code]}
        missing = set(crop.label_map.values()) - names
        assert not missing, f"{crop.code}: {missing}"


def test_class_names_unique_within_crop():
    for code, items in SEED_BY_CROP.items():
        names = [item["class_name"] for item in items]
        assert len(names) == len(set(names)), code


def test_entries_have_required_text():
    for code, items in SEED_BY_CROP.items():
        for item in items:
            for field in REQUIRED_FIELDS:
                assert item.get(field), f"{code}/{item.get('class_name')}: missing {field}"
            assert len(item["class_name"]) <= 100, "class_name exceeds DB column size"


def test_fruit_treatment_steps_follow_modal_format():
    for code in ("durian", "mangosteen", "rambutan"):
        for item in SEED_BY_CROP[code]:
            steps = item["treatment_steps"]
            headers = STAGE_HEADER.findall(steps)
            assert headers[-1] == "cuối", item["class_name"]
            assert len(headers) >= 3
            assert "• Hành động cần làm:" in steps
