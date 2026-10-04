# -*- coding: utf-8 -*-
"""Kiểm thử phác đồ điều trị (không cần PyTorch): pytest test_treatment.py"""
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from treatment import KB, build_plan, resolve_disease, router

_app = FastAPI()
_app.include_router(router)
client = TestClient(_app)


def test_resolve_model_labels_and_aliases():
    assert resolve_disease("Anthracnose") == "anthracnose"
    assert resolve_disease("Downy_blight") == "downy_blight"
    assert resolve_disease("leaf_mites") == "erinose"
    assert resolve_disease("Healthy") is None


def test_every_disease_builds_for_every_severity():
    for key in KB["diseases"]:
        for sev in ("nhe", "trung_binh", "nang"):
            plan = build_plan(key, sev, "loc_non", 1500, date(2026, 10, 5))
            assert plan["steps"][0]["type"] == "cultural"
            assert plan["steps"][0]["day"] == 0
            days = [s["day"] for s in plan["steps"]]
            assert days == sorted(days)


def test_ipm_order_light_case_has_only_conditional_chemical():
    plan = build_plan("Anthracnose", "nhe", start=date(2026, 10, 5))
    chem = [s for s in plan["steps"] if s["type"] == "chemical"]
    assert len(chem) == 1 and chem[0]["conditional"]
    first_bio = next(s for s in plan["steps"] if s["type"] == "biological")
    assert first_bio["day"] < chem[0]["day"]


def test_rotation_changes_active_group():
    plan = build_plan("Anthracnose", "nang", start=date(2026, 10, 5))
    groups = [s["products"][0]["group"] for s in plan["steps"] if s["type"] == "chemical"]
    assert len(groups) == 2 and groups[0] != groups[1]


def test_harvest_guard_blocks_chemicals():
    plan = build_plan("Downy_blight", "nang", "nuoi_qua", 1000, date(2026, 10, 5), days_to_harvest=10)
    chem = [s for s in plan["steps"] if s["type"] == "chemical"]
    assert chem and all(s["blocked"] and not s["products"] for s in chem)


def test_flowering_warning():
    plan = build_plan("Anthracnose", "trung_binh", "ra_hoa")
    chem = [s for s in plan["steps"] if s["type"] == "chemical"]
    assert all(any("hoa nở rộ" in w for w in s["warnings"]) for s in chem)


def test_spray_estimate():
    plan = build_plan("Erinose", "nhe", area_m2=1500)
    assert plan["spray"]["liquid_l"] == 120.0
    assert plan["spray"]["tanks"] == 8


def test_api_endpoints():
    r = client.get("/treatment")
    assert r.status_code == 200 and len(r.json()["diseases"]) == 5
    assert client.get("/treatment/Erinose").json()["name_vi"] == "Nhện lông nhung"
    assert client.get("/treatment/unknown").status_code == 404
    r = client.post("/treatment/plan", json={"disease": "Anthracnose", "severity": "Nghiêm trọng",
                                             "area_m2": 1500, "start_date": "2026-10-05"})
    assert r.status_code == 200
    body = r.json()
    assert body["severity"]["key"] == "nang" and body["start_date"] == "2026-10-05"
    assert client.post("/treatment/plan", json={"disease": "Healthy"}).status_code == 422
    assert client.post("/treatment/plan", json={"disease": "Erinose", "area_m2": -5}).status_code == 422
