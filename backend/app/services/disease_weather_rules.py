"""Which weather favours which leaf disease (pure, no I/O).

Each disease gets a WeatherProfile: what makes a single forecast day "favourable" for infection or
build-up. Profiles are matched by keywords in the canonical disease name, so they cover all four crops
(tea, durian, mangosteen, rambutan) without per-row configuration.

⚠️ Thresholds are initial agronomic assumptions pending review by a plant-protection specialist.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Kind = Literal["wet", "dry_day_humid_night", "dry_hot"]


class DayLike(Protocol):
    humid_hours: int   # hours with RH >= 90%
    t_min: float
    t_max: float
    precip_mm: float


@dataclass(frozen=True)
class WeatherProfile:
    key: str
    kind: Kind
    min_humid_hours: int = 6
    min_rain_mm: float = 5.0
    temp_low: float | None = None    # optimal daily-mean temperature band (°C)
    temp_high: float | None = None
    note: str = ""

    def favourable(self, day: DayLike) -> bool:
        mean_t = (day.t_min + day.t_max) / 2
        if self.temp_low is not None and mean_t < self.temp_low:
            return False
        if self.temp_high is not None and mean_t > self.temp_high:
            return False
        if self.kind == "wet":
            return day.humid_hours >= self.min_humid_hours or day.precip_mm >= self.min_rain_mm
        if self.kind == "dry_day_humid_night":
            # Powdery mildew: humid nights but little rain (heavy rain washes spores off).
            return 3 <= day.humid_hours <= 12 and day.precip_mm < 2
        return day.precip_mm < 2 and day.t_max >= 30  # dry_hot: sap-sucking pests, mites, sooty mould


PHYTOPHTHORA = WeatherProfile(
    "phytophthora", "wet", min_humid_hours=8, min_rain_mm=10, temp_low=23, temp_high=31,
    note="mưa lớn, đất ẩm úng thuận lợi cho Phytophthora (cháy lá, xì mủ)",
)
ANTHRACNOSE = WeatherProfile(
    "anthracnose", "wet", min_humid_hours=6, min_rain_mm=5, temp_low=22, temp_high=32,
    note="ẩm độ cao, mưa kéo dài thuận lợi cho nấm thán thư",
)
ALGAL = WeatherProfile(
    "algal", "wet", min_humid_hours=6, min_rain_mm=3, temp_low=22, temp_high=33,
    note="ẩm ướt kéo dài thuận lợi cho tảo gây đốm rong",
)
RUST = WeatherProfile(
    "rust", "wet", min_humid_hours=6, min_rain_mm=3, temp_low=17, temp_high=27,
    note="trời mát, ẩm thuận lợi cho nấm gỉ sắt",
)
POWDERY = WeatherProfile(
    "powdery", "dry_day_humid_night", temp_low=18, temp_high=30,
    note="ngày khô, đêm ẩm thuận lợi cho phấn trắng (mưa lớn lại rửa trôi bào tử)",
)
LEAF_SPOT = WeatherProfile(
    "leaf_spot", "wet", min_humid_hours=6, min_rain_mm=5, temp_low=20, temp_high=32,
    note="ẩm độ cao, lá ướt lâu thuận lợi cho nấm gây đốm/cháy lá",
)
CANKER = WeatherProfile(
    "canker", "wet", min_humid_hours=8, min_rain_mm=10, temp_low=24, temp_high=34,
    note="mưa lớn kèm gió làm vi khuẩn loét bắn sang lá non",
)
DRY_HOT = WeatherProfile(
    "dry_hot", "dry_hot",
    note="khô nóng, ra lộc non thuận lợi cho rầy, sâu vẽ bùa, nhện, bọ xít và nấm bồ hóng đi kèm",
)
DEFAULT = WeatherProfile("default", "wet", note="ẩm độ cao, mưa nhiều thuận lợi cho bệnh lây lan")

# Order matters: the first matching keyword group wins.
_KEYWORDS: tuple[tuple[tuple[str, ...], WeatherProfile], ...] = (
    (("phytophthora",), PHYTOPHTHORA),
    (("loét", "canker"), CANKER),
    (("rầy", "nhện", "bọ xít", "bọ trĩ", "psyllid", "leafhopper", "mite", "bug", "thrips", "bồ hóng", "sooty",
      "sâu vẽ bùa", "leafminer", "sâu xanh", "caterpillar", "vàng lá gân xanh", "greening", "xoăn lá", "leaf curl"), DRY_HOT),
    (("phấn trắng", "powdery"), POWDERY),
    (("gỉ sắt", "rust"), RUST),
    (("rong", "algal"), ALGAL),
    (("thán thư", "anthracnose", "colletotrichum"), ANTHRACNOSE),
    (("phomopsis", "pestalotiopsis", "rhizoctonia", "blight", "cháy", "thối", "đốm"), LEAF_SPOT),
)


def profile_for(disease: str) -> WeatherProfile:
    name = disease.lower()
    for keywords, profile in _KEYWORDS:
        if any(k in name for k in keywords):
            return profile
    return DEFAULT


def favourable_share(days: list[DayLike], profile: WeatherProfile) -> float:
    """Share of forecast days that favour the disease (0..1)."""
    if not days:
        return 0.0
    return sum(1 for d in days if profile.favourable(d)) / len(days)
