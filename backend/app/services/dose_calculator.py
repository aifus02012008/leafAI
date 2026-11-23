"""Spray mixing calculator: how much product and water a field needs, and what it costs.

The label dose ALWAYS comes from the product label the grower is holding. This module
only does arithmetic; it never invents a dose. Pure functions, no I/O.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

# Vietnamese field-area units -> square meters.
AREA_UNITS_M2 = MappingProxyType({
    "m2": 1.0,
    "ha": 10_000.0,
    "sao_bac_bo": 360.0,
    "sao_trung_bo": 500.0,
    "cong": 1_000.0,  # công Nam Bộ (công tầm cấy)
})

DoseBasis = Literal["per_tank", "per_ha"]


class DoseInputError(ValueError):
    """Invalid calculator input (shown to the user)."""


@dataclass(frozen=True)
class DoseInput:
    area: float
    area_unit: str
    tank_l: float
    label_dose: float                 # ml or g, as printed on the label
    label_dose_basis: DoseBasis       # "per_tank" (per label_tank_l litres) or "per_ha"
    water_l_per_ha: float             # spray volume per hectare (from label / local practice)
    label_tank_l: float | None = None
    pack_size: float | None = None    # ml or g per bottle/sachet
    pack_price: float | None = None   # VND per bottle/sachet


@dataclass(frozen=True)
class DoseResult:
    area_m2: float
    total_water_l: float
    tanks_needed: int
    product_per_tank: float
    total_product: float
    packs_needed: int | None
    estimated_cost: float | None


def to_square_meters(area: float, unit: str) -> float:
    factor = AREA_UNITS_M2.get(unit)
    if factor is None:
        raise DoseInputError(f"Đơn vị diện tích không hợp lệ: {unit}")
    return area * factor


def _require_positive(name: str, value: float | None) -> None:
    if value is None or value <= 0:
        raise DoseInputError(f"Giá trị '{name}' phải lớn hơn 0.")


def _validate(inp: DoseInput) -> None:
    for name in ("area", "tank_l", "label_dose", "water_l_per_ha"):
        _require_positive(name, getattr(inp, name))
    if inp.label_dose_basis not in ("per_tank", "per_ha"):
        raise DoseInputError("Cách tính liều phải là 'per_tank' hoặc 'per_ha'.")
    if inp.label_dose_basis == "per_tank":
        _require_positive("label_tank_l", inp.label_tank_l)
    if (inp.pack_size is None) != (inp.pack_price is None):
        raise DoseInputError("Cần nhập đủ cả quy cách gói/chai và giá để ước tính chi phí.")
    if inp.pack_size is not None:
        _require_positive("pack_size", inp.pack_size)
        _require_positive("pack_price", inp.pack_price)


def _concentration_per_litre(inp: DoseInput) -> float:
    if inp.label_dose_basis == "per_tank":
        return inp.label_dose / inp.label_tank_l  # type: ignore[operator]
    return inp.label_dose / inp.water_l_per_ha


def calculate_dose(inp: DoseInput) -> DoseResult:
    _validate(inp)
    area_m2 = to_square_meters(inp.area, inp.area_unit)
    total_water = area_m2 / 10_000.0 * inp.water_l_per_ha
    conc = _concentration_per_litre(inp)
    total_product = conc * total_water

    packs = cost = None
    if inp.pack_size is not None and inp.pack_price is not None:
        packs = math.ceil(round(total_product / inp.pack_size, 6))
        cost = round(packs * inp.pack_price, 0)

    return DoseResult(
        area_m2=round(area_m2, 2),
        total_water_l=round(total_water, 2),
        tanks_needed=max(1, math.ceil(round(total_water / inp.tank_l, 6))),
        product_per_tank=round(conc * inp.tank_l, 2),
        total_product=round(total_product, 2),
        packs_needed=packs,
        estimated_cost=cost,
    )
