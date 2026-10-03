# -*- coding: utf-8 -*-
"""
LEAF_AI - Comprehensive All-API End-to-End Test Suite
Tests all 17 API endpoints, models, integrations, and services.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import time
import json
import base64
import urllib.request
import urllib.error
from PIL import Image
import io

print("=" * 85)
print("     LEAF_AI — TOÀN BỘ KIỂM THỬ TẤT CẢ API & DỊCH VỤ HỆ THỐNG")
print("=" * 85)

results = []

def test_api(name, method, url, data=None, headers=None, expected_status=200):
    t0 = time.time()
    passed = False
    details = ""
    status_code = None

    default_headers = {'User-Agent': 'LEAF_AI-TestAgent/1.0'}
    if headers:
        default_headers.update(headers)

    req_data = None
    if data:
        if isinstance(data, dict):
            req_data = json.dumps(data).encode('utf-8')
            default_headers['Content-Type'] = 'application/json'
        elif isinstance(data, bytes):
            req_data = data

    try:
        req = urllib.request.Request(url, data=req_data, headers=default_headers, method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            status_code = resp.status
            body = resp.read().decode('utf-8', errors='ignore')
            elapsed_ms = (time.time() - t0) * 1000
            
            try:
                parsed = json.loads(body)
                if status_code == expected_status:
                    passed = True
                    if isinstance(parsed, dict):
                        keys = list(parsed.keys())[:4]
                        details = f"HTTP {status_code} | Keys: {keys}"
                    elif isinstance(parsed, list):
                        details = f"HTTP {status_code} | Items: {len(parsed)}"
                    else:
                        details = f"HTTP {status_code} | JSON OK"
                else:
                    details = f"HTTP {status_code} (Expected {expected_status})"
            except Exception:
                if status_code == expected_status:
                    passed = True
                    details = f"HTTP {status_code} | Text Len: {len(body)}"
                else:
                    details = f"HTTP {status_code} (Expected {expected_status})"

    except urllib.error.HTTPError as e:
        status_code = e.code
        elapsed_ms = (time.time() - t0) * 1000
        details = f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        elapsed_ms = (time.time() - t0) * 1000
        details = f"Error: {str(e)[:60]}"

    tag = "[PASS]" if passed else "[FAIL]"
    status_text = "PASS" if passed else "FAIL"
    print(f"  {tag} {name:<46} | {status_text:<4} | {elapsed_ms:>7.1f}ms | {details}")
    results.append({"name": name, "passed": passed, "latency_ms": elapsed_ms, "details": details})
    return passed


# 1. Dummy test image base64
dummy_img = Image.new("RGB", (224, 224), color=(34, 139, 34))
buf = io.BytesIO()
dummy_img.save(buf, format="JPEG")
test_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')

# SECTION 1: AI MICROSERVICE (Port 8001)
print("\n--- [PHẦN 1] MICROSERVICE AI SUY LUẬN PYTORCH (Port 8001) ---")
test_api("1. AI Engine Health (GET /health)", "GET", "http://127.0.0.1:8001/health")
test_api("2. AI Engine Root Dashboard (GET /)", "GET", "http://127.0.0.1:8001/")
test_api("3. AI Predict with GradCAM (POST /predict_with_gradcam)", "POST", "http://127.0.0.1:8001/predict_with_gradcam", data={"data": test_b64, "model_version": "v4"})
test_api("4. AI Predict Simple (POST /predict)", "POST", "http://127.0.0.1:8001/predict", data={"data": test_b64, "model_version": "v3"})

# SECTION 2: DJANGO REST BACKEND (Port 8000)
print("\n--- [PHẦN 2] DJANGO BACKEND REST API (Port 8000) ---")
test_api("5. Django Health Check (GET /health/)", "GET", "http://127.0.0.1:8000/health/")
test_api("6. Tomato Diseases Library (GET /api/diseases/)", "GET", "http://127.0.0.1:8000/api/diseases/")
test_api("7. Filter Diseases by Fungus (GET /api/diseases/?category=fungus)", "GET", "http://127.0.0.1:8000/api/diseases/?category=fungus")
test_api("8. Search Diseases by Query (GET /api/diseases/?q=Early)", "GET", "http://127.0.0.1:8000/api/diseases/?q=Early")
test_api("9. FAO IPM Handbook All (GET /api/handbook/)", "GET", "http://127.0.0.1:8000/api/handbook/")
test_api("10. FAO IPM 8 Principles (GET /api/handbook/?section=principles)", "GET", "http://127.0.0.1:8000/api/handbook/?section=principles")
test_api("11. AI Models Metadata (GET /api/models/)", "GET", "http://127.0.0.1:8000/api/models/")
test_api("12. Platform Statistics (GET /api/stats/)", "GET", "http://127.0.0.1:8000/api/stats/")
test_api("13. Supabase Cloud Status (GET /api/supabase/status/)", "GET", "http://127.0.0.1:8000/api/supabase/status/")
test_api("14. Diagnosis History List (GET /api/history/)", "GET", "http://127.0.0.1:8000/api/history/")
test_api("15. Gemini 2.5 Flash Chatbot (POST /api/chat/)", "POST", "http://127.0.0.1:8000/api/chat/", data={"message": "Lá cà chua bị đốm nâu đồng tâm là bệnh gì?", "context": {}})
test_api("16. AI Leaf Diagnosis End-to-End (POST /api/diagnose/)", "POST", "http://127.0.0.1:8000/api/diagnose/", data={"image": test_b64, "model_version": "v4"})

# SECTION 3: HUGGING FACE CLOUD (Spaces & Model Hub)
print("\n--- [PHẦN 3] HUGGING FACE CLOUD REPOSITORIES ---")
test_api("17. HF Space Live Web App (GET https://huggingface.co/spaces/Hphuccoder28/leaf-ai-app)", "GET", "https://huggingface.co/spaces/Hphuccoder28/leaf-ai-app")
test_api("18. HF Model Repository (GET https://huggingface.co/Hphuccoder28/leaf-ai-tomato-model)", "GET", "https://huggingface.co/Hphuccoder28/leaf-ai-tomato-model")

passed_count = sum(1 for r in results if r["passed"])
total_count = len(results)
print("\n" + "=" * 85)
print(f"   TỔNG KẾT KIỂM THỬ: {passed_count}/{total_count} APIS & DỊCH VỤ HOẠT ĐỘNG HOÀN HẢO ({(passed_count/total_count)*100:.1f}%)")
print("=" * 85)
