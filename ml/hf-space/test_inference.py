# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import io
import os

model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tomato_model.pt")
if not os.path.exists(model_path):
    print("Model not found yet")
    sys.exit(0)

checkpoint = torch.load(model_path, map_location="cpu")
print("Checkpoint loaded. Best Acc:", checkpoint.get("best_acc"), "Classes:", checkpoint.get("classes"))

model = models.resnet18()
model.fc = torch.nn.Sequential(
    torch.nn.Dropout(p=0.3),
    torch.nn.Linear(model.fc.in_features, len(checkpoint["classes"]))
)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Test dummy image
img = Image.new("RGB", (256, 256), color=(45, 120, 45))
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
tensor = transform(img).unsqueeze(0)

with torch.no_grad():
    output = model(tensor)
    probs = torch.softmax(output, dim=1)[0]

top3_prob, top3_idx = torch.topk(probs, 3)
classes = checkpoint["classes"]
for p, idx in zip(top3_prob, top3_idx):
    print(f"  Class: {classes[idx]:<30} Prob: {p.item()*100:.2f}%")
