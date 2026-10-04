# -*- coding: utf-8 -*-
"""
LEAF_AI - Supabase Cloud Integration Service
Kết nối cơ sở dữ liệu Supabase (PostgreSQL), đồng bộ hóa lịch sử chẩn đoán,
thư viện 6 bệnh cà chua và cẩm nang IPM chuẩn FAO lên Supabase Cloud.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Đọc cấu hình Supabase từ môi trường hoặc backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or
    os.environ.get("SUPABASE_KEY", "") or
    os.environ.get("SUPABASE_ANON_KEY", "")
).strip()

_supabase_client = None


def is_supabase_configured() -> bool:
    """Kiểm tra xem URL và Key của Supabase đã được cấu hình hay chưa."""
    global SUPABASE_URL, SUPABASE_KEY
    # Tải lại nếu vừa cập nhật .env
    if not SUPABASE_URL or not SUPABASE_KEY:
        load_dotenv()
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
        SUPABASE_KEY = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or
            os.environ.get("SUPABASE_KEY", "") or
            os.environ.get("SUPABASE_ANON_KEY", "")
        ).strip()
    return bool(SUPABASE_URL and SUPABASE_KEY and not SUPABASE_URL.startswith("https://your-project"))


def get_supabase_client():
    """Lấy hoặc khởi tạo Supabase Client instance (singleton)."""
    global _supabase_client
    if not is_supabase_configured():
        return None

    if _supabase_client is None:
        try:
            from supabase import create_client, Client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info(f"Supabase client initialized successfully with endpoint: {SUPABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    return _supabase_client


def save_diagnosis_to_supabase(record_data: Dict[str, Any]) -> Optional[str]:
    """
    Lưu kết quả chẩn đoán lá vải thiều lên bảng 'leaf_diagnoses' của Supabase.
    Nếu Supabase chưa cấu hình hoặc mất mạng, trả về None mà không làm gián đoạn hệ thống.
    """
    client = get_supabase_client()
    if not client:
        logger.info("Supabase not configured or unreachable. Diagnosis saved locally only.")
        return None

    try:
        payload = {
            "local_id": record_data.get("id"),
            "model_version": record_data.get("model_version", "v3"),
            "plant_type": record_data.get("plant_type", "lychee"),
            "primary_disease": record_data.get("primary_disease", ""),
            "primary_disease_vi": record_data.get("primary_disease_vi", ""),
            "confidence": float(record_data.get("confidence", 0.0)),
            "severity": record_data.get("severity", "Nghiêm trọng"),
            "is_coinfection": bool(record_data.get("is_coinfection", False)),
            "secondary_diseases": record_data.get("secondary_diseases", []),
            "detections": record_data.get("detections", []),
            "treatment_summary": record_data.get("treatment_summary", ""),
        }

        response = client.table("leaf_diagnoses").insert(payload).execute()
        if response.data and len(response.data) > 0:
            supabase_id = str(response.data[0].get("id", ""))
            logger.info(f"Successfully synced diagnosis record to Supabase, id={supabase_id}")
            return supabase_id
    except Exception as e:
        logger.warning(f"Error syncing diagnosis to Supabase: {e}")
    return None


def fetch_history_from_supabase(limit: int = 50) -> Optional[List[Dict[str, Any]]]:
    """Lấy danh sách lịch sử chẩn đoán từ Supabase Cloud."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = (
            client.table("leaf_diagnoses")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.warning(f"Error fetching diagnosis history from Supabase: {e}")
        return None


def delete_diagnosis_from_supabase(local_id: int) -> bool:
    """Xóa bản ghi chẩn đoán khỏi Supabase Cloud theo local_id."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("leaf_diagnoses").delete().eq("local_id", local_id).execute()
        return True
    except Exception as e:
        logger.warning(f"Error deleting record {local_id} from Supabase: {e}")
        return False


def clear_history_from_supabase() -> bool:
    """Xóa toàn bộ lịch sử trên Supabase Cloud."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("leaf_diagnoses").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return True
    except Exception as e:
        logger.warning(f"Error clearing history on Supabase: {e}")
        return False


def seed_supabase_knowledge_base():
    """Đẩy toàn bộ 6 bệnh cà chua và Cẩm nang IPM lên Supabase nếu các bảng còn trống."""
    from .leaf_knowledge import TOMATO_DISEASES, FAO_IPM_HANDBOOK

    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase not configured"}

    results = {"diseases_seeded": 0, "handbook_seeded": 0}

    # 1. Seed Tomato Diseases
    try:
        existing = client.table("tomato_diseases").select("disease_id").execute()
        existing_ids = {row["disease_id"] for row in (existing.data or [])}

        to_insert = []
        for key, d in TOMATO_DISEASES.items():
            if key not in existing_ids:
                to_insert.append({
                    "disease_id": key,
                    "name_en": d.get("name_en", key),
                    "name_vi": d.get("name_vi", key),
                    "pathogen": d.get("pathogen", ""),
                    "color": d.get("color", "#ea580c"),
                    "severity_default": d.get("severity", "Nghiêm trọng"),
                    "confidence_default": float(d.get("confidence", 50.0)),
                    "symptoms_stage1": d.get("symptoms", {}).get("stage_1", ""),
                    "symptoms_stage2": d.get("symptoms", {}).get("stage_2", ""),
                    "symptoms_stage3": d.get("symptoms", {}).get("stage_3", ""),
                    "conditions": d.get("conditions", ""),
                    "prevention": d.get("prevention", ""),
                    "treatment_cultural": d.get("treatment", {}).get("cultural", ""),
                    "treatment_bio": d.get("treatment", {}).get("biological", ""),
                    "treatment_chemical": d.get("treatment", {}).get("chemical", ""),
                    "references": d.get("references", "")
                })

        if to_insert:
            client.table("tomato_diseases").insert(to_insert).execute()
            results["diseases_seeded"] = len(to_insert)
    except Exception as e:
        logger.warning(f"Failed to seed diseases to Supabase: {e}")

    # 2. Seed IPM Handbook
    try:
        existing_h = client.table("ipm_handbook").select("id").limit(1).execute()
        if not existing_h.data:
            handbook_rows = []
            for item in FAO_IPM_HANDBOOK.get("principles", []):
                handbook_rows.append({"section": "principles", "step_num": item["num"], "title": item["title"], "description": item["desc"]})
            for item in FAO_IPM_HANDBOOK.get("inspection", []):
                handbook_rows.append({"section": "inspection", "step_num": item["step"], "title": item["title"], "description": item["desc"]})
            for item in FAO_IPM_HANDBOOK.get("ipm", []):
                handbook_rows.append({"section": "ipm", "step_num": item["step"], "title": item["title"], "description": item["desc"]})
            for i, item in enumerate(FAO_IPM_HANDBOOK.get("safe_pesticide", [])):
                handbook_rows.append({"section": "safe", "step_num": i + 1, "title": item["rule"], "description": item["desc"]})

            if handbook_rows:
                client.table("ipm_handbook").insert(handbook_rows).execute()
                results["handbook_seeded"] = len(handbook_rows)
    except Exception as e:
        logger.warning(f"Failed to seed handbook to Supabase: {e}")

    results["success"] = True
    return results


def get_supabase_status() -> Dict[str, Any]:
    """Kiểm tra và trả về trạng thái chi tiết của Supabase kết nối."""
    configured = is_supabase_configured()
    client = get_supabase_client() if configured else None
    connected = False
    details = {}

    if client:
        try:
            # Thử ping nhẹ bằng select count
            res = client.table("leaf_diagnoses").select("id", count="exact").limit(1).execute()
            connected = True
            details["diagnoses_count"] = res.count if hasattr(res, "count") else len(res.data or [])
        except Exception as e:
            connected = False
            details["error"] = str(e)

    return {
        "configured": configured,
        "connected": connected,
        "supabase_url": SUPABASE_URL if configured else "Chua cau hinh (Not configured)",
        "details": details
    }
