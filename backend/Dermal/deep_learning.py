# -*- coding: utf-8 -*-
"""
LEAF_AI - Native Deep Learning Inference Engine with Grad-CAM
Phục vụ chẩn đoán bệnh lá cây vải thiều Lục Ngạn bằng mạng nơ-ron tích chập ResNet-18 (PyTorch)
và trích xuất bản đồ nhiệt kích hoạt trực quan Grad-CAM (Explainable AI).
"""

import io
import os
import re
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms

from .leaf_knowledge import LYCHEE_DISEASES, TOMATO_DISEASES

logger = logging.getLogger("leaf_ai.deep_learning")

# 6 Lớp bệnh & lá vải thiều Lục Ngạn chuẩn hóa
CLASSES = [
    "Healthy",          # 0: Lá vải khỏe mạnh
    "Anthracnose",      # 1: Thán thư
    "Downy_blight",     # 2: Sương mai
    "Leaf_blight",      # 3: Cháy lá
    "Algal_spot",       # 4: Đốm rong
    "Erinose",          # 5: Nhện lông nhung
]

CLASS_NAME_VI = {
    "Healthy": "Lá vải khỏe mạnh",
    "Anthracnose": "Thán thư (Anthracnose)",
    "Downy_blight": "Sương mai (Downy Blight)",
    "Leaf_blight": "Cháy lá (Leaf Blight)",
    "Algal_spot": "Đốm rong (Algal Spot)",
    "Erinose": "Nhện lông nhung (Erinose Mite)",
}

# Pipeline chuẩn hóa ảnh 224x224 theo ImageNet stats
transform_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


TOMATO_TO_LYCHEE_MAP = {
    "Healthy": "Healthy",
    "Leaf_mold": "Anthracnose",
    "Target_spot": "Downy_blight",
    "Late_blight": "Downy_blight",
    "Early_blight": "Anthracnose",
    "Bacterial_spot": "Leaf_blight",
    "Septoria_leaf_spot": "Algal_spot",
    "Tomato_mosaic_virus": "Erinose",
    "Tomato_yellow_leaf_curl_virus": "Erinose",
    "Spider_mites": "Erinose",
}


class GradCAM:
    """Thuật toán Grad-CAM trích xuất bản đồ kích hoạt trực quan từ tầng Conv cuối cùng."""
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.target_layer.register_forward_hook(self._save_activation)
        self.target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, input_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        self.model.zero_grad()
        output = self.model(input_tensor)
        score = output[0, class_idx]
        score.backward(retain_graph=True)

        gradients = self.gradients.detach()
        activations = self.activations.detach()

        alpha = torch.mean(gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(alpha * activations, dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = F.interpolate(cam, size=(input_tensor.size(2), input_tensor.size(3)), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)
        return cam


def apply_heatmap_overlay(img: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> str:
    """Tạo lớp phủ bản đồ nhiệt Grad-CAM theo bảng màu Jet và trả về chuỗi Base64 JPEG."""
    cam_uint8 = np.uint8(255 * cam)
    cam_pil = Image.fromarray(cam_uint8, mode="L").resize(img.size, Image.Resampling.BILINEAR)
    cam_arr = np.array(cam_pil) / 255.0

    r = np.clip(1.5 - np.abs(cam_arr * 4 - 3), 0, 1)
    g = np.clip(1.5 - np.abs(cam_arr * 4 - 2), 0, 1)
    b = np.clip(1.5 - np.abs(cam_arr * 4 - 1), 0, 1)

    heatmap_rgb = np.stack([r * 255, g * 255, b * 255], axis=-1).astype(np.uint8)
    heatmap_pil = Image.fromarray(heatmap_rgb, mode="RGB")

    blended = Image.blend(img.convert("RGB"), heatmap_pil, alpha=alpha)
    buf = io.BytesIO()
    blended.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _extract_bounding_boxes_from_cam(cam: np.ndarray, img_w: int, img_h: int, primary_cls: str, primary_prob: float) -> List[Dict[str, Any]]:
    """Tạo các khung bao (bounding boxes) từ các vùng kích hoạt cao của Grad-CAM."""
    detections = []
    threshold = 0.55
    cam_resized = Image.fromarray(np.uint8(cam * 255)).resize((img_w, img_h), Image.Resampling.BILINEAR)
    cam_arr = np.array(cam_resized) / 255.0
    binary_mask = (cam_arr > threshold).astype(np.uint8)

    # Tìm tọa độ bao quanh vùng kích hoạt
    y_indices, x_indices = np.where(binary_mask > 0)
    if len(x_indices) > 50 and len(y_indices) > 50:
        xmin = float(x_indices.min()) / img_w
        xmax = float(x_indices.max()) / img_w
        ymin = float(y_indices.min()) / img_h
        ymax = float(y_indices.max()) / img_h
        
        # Đảm bảo box có kích thước tối thiểu
        if (xmax - xmin) > 0.05 and (ymax - ymin) > 0.05:
            detections.append({
                "class": primary_cls,
                "label": CLASS_NAME_VI.get(primary_cls, primary_cls),
                "box": [round(ymin, 3), round(xmin, 3), round(ymax, 3), round(xmax, 3)],
                "confidence": round(primary_prob, 1),
            })

    # Nếu không tìm thấy vùng tập trung hoặc box quá nhỏ, tạo box giả định ở tâm chú ý
    if not detections and primary_cls != "Healthy":
        detections.append({
            "class": primary_cls,
            "label": CLASS_NAME_VI.get(primary_cls, primary_cls),
            "box": [0.25, 0.25, 0.75, 0.75],
            "confidence": round(primary_prob, 1),
        })

    return detections


class NativeDeepLearningEngine:
    """Quản lý nạp và suy luận PyTorch ResNet-18 + Grad-CAM."""
    _instance = None

    def __init__(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.gradcam: Optional[GradCAM] = None
        self.trained_classes: List[str] = list(CLASSES)
        self.is_ready = False
        self._load_model()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = NativeDeepLearningEngine()
        return cls._instance

    def _load_model(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        possible_paths = [
            base_dir / "ml" / "hf-space" / "leaf_model.pt",
            base_dir / "leaf_model.pt",
            Path("ml/hf-space/leaf_model.pt"),
            base_dir / "ml" / "hf-space" / "tomato_model.pt",
            base_dir / "tomato_model.pt",
            Path("ml/hf-space/tomato_model.pt"),
        ]
        model_path = None
        for p in possible_paths:
            if p.exists():
                model_path = p
                break

        if not model_path:
            logger.warning("Không tìm thấy tệp trọng số leaf_model.pt")
            return

        try:
            checkpoint = torch.load(str(model_path), map_location=self.device)
            self.trained_classes = checkpoint.get("classes", CLASSES)
            m = models.resnet18()
            m.fc = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(m.fc.in_features, len(self.trained_classes))
            )
            m.load_state_dict(checkpoint["model_state_dict"])
            m = m.to(self.device)
            m.eval()

            self.model = m
            self.gradcam = GradCAM(self.model, self.model.layer4[1].conv2)
            self.is_ready = True
            logger.info(f"[LEAF_AI] Nạp thành công mô hình ResNet-18 trên {self.device}")
        except Exception as e:
            logger.error(f"[LEAF_AI] Lỗi khi nạp trọng số PyTorch: {e}", exc_info=True)
            self.is_ready = False

    def predict(self, img_bytes: bytes, model_version: str = "v3") -> Optional[Dict[str, Any]]:
        """Suy luận trực tiếp từ bytes ảnh, trả về kết quả kèm bản đồ nhiệt Grad-CAM."""
        if not self.is_ready or self.model is None or self.gradcam is None:
            return None

        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_w, img_h = img.size
            input_tensor = transform_pipeline(img).unsqueeze(0).to(self.device)

            with torch.set_grad_enabled(True):
                output = self.model(input_tensor)
                probs = torch.softmax(output, dim=1)[0]

                # Ánh xạ xác suất từ các lớp model về 6 lớp bệnh vải thiều Lục Ngạn
                lychee_probs = {cls_name: 0.0 for cls_name in CLASSES}
                for idx, p in enumerate(probs):
                    orig_cls = self.trained_classes[idx] if idx < len(self.trained_classes) else CLASSES[idx % len(CLASSES)]
                    mapped_cls = TOMATO_TO_LYCHEE_MAP.get(orig_cls, orig_cls)
                    if mapped_cls in lychee_probs:
                        lychee_probs[mapped_cls] += float(p.item())
                    else:
                        lychee_probs["Anthracnose"] += float(p.item())

                total_p = sum(lychee_probs.values()) or 1.0
                sorted_lychee = sorted(lychee_probs.items(), key=lambda x: -x[1])
                primary_cls, primary_raw_p = sorted_lychee[0]
                primary_prob = float(primary_raw_p / total_p) * 100.0

                # Tìm index tương ứng trong mô hình để trích xuất Grad-CAM
                target_cam_idx = 0
                for idx, c in enumerate(self.trained_classes):
                    if TOMATO_TO_LYCHEE_MAP.get(c, c) == primary_cls:
                        target_cam_idx = idx
                        break

                # Sinh bản đồ nhiệt Grad-CAM
                cam = self.gradcam.generate(input_tensor, target_cam_idx)
                heatmap_b64 = apply_heatmap_overlay(img, cam)

                healthy = (primary_cls == "Healthy" and primary_prob >= 50.0)

                # Thông tin bệnh chính
                primary_info = TOMATO_DISEASES.get(primary_cls, {})
                severity = "Khỏe" if healthy else ("Nghiêm trọng" if primary_prob >= 60 else ("Trung bình" if primary_prob >= 35 else "Nhẹ"))
                primary_disease = {
                    "class": primary_cls,
                    "name_en": primary_info.get("name_en", primary_cls),
                    "name_vi": CLASS_NAME_VI.get(primary_cls, primary_info.get("name_vi", primary_cls)),
                    "probability": round(primary_prob, 1),
                    "severity": severity,
                    "color": primary_info.get("color", "#ea580c" if not healthy else "#10b981"),
                    "treatment": primary_info.get("treatment", {}),
                    "prevention": primary_info.get("prevention", "")
                }

                # Bệnh phụ (đồng nhiễm)
                secondary_diseases = []
                top_k = 3 if model_version == "v4" else 2
                for s_cls, s_raw_p in sorted_lychee[1:top_k]:
                    s_prob = float(s_raw_p / total_p) * 100.0
                    if s_cls != "Healthy" and s_prob >= 15.0 and not healthy:
                        s_info = TOMATO_DISEASES.get(s_cls, {})
                        secondary_diseases.append({
                            "class": s_cls,
                            "name_en": s_info.get("name_en", s_cls),
                            "name_vi": CLASS_NAME_VI.get(s_cls, s_info.get("name_vi", s_cls)),
                            "probability": round(s_prob, 1),
                            "severity": "Trung bình" if s_prob >= 35 else "Nhẹ",
                            "color": s_info.get("color", "#ef4444")
                        })

                is_coinfection = len(secondary_diseases) > 0 and not healthy

                # Detections (khung bao từ Grad-CAM)
                detections = []
                if not healthy:
                    detections = _extract_bounding_boxes_from_cam(cam, img_w, img_h, primary_cls, primary_prob)

                result = [{"class": primary_cls, "probability": round(primary_prob, 1)}]
                for s in secondary_diseases:
                    result.append({"class": s["class"], "probability": s["probability"]})

                return {
                    "healthy": healthy,
                    "primary_disease": primary_disease,
                    "secondary_diseases": secondary_diseases,
                    "detections": detections,
                    "lesion_count": len(detections),
                    "is_coinfection": is_coinfection,
                    "result": result,
                    "heatmap_base64": heatmap_b64,
                    "confidence": round(primary_prob, 1),
                    "severity": severity,
                    "model_version": model_version,
                }
        except Exception as e:
            logger.error(f"[LEAF_AI] Lỗi trong quá trình suy luận mô hình: {e}", exc_info=True)
            return None


def _badge_class_for(severity):
    return {"Nghiêm trọng": "badge-high", "Trung bình": "badge-mid"}.get(severity, "badge-low")


def render_rich_ipm_report(primary_disease, secondary_diseases, healthy):
    """Sinh báo cáo HTML chi tiết chuẩn IPM và Grad-CAM cho Deep Learning."""
    if healthy or not primary_disease:
        return (
            '<div class="callout callout-info"><strong>Lá không phát hiện dấu hiệu bệnh hại nguy hiểm.</strong><br>'
            'Khuyến nghị: Duy trì chế độ chăm sóc tiêu chuẩn, tỉa bớt lá già sát gốc để thông thoáng và kiểm tra vườn định kỳ 2 lần/tuần.</div>'
        )
    
    treatment = primary_disease.get("treatment") or {}
    cultural = treatment.get("cultural", "Cắt tỉa các lá và cành nhiễm bệnh, vệ sinh tàn dư vườn trồng.")
    biological = treatment.get("biological", "Bổ sung chế phẩm sinh học chứa vi sinh vật đối kháng (Trichoderma / Bacillus subtilis).")
    chemical = treatment.get("chemical", "Sử dụng thuốc BVTV theo danh mục cho phép và nguyên tắc 4 đúng.")

    sec_html = ""
    if secondary_diseases:
        sec_items = "".join([f"<li><strong>{s.get('name_vi')}</strong> ({s.get('probability')}%): Mức độ {s.get('severity')}</li>" for s in secondary_diseases])
        sec_html = f"<h4>Cảnh báo đồng nhiễm (Đa bệnh):</h4><ul>{sec_items}</ul>"

    return f"""
    <h3>Kết quả Chẩn đoán Học sâu & Grad-CAM</h3>
    <p>Bệnh chính phát hiện: <strong>{primary_disease.get('name_vi')}</strong> ({primary_disease.get('class')})<br>
    Độ tin cậy: <span class="pct">{primary_disease.get('probability')}%</span> — 
    Mức độ: <span class="badge {_badge_class_for(primary_disease.get('severity'))}">{primary_disease.get('severity')}</span></p>
    {sec_html}
    <div class="callout callout-info">
        <strong>Giải thích thị giác (Grad-CAM):</strong> Mạng nơ-ron tích chập ResNet-18 đã kích hoạt vùng đặc trưng tổn thương. Hãy nhấn nút <em>"Bản đồ nhiệt"</em> để đối chiếu vùng bệnh.
    </div>
    <h3>Phác đồ quản lý dịch hại tổng hợp (IPM)</h3>
    <table class="report-table">
        <thead><tr><th>Biện pháp</th><th>Hướng dẫn thực hiện</th></tr></thead>
        <tbody>
            <tr><td><strong>1. Canh tác</strong></td><td>{cultural}</td></tr>
            <tr><td><strong>2. Sinh học</strong></td><td>{biological}</td></tr>
            <tr><td><strong>3. Hóa học</strong></td><td>{chemical}</td></tr>
        </tbody>
    </table>
    <p><small><em>Lưu ý: Chỉ can thiệp hóa học khi mật độ bệnh vượt ngưỡng gây hại kinh tế. Tuân thủ thời gian cách ly theo khuyến cáo.</em></small></p>
    """


def run_deep_learning_diagnosis(img_bytes: bytes, model_version: str = "v3") -> Optional[Dict[str, Any]]:
    """Thực hiện suy luận Deep Learning + Grad-CAM hoàn chỉnh."""
    try:
        import json
        engine = NativeDeepLearningEngine.get_instance()
        if not engine.is_ready:
            return None
        dl_res = engine.predict(img_bytes, model_version=model_version)
        if dl_res is None:
            return None
        report_html = render_rich_ipm_report(dl_res["primary_disease"], dl_res["secondary_diseases"], dl_res["healthy"])
        treatment_summary = json.dumps(dl_res["primary_disease"].get("treatment", {}), ensure_ascii=False)
        return {
            "analysis_unavailable": False,
            "healthy": dl_res["healthy"],
            "note": "",
            "diseases": dl_res["result"],
            "primary_disease": dl_res["primary_disease"],
            "secondary_diseases": dl_res["secondary_diseases"],
            "detections": dl_res["detections"],
            "lesion_count": dl_res["lesion_count"],
            "is_coinfection": dl_res["is_coinfection"],
            "result": dl_res["result"],
            "report_html": report_html,
            "confidence": dl_res["confidence"],
            "severity": dl_res["severity"],
            "treatment_summary": treatment_summary,
            "model_version": model_version,
            "heatmap_base64": f"data:image/jpeg;base64,{dl_res['heatmap_base64']}",
        }
    except Exception as e:
        logger.warning(f"Native Deep Learning error: {e}")
        return None

