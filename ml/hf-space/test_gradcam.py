# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import io
import time
import base64
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms

class GradCAM:
    def __init__(self, model, target_layer):
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

    def generate(self, input_tensor, target_class_idx):
        self.model.zero_grad()
        output = self.model(input_tensor)
        score = output[0, target_class_idx]
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
        return cam, output


def apply_heatmap(img: Image.Image, cam: np.ndarray, alpha=0.45) -> str:
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


# Run test
import os
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tomato_model.pt")
checkpoint = torch.load(model_path, map_location="cpu")
classes = checkpoint["classes"]

model = models.resnet18()
model.fc = nn.Sequential(nn.Dropout(p=0.3), nn.Linear(model.fc.in_features, len(classes)))
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

target_layer = model.layer4[1].conv2
gradcam = GradCAM(model, target_layer)

img = Image.new("RGB", (256, 256), color=(40, 140, 50))
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
tensor = transform(img).unsqueeze(0)

t0 = time.time()
cam, output = gradcam.generate(tensor, 0)
b64 = apply_heatmap(img, cam)
t_elapsed = (time.time() - t0) * 1000
print(f"GradCAM generated in {t_elapsed:.2f}ms! Heatmap b64 len: {len(b64)}")
print("TEST GRADCAM SUCCESSFUL!")
