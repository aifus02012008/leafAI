"""Unit tests for PHI (pre-harvest interval) and treatment-response rules."""
from datetime import date

import pytest

from app.services.treatment_rules import (
    SprayRecord,
    evaluate_response,
    harvest_safe_date,
    suggest_rotation,
)
from app.db.seed.actives import ACTIVE_INGREDIENTS


# ---------- PHI ----------

def test_harvest_date_single_spray():
    result = harvest_safe_date([SprayRecord(applied_on=date(2026, 11, 20), phi_days=7)])
    assert result == date(2026, 11, 27)


def test_harvest_date_uses_latest_constraint():
    sprays = [
        SprayRecord(applied_on=date(2026, 11, 1), phi_days=21),   # -> 22/11
        SprayRecord(applied_on=date(2026, 11, 18), phi_days=3),   # -> 21/11
        SprayRecord(applied_on=date(2026, 11, 10), phi_days=14),  # -> 24/11
    ]
    assert harvest_safe_date(sprays) == date(2026, 11, 24)


def test_harvest_date_ignores_unknown_phi():
    assert harvest_safe_date([SprayRecord(applied_on=date(2026, 1, 1), phi_days=None)]) is None
    assert harvest_safe_date([]) is None


def test_negative_phi_rejected():
    with pytest.raises(ValueError):
        SprayRecord(applied_on=date(2026, 1, 1), phi_days=-1)


# ---------- response verdict ----------

def test_lesions_stable_is_effective():
    assert evaluate_response(10.0, 10.5).verdict == "effective"


def test_lesions_shrinking_is_effective():
    assert evaluate_response(10.0, 6.0).verdict == "effective"


def test_moderate_growth_is_unclear():
    assert evaluate_response(10.0, 12.0).verdict == "unclear"


def test_large_growth_is_ineffective():
    out = evaluate_response(10.0, 15.0)
    assert out.verdict == "ineffective"
    assert out.relative_change == pytest.approx(0.5)


def test_tiny_baseline_uses_floor_to_avoid_noise():
    # 0.2% -> 0.4% is a doubling but practically negligible
    assert evaluate_response(0.2, 0.4).verdict == "effective"


def test_missing_measurement_is_inconclusive():
    assert evaluate_response(None, 5.0).verdict == "inconclusive"
    assert evaluate_response(5.0, None).verdict == "inconclusive"


# ---------- rotation ----------

def test_rotation_excludes_same_moa_group_and_banned():
    by_code = {a["code"]: a for a in ACTIVE_INGREDIENTS}
    used = by_code["difenoconazole"]
    candidates = [by_code[c] for c in ("hexaconazole", "azoxystrobin", "mancozeb", "carbendazim")]
    suggestions = suggest_rotation(used, candidates)
    codes = [s["code"] for s in suggestions]
    assert "hexaconazole" not in codes        # same FRAC group 3
    assert "carbendazim" not in codes         # banned in Vietnam
    assert codes == ["azoxystrobin", "mancozeb"]


def test_active_catalog_is_well_formed():
    codes = [a["code"] for a in ACTIVE_INGREDIENTS]
    assert len(codes) == len(set(codes))
    for a in ACTIVE_INGREDIENTS:
        assert a["kind"] in {"fungicide", "insecticide", "acaricide", "bactericide"}
        assert a["name"]
