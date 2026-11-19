from __future__ import annotations
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    _instance = None
    _model = None
    _model_loaded = False
    _load_error: str | None = None
    _class_names: dict[int, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load the YOLO model once during startup."""
        if self._model_loaded:
            return
            
        model_path = settings.resolved_model_path
        logger.info(f"Loading YOLO model from: {model_path}")
        
        path_obj = Path(model_path)
        if not path_obj.exists():
            self._load_error = f"Model file not found at: {model_path}"
            logger.error(self._load_error)
            raise FileNotFoundError(self._load_error)
            
        try:
            from ultralytics import YOLO
            self._model = YOLO(model_path)
            self._model_loaded = True
            
            # Extract class names
            if hasattr(self._model, "names") and self._model.names:
                self._class_names = self._model.names
            elif hasattr(self._model, "model") and hasattr(self._model.model, "names"):
                self._class_names = self._model.model.names
            else:
                self._class_names = {
                    0: "Algal Leaf Spot",
                    1: "Brown Blight",
                    2: "Gray Blight",
                    3: "Healthy",
                    4: "Helopeltis",
                    5: "Red Leaf Spot"
                }
                
            logger.info(f"Model successfully loaded. Classes ({len(self._class_names)}): {self._class_names}")
        except Exception as e:
            self._load_error = f"Failed to initialize YOLO model: {e}"
            logger.error(self._load_error, exc_info=True)
            raise
    
    @property
    def model(self):
        if not self._model_loaded or self._model is None:
            raise RuntimeError(
                f"Model is not ready. {self._load_error or 'Model initialization failed'}"
            )
        return self._model
    
    @property
    def is_loaded(self) -> bool:
        return self._model_loaded
    
    @property
    def class_names(self) -> dict[int, str]:
        return self._class_names
    
    @property
    def load_error(self) -> str | None:
        return self._load_error
        
    def predict(self, image_path: str, conf: float | None = None, imgsz: int | None = None):
        """Run YOLO inference on target image."""
        confidence = conf if conf is not None else settings.MODEL_CONFIDENCE_THRESHOLD
        img_size = imgsz if imgsz is not None else settings.MODEL_IMG_SIZE
        
        results = self.model.predict(
            source=image_path,
            conf=confidence,
            imgsz=img_size,
            verbose=False
        )
        return results

model_service = ModelService()
