"""Danh mục HOẠT CHẤT thuốc BVTV (không phải tên thương mại) kèm nhóm cơ chế tác động.

- `moa_code`: mã nhóm FRAC (thuốc trừ nấm) hoặc IRAC (thuốc trừ sâu) — dùng để gợi ý
  luân phiên hoạt chất khác nhóm khi nghi kháng thuốc.
- `banned`: hoạt chất đã bị loại khỏi Danh mục thuốc BVTV được phép sử dụng tại Việt Nam.
- KHÔNG lưu liều/thời gian cách ly ở đây: các thông số đó khác nhau theo từng sản phẩm,
  người dùng nhập từ nhãn thuốc thực tế.
⚠️ Cần đối chiếu định kỳ với Danh mục thuốc BVTV do Bộ NN&PTNT ban hành hằng năm.
"""
from __future__ import annotations

from types import MappingProxyType

from app.db.seed import durian, mangosteen, rambutan


def _a(code, name, kind, scheme, moa, banned=False, note=None) -> dict:
    return {
        "code": code, "name": name, "kind": kind, "moa_scheme": scheme,
        "moa_code": moa, "banned": banned, "note": note,
    }


ACTIVE_INGREDIENTS: tuple[dict, ...] = (
    # ----- Thuốc trừ nấm -----
    _a("azoxystrobin", "Azoxystrobin", "fungicide", "FRAC", "11"),
    _a("difenoconazole", "Difenoconazole", "fungicide", "FRAC", "3"),
    _a("hexaconazole", "Hexaconazole", "fungicide", "FRAC", "3"),
    _a("propiconazole", "Propiconazole", "fungicide", "FRAC", "3"),
    _a("tebuconazole", "Tebuconazole", "fungicide", "FRAC", "3"),
    _a("mancozeb", "Mancozeb", "fungicide", "FRAC", "M03"),
    _a("propineb", "Propineb", "fungicide", "FRAC", "M03"),
    _a("copper_hydroxide", "Copper hydroxide (gốc đồng)", "fungicide", "FRAC", "M01"),
    _a("copper_oxychloride", "Copper oxychloride (gốc đồng)", "fungicide", "FRAC", "M01"),
    _a("sulfur", "Lưu huỳnh (Sulfur)", "fungicide", "FRAC", "M02"),
    _a("metalaxyl_m", "Metalaxyl-M", "fungicide", "FRAC", "4"),
    _a("fosetyl_al", "Fosetyl-aluminium", "fungicide", "FRAC", "P07"),
    _a("potassium_phosphonate", "Potassium phosphonate", "fungicide", "FRAC", "P07"),
    _a("dimethomorph", "Dimethomorph", "fungicide", "FRAC", "40"),
    _a("validamycin", "Validamycin", "fungicide", "FRAC", "26"),
    _a("carbendazim", "Carbendazim", "fungicide", "FRAC", "1", banned=True,
       note="Đã bị loại khỏi danh mục được phép sử dụng tại Việt Nam."),
    _a("thiophanate_methyl", "Thiophanate-methyl", "fungicide", "FRAC", "1", banned=True,
       note="Đã bị loại khỏi danh mục được phép sử dụng tại Việt Nam."),
    _a("benomyl", "Benomyl", "fungicide", "FRAC", "1", banned=True,
       note="Đã bị loại khỏi danh mục được phép sử dụng tại Việt Nam."),
    # ----- Thuốc trừ sâu / nhện -----
    _a("imidacloprid", "Imidacloprid", "insecticide", "IRAC", "4A"),
    _a("thiamethoxam", "Thiamethoxam", "insecticide", "IRAC", "4A"),
    _a("dinotefuran", "Dinotefuran", "insecticide", "IRAC", "4A"),
    _a("abamectin", "Abamectin", "insecticide", "IRAC", "6"),
    _a("emamectin_benzoate", "Emamectin benzoate", "insecticide", "IRAC", "6"),
    _a("buprofezin", "Buprofezin", "insecticide", "IRAC", "16"),
    _a("flonicamid", "Flonicamid", "insecticide", "IRAC", "29"),
    _a("pymetrozine", "Pymetrozine", "insecticide", "IRAC", "9B"),
    _a("spirotetramat", "Spirotetramat", "insecticide", "IRAC", "23"),
    _a("mineral_oil", "Dầu khoáng (Mineral oil)", "insecticide", "IRAC", None,
       note="Tác động vật lý (làm ngạt), ít nguy cơ kháng."),
    _a("hexythiazox", "Hexythiazox", "acaricide", "IRAC", "10A"),
    _a("propargite", "Propargite", "acaricide", "IRAC", "12C"),
    _a("chlorpyrifos_ethyl", "Chlorpyrifos ethyl", "insecticide", "IRAC", "1B", banned=True,
       note="Đã bị loại khỏi danh mục được phép sử dụng tại Việt Nam."),
)

ACTIVES_BY_CODE = MappingProxyType({a["code"]: a for a in ACTIVE_INGREDIENTS})

_FUNGAL_LEAF = ("azoxystrobin", "difenoconazole", "propineb", "mancozeb", "copper_hydroxide")
_ALGAL = ("copper_hydroxide", "copper_oxychloride")
_SOOTY = ("mineral_oil", "buprofezin", "spirotetramat", "copper_hydroxide")

# (crop_code, disease class_name) -> recommended active codes, in preference order.
DISEASE_ACTIVES = MappingProxyType({
    ("tea", "Bệnh rầy xanh (Tea green leafhopper)"): ("flonicamid", "buprofezin", "pymetrozine", "emamectin_benzoate", "dinotefuran"),
    ("tea", "Thối đen lá chè (Black rot of tea)"): _FUNGAL_LEAF + ("hexaconazole",),
    ("tea", "Cháy nâu lá chè (Brown blight of tea)"): _FUNGAL_LEAF + ("hexaconazole",),
    ("tea", "Gỉ sắt lá chè (Leaf rust of tea)"): ("hexaconazole", "azoxystrobin", "copper_hydroxide", "sulfur"),
    ("tea", "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)"): ("abamectin", "hexythiazox", "propargite", "mineral_oil"),
    ("tea", "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)"): ("thiamethoxam", "emamectin_benzoate", "dinotefuran", "abamectin"),
    ("durian", durian.PHYTOPHTHORA): ("fosetyl_al", "metalaxyl_m", "dimethomorph", "potassium_phosphonate"),
    ("durian", durian.RHIZOCTONIA): ("validamycin", "hexaconazole", "azoxystrobin"),
    ("durian", durian.ANTHRACNOSE): _FUNGAL_LEAF,
    ("durian", durian.ALGAL): _ALGAL,
    ("durian", durian.PHOMOPSIS): ("azoxystrobin", "difenoconazole", "propiconazole", "mancozeb", "propineb", "copper_hydroxide"),
    ("durian", durian.PSYLLID): ("thiamethoxam", "imidacloprid", "dinotefuran", "abamectin", "mineral_oil"),
    ("mangosteen", mangosteen.ANTHRACNOSE): _FUNGAL_LEAF,
    ("mangosteen", mangosteen.PESTALOTIOPSIS): ("mancozeb", "propineb", "azoxystrobin", "difenoconazole", "copper_hydroxide"),
    ("mangosteen", mangosteen.ALGAL): _ALGAL,
    ("mangosteen", mangosteen.SOOTY_MOLD): _SOOTY,
    ("rambutan", rambutan.POWDERY_MILDEW): ("sulfur", "hexaconazole", "difenoconazole", "azoxystrobin"),
    ("rambutan", rambutan.ANTHRACNOSE): _FUNGAL_LEAF,
    ("rambutan", rambutan.ALGAL): _ALGAL,
    ("rambutan", rambutan.SOOTY_MOLD): _SOOTY,
})


def actives_for_disease(crop_code: str, class_name: str) -> list[dict]:
    """Recommended, non-banned actives for a disease (empty if unknown)."""
    codes = DISEASE_ACTIVES.get((crop_code, class_name), ())
    return [ACTIVES_BY_CODE[c] for c in codes if not ACTIVES_BY_CODE[c]["banned"]]
