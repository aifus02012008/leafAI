# -*- coding: utf-8 -*-
"""
LEAF_AI - Phác đồ điều trị bệnh lá vải sau chẩn đoán.

Từ kết quả chẩn đoán (lớp bệnh) và thông tin người dùng nhập (mức độ bệnh quan sát
được, giai đoạn sinh trưởng, diện tích, số ngày đến thu hoạch), sinh lịch xử lý theo
thứ tự ưu tiên IPM: canh tác -> sinh học -> hóa học, có kiểm tra lại và đánh giá.

Endpoint:
    GET  /treatment              danh sách bệnh có phác đồ, mức độ, giai đoạn
    GET  /treatment/{disease}    phác đồ gốc của một bệnh
    POST /treatment/plan         lịch điều trị cá nhân hóa
"""

import json
import math
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

KB_PATH = Path(__file__).parent / "treatment_protocols.json"
KB: Dict[str, Any] = json.loads(KB_PATH.read_text(encoding="utf-8"))

# Lịch mẫu theo mức độ: (ngày thứ, loại bước)
SCHEDULES: Dict[str, List[tuple]] = {
    "nhe": [(0, "cultural"), (1, "biological"), (3, "monitor"), (7, "biological"),
            (10, "evaluate"), (10, "chemical_conditional")],
    "trung_binh": [(0, "cultural"), (1, "biological"), (3, "monitor"), (5, "chemical"),
                   (12, "monitor"), (14, "chemical_conditional"), (21, "evaluate")],
    "nang": [(0, "cultural"), (1, "chemical"), (4, "monitor"), (8, "chemical"),
             (11, "biological"), (15, "monitor"), (21, "evaluate")],
}

SEVERITY_ALIASES = {
    "nhe": "nhe", "nhẹ": "nhe", "low": "nhe", "mild": "nhe",
    "trung_binh": "trung_binh", "trung bình": "trung_binh", "medium": "trung_binh", "moderate": "trung_binh",
    "nang": "nang", "nặng": "nang", "nghiêm trọng": "nang", "high": "nang", "severe": "nang",
}

DISEASE_ALIASES = {
    "than_thu": "anthracnose", "colletotrichum": "anthracnose",
    "suong_mai": "downy_blight", "downy": "downy_blight", "peronophythora": "downy_blight",
    "chay_la": "leaf_blight", "pestalotiopsis": "leaf_blight",
    "dom_rong": "algal_spot", "algal": "algal_spot", "cephaleuros": "algal_spot",
    "nhen_long_nhung": "erinose", "erinose_mite": "erinose", "leaf_mite": "erinose",
    "leaf_mites": "erinose", "mite": "erinose", "aceria": "erinose",
}

HEALTHY_KEYS = {"healthy", "la_khoe", "normal", "healthy_leaf"}

GENERAL_RULES = [
    "Đúng thuốc: chỉ dùng thuốc có trong danh mục được phép, đúng đối tượng gây hại.",
    "Đúng liều: pha theo liều ghi trên nhãn, không tự tăng nồng độ.",
    "Đúng lúc: phun sáng sớm hoặc chiều mát, khi trời không mưa; không phun khi hoa nở rộ.",
    "Đúng cách: phun ướt đều hai mặt lá, chú ý lộc non; mang đồ bảo hộ khi pha và phun.",
    "Luân phiên nhóm hoạt chất (mã FRAC/IRAC khác nhau) giữa các lần phun để hạn chế kháng thuốc.",
    "Ghi nhật ký mỗi lần phun (ngày, hoạt chất, liều) để tính thời gian cách ly trước thu hoạch.",
]


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", str(text or "")).strip().lower()


def resolve_disease(name: str) -> Optional[str]:
    """Đổi tên lớp mô hình / tên gọi khác sang khóa phác đồ."""
    key = _norm(name).replace(" ", "_").replace("-", "_")
    diseases = KB["diseases"]
    if key in diseases:
        return key
    for k, d in diseases.items():
        if key == d["class"].lower():
            return k
    return DISEASE_ALIASES.get(key)


def resolve_severity(value: Optional[str]) -> str:
    return SEVERITY_ALIASES.get(_norm(value or "trung_binh"), "trung_binh")


def _pick_chemicals(options: List[Dict[str, str]], count: int) -> List[Dict[str, str]]:
    """Chọn hoạt chất cho từng lần phun, ưu tiên đổi nhóm FRAC/IRAC giữa hai lần liên tiếp."""
    picks: List[Dict[str, str]] = []
    for i in range(count):
        if not options:
            break
        if not picks:
            picks.append(options[0])
            continue
        prev_group = picks[-1]["group"]
        nxt = next((o for o in options if o["group"] != prev_group and o not in picks), None)
        picks.append(nxt or options[(i) % len(options)])
    return picks


def build_plan(disease: str, severity: Optional[str] = "trung_binh", growth_stage: Optional[str] = "loc_non",
               area_m2: float = 1000.0, start: Optional[date] = None,
               days_to_harvest: Optional[int] = None) -> Dict[str, Any]:
    """Sinh lịch điều trị. Ném ValueError nếu bệnh không có phác đồ."""
    key = resolve_disease(disease)
    if key is None:
        if _norm(disease) in HEALTHY_KEYS:
            raise ValueError("Lá khỏe mạnh, không cần phác đồ điều trị. Tiếp tục thăm vườn 1–2 lần mỗi tuần.")
        raise ValueError(f"Chưa có phác đồ cho lớp '{disease}'.")

    d = KB["diseases"][key]
    sev = resolve_severity(severity)
    stage = growth_stage if growth_stage in KB["growth_stages"] else "loc_non"
    start = start or date.today()
    area = max(1.0, float(area_m2 or 1000))
    guard = int(KB["phi_guard_days"])

    schedule = SCHEDULES[sev]
    n_chem = sum(1 for _, t in schedule if t.startswith("chemical"))
    chems = _pick_chemicals(d["chemical"], n_chem)
    bio_seen = 0
    chem_seen = 0
    steps: List[Dict[str, Any]] = []

    for day, kind in schedule:
        step: Dict[str, Any] = {
            "day": day,
            "date": (start + timedelta(days=day)).isoformat(),
            "type": kind,
            "conditional": False,
            "blocked": False,
            "actions": [],
            "products": [],
            "warnings": [],
        }
        if kind == "cultural":
            step.update(title="Cắt bỏ, tiêu hủy phần bị bệnh", actions=list(d["cultural"]))
        elif kind == "biological":
            bio_seen += 1
            if d["biological"]:
                step.update(title="Biện pháp sinh học" + (" (lần 2)" if bio_seen > 1 else ""),
                            actions=list(d["biological"]))
            else:
                step.update(type="cultural", title="Bổ sung biện pháp canh tác",
                            actions=["Chưa có chế phẩm sinh học đặc hiệu cho bệnh này.", d["cultural"][1]])
        elif kind == "monitor":
            step.update(title="Kiểm tra lại vườn", actions=[
                d["monitor"],
                "Chụp lại lá nghi bệnh bằng LEAF_AI để so sánh với lần chẩn đoán đầu.",
            ])
        elif kind == "evaluate":
            step.update(title="Đánh giá hiệu quả", actions=[
                "Tiêu chí đạt: " + d["success"],
                "Nếu đạt: chuyển sang phòng ngừa, thăm vườn 1–2 lần mỗi tuần.",
                "Nếu chưa đạt: mang mẫu lá đến trạm bảo vệ thực vật để xác định lại tác nhân.",
            ])
        else:  # chemical, chemical_conditional
            prod = chems[chem_seen] if chem_seen < len(chems) else None
            chem_seen += 1
            conditional = kind == "chemical_conditional"
            step.update(
                type="chemical", conditional=conditional,
                title=("Hóa học, chỉ khi bệnh vẫn lan" if conditional else
                       "Phun thuốc hóa học" + (f" (lần {chem_seen})" if n_chem > 1 else "")),
                actions=[
                    "Pha đúng liều ghi trên nhãn; phun ướt đều hai mặt lá, tập trung lộc non và vùng bị bệnh.",
                    "Ghi nhật ký: ngày phun, tên thuốc, hoạt chất, liều lượng.",
                ],
                products=[prod] if prod else [],
            )
            if stage == "ra_hoa":
                step["warnings"].append("Cây đang ra hoa: không phun khi hoa nở rộ để bảo vệ ong thụ phấn; "
                                        "phun trước khi hoa nở hoặc sau khi hoa tàn.")
            if days_to_harvest is not None and day > days_to_harvest - guard:
                step["blocked"] = True
                step["products"] = []
                step["warnings"].append(f"Còn dưới {guard} ngày đến thu hoạch: không dùng thuốc hóa học, "
                                        "chỉ áp dụng canh tác và sinh học. Luôn kiểm tra thời gian cách ly trên nhãn.")
        steps.append(step)

    liquid = round(area * float(KB["spray_volume_l_per_m2"]), 1)
    tanks = math.ceil(liquid / float(KB["tank_volume_l"]))
    last_day = max(s["day"] for s in steps)

    notes = [d["note"]]
    if days_to_harvest is not None and any(s["blocked"] for s in steps):
        notes.append("Có bước hóa học bị loại do gần ngày thu hoạch.")

    return {
        "disease": {"id": key, "class": d["class"], "name_vi": d["name_vi"],
                    "pathogen": d["pathogen"], "kind": d["kind"]},
        "severity": {"key": sev, **KB["severity_levels"][sev]},
        "growth_stage": {"key": stage, "label": KB["growth_stages"][stage]},
        "area_m2": area,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=last_day)).isoformat(),
        "duration_days": last_day,
        "days_to_harvest": days_to_harvest,
        "spray": {
            "liquid_l": liquid,
            "tanks": tanks,
            "tank_l": KB["tank_volume_l"],
            "note": "Ước tính lượng dung dịch cho một lần phun, điều chỉnh theo độ lớn tán. Lượng thuốc pha theo nhãn.",
        },
        "steps": steps,
        "monitor": d["monitor"],
        "success": d["success"],
        "notes": notes,
        "rules": GENERAL_RULES,
        "source": KB["source"],
        "generated_by": "server",
        "version": KB["version"],
    }


# ----------------------------------------------------------------------------
# API
# ----------------------------------------------------------------------------
router = APIRouter(tags=["treatment"])


class PlanRequest(BaseModel):
    disease: str = Field(..., description="Lớp bệnh trả về từ /predict_with_gradcam hoặc khóa phác đồ")
    severity: Optional[str] = Field("trung_binh", description="nhe | trung_binh | nang")
    growth_stage: Optional[str] = Field("loc_non", description="sau_thu_hoach | loc_non | ra_hoa | nuoi_qua")
    area_m2: float = Field(1000.0, gt=0, le=1_000_000)
    start_date: Optional[date] = None
    days_to_harvest: Optional[int] = Field(None, ge=0, le=365)


@router.get("/treatment")
def list_treatments():
    return {
        "diseases": [{"id": k, "class": v["class"], "name_vi": v["name_vi"], "kind": v["kind"]}
                     for k, v in KB["diseases"].items()],
        "severity_levels": KB["severity_levels"],
        "growth_stages": KB["growth_stages"],
        "version": KB["version"],
    }


@router.get("/treatment/{disease}")
def get_treatment(disease: str):
    key = resolve_disease(disease)
    if key is None:
        raise HTTPException(status_code=404, detail=f"Chưa có phác đồ cho '{disease}'.")
    return {"id": key, **KB["diseases"][key], "source": KB["source"]}


@router.post("/treatment/plan")
def create_plan(req: PlanRequest):
    try:
        return build_plan(req.disease, req.severity, req.growth_stage, req.area_m2,
                          req.start_date, req.days_to_harvest)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
