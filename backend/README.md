# LEAF_AI — Backend Service

FastAPI REST API powering the LEAF_AI leaf disease detection platform with YOLO object detection, SQLite persistence, and JWT authentication.

---

## 1. Prerequisites

- Python 3.10+ (Tested on Python 3.12.3)
- PyTorch (CPU or CUDA compatible)
- SQLite3

---

## 2. Setup & Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PyTorch CPU (recommended for CPU environments)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install all backend requirements
pip install -r requirements.txt
```

---

## 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Configure parameters in `.env`:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./data/leafai.db
SECRET_KEY=<random string, >= 32 chars; required when APP_ENV=production>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_ORIGIN=http://localhost:5173
MODEL_PATH=../model/best.pt
MODEL_IMG_SIZE=640
MODEL_CONFIDENCE_THRESHOLD=0.25
MAX_UPLOAD_SIZE_MB=10
```

---

## 4. Database Setup

Database tables and the disease catalog are initialized automatically during the FastAPI application lifespan startup.

To manually trigger or verify database initialization:

```bash
venv/bin/python -c "from app.db.init_db import init_database; init_database(); print('Database initialized!')"
```

The SQLite database file is persisted at `backend/data/leafai.db`.

---

## 5. Starting the Server

Run Uvicorn from the `backend/` directory:

```bash
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 6. Interactive API Documentation

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 7. Running Backend Tests

Run the test suite with pytest:

```bash
venv/bin/pytest app/tests/test_api.py -v
```

All integration tests cover:
- Health check and YOLO model status
- Disease catalog retrieval
- User registration and login flow
- Tenant isolation of dashboard & history
- Image validation, real YOLO inference, and safe record deletion

---

## 8. Common Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `FileNotFoundError: Model file not found` | `MODEL_PATH` cannot be located relative to backend root | Verify `model/best.pt` exists in the project root. The backend resolves both `../model/best.pt` and absolute paths. |
| `ModuleNotFoundError: No module named 'torch'` | PyTorch is missing in the active virtual environment | Run `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu` |
| `413 Request Entity Too Large` | Uploaded image exceeds `MAX_UPLOAD_SIZE_MB` | Upload an image smaller than 10MB or adjust `MAX_UPLOAD_SIZE_MB` in `.env`. |
| `503 Model not loaded` | Model weights could not be loaded into memory at startup | Check startup terminal logs for PyTorch/ultralytics compatibility errors. |
