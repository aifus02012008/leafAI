"""Unit tests for the spray dose / cost calculator (pure functions)."""
import pytest

from app.services.dose_calculator import (
    AREA_UNITS_M2,
    DoseInput,
    DoseInputError,
    calculate_dose,
    to_square_meters,
)


def test_area_unit_conversions():
    assert to_square_meters(1, "ha") == 10_000
    assert to_square_meters(2, "sao_bac_bo") == 720
    assert to_square_meters(1, "sao_trung_bo") == 500
    assert to_square_meters(3, "cong") == 3_000
    assert to_square_meters(250, "m2") == 250
    assert set(AREA_UNITS_M2) == {"m2", "ha", "sao_bac_bo", "sao_trung_bo", "cong"}


def test_unknown_unit_rejected():
    with pytest.raises(DoseInputError):
        to_square_meters(1, "acre")


def test_dose_per_tank_label_one_hectare():
    # Label: 20 ml per 16 L tank; spray 500 L water per ha; user has 16 L tank.
    result = calculate_dose(DoseInput(
        area=1, area_unit="ha", tank_l=16,
        label_dose=20, label_dose_basis="per_tank", label_tank_l=16,
        water_l_per_ha=500,
    ))
    assert result.total_water_l == 500
    assert result.tanks_needed == 32  # ceil(500 / 16)
    assert result.product_per_tank == 20
    assert result.total_product == pytest.approx(625.0)  # 500 L * 20/16


def test_per_tank_dose_scales_to_user_tank_size():
    result = calculate_dose(DoseInput(
        area=1000, area_unit="m2", tank_l=25,
        label_dose=20, label_dose_basis="per_tank", label_tank_l=16,
        water_l_per_ha=400,
    ))
    assert result.product_per_tank == pytest.approx(31.25)
    assert result.total_water_l == pytest.approx(40)
    assert result.tanks_needed == 2


def test_dose_per_hectare_label():
    # Label: 1 L (1000 ml) product per ha in 500 L water; field is 2 sào Bắc Bộ (720 m2).
    result = calculate_dose(DoseInput(
        area=2, area_unit="sao_bac_bo", tank_l=16,
        label_dose=1000, label_dose_basis="per_ha",
        water_l_per_ha=500,
    ))
    assert result.area_m2 == 720
    assert result.total_product == pytest.approx(72.0)
    assert result.total_water_l == pytest.approx(36.0)
    assert result.tanks_needed == 3
    assert result.product_per_tank == pytest.approx(32.0)  # 1000 ml / 500 L * 16 L


def test_cost_estimate_uses_pack_price():
    result = calculate_dose(DoseInput(
        area=1, area_unit="ha", tank_l=16,
        label_dose=20, label_dose_basis="per_tank", label_tank_l=16,
        water_l_per_ha=480,
        pack_size=100, pack_price=50_000,
    ))
    assert result.total_product == pytest.approx(600)
    assert result.packs_needed == 6
    assert result.estimated_cost == pytest.approx(300_000)


def test_cost_is_none_without_price():
    result = calculate_dose(DoseInput(
        area=100, area_unit="m2", tank_l=16,
        label_dose=10, label_dose_basis="per_tank", label_tank_l=16, water_l_per_ha=500,
    ))
    assert result.estimated_cost is None
    assert result.packs_needed is None


@pytest.mark.parametrize("field,value", [
    ("area", 0), ("tank_l", -1), ("label_dose", 0), ("water_l_per_ha", 0),
])
def test_non_positive_inputs_rejected(field, value):
    params = dict(
        area=1, area_unit="ha", tank_l=16, label_dose=20,
        label_dose_basis="per_tank", label_tank_l=16, water_l_per_ha=500,
    )
    params[field] = value
    with pytest.raises(DoseInputError):
        calculate_dose(DoseInput(**params))


def test_per_tank_basis_requires_label_tank_size():
    with pytest.raises(DoseInputError):
        calculate_dose(DoseInput(
            area=1, area_unit="ha", tank_l=16, label_dose=20,
            label_dose_basis="per_tank", label_tank_l=None, water_l_per_ha=500,
        ))
