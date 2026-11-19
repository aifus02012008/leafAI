from __future__ import annotations
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./data/leafai.db"
    SECRET_KEY: str = "leafai-super-secret-key-at-least-32-chars-long-development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    MODEL_PATH: str = "../model/model.pt"
    MODEL_IMG_SIZE: int = 640
    MODEL_CONFIDENCE_THRESHOLD: float = 0.05  # Base threshold (hạ xuống 0.05 để bắt trọn candidates)
    
    # Per-class confidence thresholds (class_name -> min confidence)
    # Detections below their class threshold are filtered out after inference.
    # Cấu hình dựa trên ma trận đánh giá hiệu năng mô hình:
    CLASS_CONFIDENCE_THRESHOLDS: dict[str, float] = {
        # 1. Bệnh rầy xanh (Tea green leafhopper)
        "Bệnh rầy xanh (Tea green leafhopper)":                          0.25,
        "Bệnh rầy xanh":                                                 0.25,
        "Rầy xanh":                                                      0.25,
        "Rầy xanh hại chè":                                              0.25,
        "Lá chè bị rầy xanh gây hại (Tea green leafhopper infested leaf)": 0.25,
        "Lá chè bị rầy xanh gây hại":                                    0.25,
        "Tea green leafhopper":                                          0.25,
        "Bacterial Leaf and Shoot Blight":                              0.25,
        "Healthy":                                                      0.35,

        # 2. Thối đen lá chè (Black rot of tea)
        "Thối đen lá chè (Black rot of tea)":                           0.25,
        "Black rot of tea":                                             0.25,
        "Gray Blight":                                                  0.25,
        "Grey Blight":                                                  0.25,

        # 3. Cháy nâu lá chè (Brown blight of tea)
        "Cháy nâu lá chè (Brown blight of tea)":                        0.25,
        "Brown blight of tea":                                          0.25,
        "Brown Blight":                                                 0.25,

        # 4. Gỉ sắt lá chè (Leaf rust of tea)
        "Gỉ sắt lá chè (Leaf rust of tea)":                             0.30,
        "Leaf rust of tea":                                             0.30,
        "White spot of tea":                                            0.25,
        "White Scab":                                                   0.25,

        # 5. Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)
        "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)":0.30,
        "Red Spider infested tea leaf":                                 0.30,
        "Red Leaf Spot":                                                0.25,
        "Blister Blight":                                               0.25,

        # 6. Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)
        "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)":0.35,
        "Tea Mosquito bug infested leaf":                               0.35,
        "Helopeltis":                                                   0.30,
        "Algal Leaf Spot":                                              0.25,

        # Nhãn phụ
        "disease":                                                      0.25,

        # Backwards compatibility for existing historical records
        "Tomato___Late_blight":                                         0.15,
        "Tomato___Bacterial_spot":                                      0.50,
        "Tomato___Early_blight":                                        0.50,
        "Tomato___Septoria_leaf_spot":                                  0.50,
        "Tomato___Leaf_mold":                                           0.50,
        "Tomato___Powdery_mildew":                                      0.50,
    }
    DEFAULT_CLASS_CONFIDENCE: float = 0.25  # Fallback: Giữ ngưỡng mặc định cho các nhãn chưa được cấu hình riêng
    MAX_UPLOAD_SIZE_MB: int = 10
    
    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    @property
    def resolved_model_path(self) -> str:
        """Resolve model path reliably regardless of cwd."""
        backend_dir = Path(__file__).resolve().parent.parent.parent
        project_root = backend_dir.parent
        model_path = Path(self.MODEL_PATH)
        
        if model_path.is_absolute() and model_path.exists():
            return str(model_path)
        
        # Check relative to backend_dir
        candidate1 = (backend_dir / model_path).resolve()
        if candidate1.exists():
            return str(candidate1)
            
        # Check relative to project_root
        candidate2 = (project_root / model_path).resolve()
        if candidate2.exists():
            return str(candidate2)
            
        # Standard location in project_root/model/model.pt
        candidate3 = (project_root / "model" / "model.pt").resolve()
        if candidate3.exists():
            return str(candidate3)
            
        return str(candidate1)
    
    @property
    def storage_dir(self) -> Path:
        backend_dir = Path(__file__).resolve().parent.parent.parent
        d = backend_dir / "app" / "storage"
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    @property
    def originals_dir(self) -> Path:
        d = self.storage_dir / "originals"
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    @property
    def results_dir(self) -> Path:
        d = self.storage_dir / "results"
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    @property
    def data_dir(self) -> Path:
        backend_dir = Path(__file__).resolve().parent.parent.parent
        d = backend_dir / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Mapping label đề xuất theo danh sách khách hàng:
LABEL_MAPPING: dict[str, str] = {
    # 1. Bệnh rầy xanh (Tea green leafhopper)
    "Bệnh rầy xanh (Tea green leafhopper)": "Bệnh rầy xanh (Tea green leafhopper)",
    "Bệnh rầy xanh": "Bệnh rầy xanh (Tea green leafhopper)",
    "Rầy xanh": "Bệnh rầy xanh (Tea green leafhopper)",
    "Rầy xanh hại chè": "Bệnh rầy xanh (Tea green leafhopper)",
    "Lá chè bị rầy xanh gây hại (Tea green leafhopper infested leaf)": "Bệnh rầy xanh (Tea green leafhopper)",
    "Lá chè bị rầy xanh gây hại": "Bệnh rầy xanh (Tea green leafhopper)",
    "Tea green leafhopper": "Bệnh rầy xanh (Tea green leafhopper)",
    "Bacterial Leaf and Shoot Blight": "Bệnh rầy xanh (Tea green leafhopper)",

    # Healthy / Lá khỏe mạnh (không phải bệnh hại)
    "Healthy": "Healthy",
    "healthy": "Healthy",
    "Khỏe mạnh": "Healthy",
    "Lá khỏe mạnh": "Healthy",
    "Lá chè khỏe mạnh": "Healthy",

    # 2. Grey Blight / Gray Blight -> Thối đen lá chè (Black rot of tea)
    "Grey Blight": "Thối đen lá chè (Black rot of tea)",
    "Gray Blight": "Thối đen lá chè (Black rot of tea)",
    "Black rot of tea": "Thối đen lá chè (Black rot of tea)",
    "Thối đen lá chè (Black rot of tea)": "Thối đen lá chè (Black rot of tea)",

    # 3. Brown Blight -> Cháy nâu lá chè (Brown blight of tea)
    "Brown Blight": "Cháy nâu lá chè (Brown blight of tea)",
    "Brown blight of tea": "Cháy nâu lá chè (Brown blight of tea)",
    "Cháy nâu lá chè (Brown blight of tea)": "Cháy nâu lá chè (Brown blight of tea)",

    # 4. White Scab -> Gỉ sắt lá chè (Leaf rust of tea)
    "White Scab": "Gỉ sắt lá chè (Leaf rust of tea)",
    "White spot of tea": "Gỉ sắt lá chè (Leaf rust of tea)",
    "Leaf rust of tea": "Gỉ sắt lá chè (Leaf rust of tea)",
    "Gỉ sắt lá chè (Leaf rust of tea)": "Gỉ sắt lá chè (Leaf rust of tea)",

    # 5. Blister Blight -> Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)
    "Blister Blight": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
    "Red Spider infested tea leaf": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
    "Red Leaf Spot": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
    "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",

    # 6. Algal Leaf Spot -> Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)
    "Algal Leaf Spot": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
    "Tea Mosquito bug infested leaf": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
    "Helopeltis": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
    "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",

    # Tomato legacy mapping
    "Tomato___Late_blight": "Thối đen lá chè (Black rot of tea)",
    "Tomato___Septoria_leaf_spot": "Gỉ sắt lá chè (Leaf rust of tea)",
    "Tomato___Bacterial_spot": "Bệnh rầy xanh (Tea green leafhopper)",
    "Tomato___Early_blight": "Cháy nâu lá chè (Brown blight of tea)",
    "Tomato___Leaf_mold": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
    "Tomato___Powdery_mildew": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
}

def map_disease_label(raw_label: str | None) -> str:
    """Map any model/catalog label to the customer's standardized label."""
    if not raw_label:
        return ""
    clean = raw_label.strip()
    return LABEL_MAPPING.get(clean, clean)
