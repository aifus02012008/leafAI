# -*- coding: utf-8 -*-
"""
LEAF_AI — Bộ suy luận mô hình lá vải (dùng chung cho app.py và predict_lychee.py).

- Nạp checkpoint định dạng "leafai-lychee-v1" (train_lychee.py) — đọc arch, lớp, tiền xử lý, temperature, ngưỡng.
- Từ chối checkpoint cà chua cũ thay vì đổi tên lớp (nguyên nhân kết quả sai trước đây).
- TTA (ảnh gốc + lật ngang), xác suất đã hiệu chỉnh, cờ `uncertain` để frontend hỏi thêm Gemini.
- Grad-CAM theo đúng tầng tích chập cuối của từng kiến trúc.
"""
import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from model_zoo import build_model, eval_transform, gradcam_layer

logger = logging.getLogger("leaf_ai_inference")

LYCHEE_CLASSES = {"Healthy", "Anthracnose", "Downy_blight", "Leaf_blight", "Algal_spot", "Erinose", "Other"}
TOMATO_MARKERS = {"Leaf_mold", "Target_spot", "Late_blight", "Early_blight", "Bacterial_spot",
                  "Septoria_leaf_spot", "Tomato_mosaic_virus", "Tomato_yellow_leaf_curl_virus", "Spider_mites"}

CLASS_NAME_VI = {
    "Healthy": "Lá vải khỏe mạnh",
    "Anthracnose": "Thán thư",
    "Downy_blight": "Sương mai",
    "Leaf_blight": "Cháy lá",
    "Algal_spot": "Đốm rong",
    "Erinose": "Nhện lông nhung",
    "Other": "Vấn đề khác (không thuộc 5 bệnh)",
}


class WrongModelError(RuntimeError):
    pass


class GradCAM:
    def __init__(self, model: nn.Module, layer: nn.Module):
        self.model = model
        self.acts = None
        self.grads = None
        layer.register_forward_hook(lambda m, i, o: setattr(self, "acts", o))
        layer.register_full_backward_hook(lambda m, gi, go: setattr(self, "grads", go[0]))

    def __call__(self, x: torch.Tensor, class_idx: int) -> np.ndarray:
        self.model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            x = x.clone().requires_grad_(True)
            out = self.model(x)
            out[0, class_idx].backward()
        if self.acts is None or self.grads is None:
            return np.zeros(x.shape[2:], dtype=np.float32)
        a, g = self.acts.detach(), self.grads.detach()
        self.acts = self.grads = None
        cam = F.relu((g.mean(dim=(2, 3), keepdim=True) * a).sum(1, keepdim=True))
        cam = F.interpolate(cam, size=x.shape[2:], mode="bilinear", align_corners=False)[0, 0].cpu().numpy()
        lo, hi = float(cam.min()), float(cam.max())
        self.model.zero_grad(set_to_none=True)
        return (cam - lo) / (hi - lo) if hi > lo else np.zeros_like(cam)


def heatmap_overlay(img: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> str:
    cam_img = Image.fromarray(np.uint8(255 * cam), mode="L").resize(img.size, Image.Resampling.BILINEAR)
    c = np.asarray(cam_img, dtype=np.float32) / 255.0
    rgb = np.stack([np.clip(1.5 - np.abs(c * 4 - k), 0, 1) for k in (3, 2, 1)], axis=-1)
    blended = Image.blend(img.convert("RGB"), Image.fromarray(np.uint8(rgb * 255)), alpha=alpha)
    buf = io.BytesIO()
    blended.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class LycheeClassifier:
    def __init__(self, path: str, device: Optional[str] = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        ckpt = torch.load(str(path), map_location=self.device, weights_only=False)
        classes: List[str] = list(ckpt.get("classes") or [])
        if not classes or set(classes) & TOMATO_MARKERS or not set(classes) <= LYCHEE_CLASSES | {"Healthy"}:
            raise WrongModelError(
                f"Checkpoint {Path(path).name} không phải mô hình lá vải (lớp: {classes}). "
                "Hãy huấn luyện bằng ml/training/train_lychee.py rồi cập nhật MODEL_DOWNLOAD_URL."
            )
        self.classes = classes
        self.arch = ckpt.get("arch", "resnet18")
        self.img_size = int(ckpt.get("img_size", 224))
        self.temperature = float(ckpt.get("temperature", 1.0))
        self.accept_threshold = float(ckpt.get("accept_threshold", 0.7))
        self.tta = bool(ckpt.get("tta", True))
        self.meta = {
            "format": ckpt.get("format", "legacy"),
            "version": ckpt.get("version", "unknown"),
            "arch": self.arch,
            "classes": classes,
            "img_size": self.img_size,
            "temperature": round(self.temperature, 3),
            "accept_threshold": self.accept_threshold,
            "best_acc": ckpt.get("best_acc"),
            "test_macro_f1": ((ckpt.get("metrics") or {}).get("test") or {}).get("macro_f1"),
            "timestamp": ckpt.get("timestamp"),
        }
        self.model = build_model(self.arch, len(classes), pretrained=False)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.to(self.device).eval()
        self.transform = eval_transform(self.img_size, ckpt.get("eval_resize"), ckpt.get("mean"), ckpt.get("std"))
        self.cam = GradCAM(self.model, gradcam_layer(self.model, self.arch))
        logger.info(f"[OK] Nạp mô hình lá vải {self.arch} {self.meta['version']} — lớp {classes}")

    @torch.no_grad()
    def _logits(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.model(x)
        if self.tta:
            logits = (logits + self.model(torch.flip(x, dims=[3]))) / 2
        return logits[0]

    def predict(self, img: Image.Image, with_heatmap: bool = True, top_k: int = 0) -> Dict[str, Any]:
        img = img.convert("RGB")
        x = self.transform(img).unsqueeze(0).to(self.device)
        probs = F.softmax(self._logits(x) / self.temperature, dim=0).cpu().numpy()
        order = np.argsort(-probs)
        top_idx = int(order[0])
        top_p = float(probs[top_idx])
        second_p = float(probs[order[1]]) if len(order) > 1 else 0.0
        top_cls = self.classes[top_idx]

        # Ca khó: dưới ngưỡng chấp nhận, hai lớp đầu sát nhau, hoặc mô hình nghiêng về "Other"
        reasons = []
        if top_p < self.accept_threshold:
            reasons.append("low_confidence")
        if top_p - second_p < 0.15:
            reasons.append("close_call")
        if top_cls == "Other":
            reasons.append("other_class")

        results = [{
            "class": self.classes[i],
            "name_vi": CLASS_NAME_VI.get(self.classes[i], self.classes[i]),
            "probability": round(100.0 * float(probs[i]), 1),
        } for i in (order[:top_k] if top_k else order)]

        heatmap = None
        if with_heatmap and top_cls not in ("Healthy", "Other"):
            try:
                heatmap = heatmap_overlay(img, self.cam(x, top_idx))
            except Exception as e:  # Grad-CAM lỗi không được làm hỏng kết quả chẩn đoán
                logger.warning(f"Grad-CAM lỗi: {e}")

        return {
            "results": results,
            "top": top_cls,
            "confidence": round(100.0 * top_p, 1),
            "uncertain": bool(reasons),
            "uncertain_reasons": reasons,
            "accept_threshold": round(100.0 * self.accept_threshold, 1),
            "heatmap_base64": heatmap,
            "model": {"arch": self.arch, "version": self.meta["version"], "crop": "lychee"},
        }
