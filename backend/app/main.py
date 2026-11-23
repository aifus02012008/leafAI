import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from app.core.config import settings
from app.services import storage
from app.db.init_db import init_database
from app.core.config import validate_production_settings
from app.core.crops import DEFAULT_CROP_CODE, get_crop, list_crops
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import client_ip, limited, too_many_requests
from app.services.model_registry import model_registry
from app.api.routes import auth, predict, history, diseases, dashboard, crops, tools, treatments, assistant, radar, farms, internal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("leaf_ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LEAF_AI backend...")
    validate_production_settings(settings)
    
    # 1. Initialize SQLite database & tables & initial disease data
    try:
        init_database()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failure: {e}", exc_info=True)
        
    # 2. Preload the default crop's model; other crops load lazily on first use.
    try:
        model_registry.get(get_crop(DEFAULT_CROP_CODE))
    except Exception as e:
        logger.error(f"AI Model failed to load at startup: {e}. Model predictions will report error until resolved.")
        
    yield
    
    logger.info("LEAF_AI backend shut down cleanly.")

app = FastAPI(
    title="LEAF_AI — Tea Plant (Camellia sinensis) Foliar Disease Detection API",
    description="Real full-stack tea leaf disease detection and complete treatment management using YOLO deep learning.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://hieu0345984559.github.io",
]

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*(github\.io|vercel\.app|onrender\.com|hf\.space)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_registry.is_loaded(DEFAULT_CROP_CODE),
        "model_classes": list(model_registry.class_names(DEFAULT_CROP_CODE).values()),
        "crops": [
            {
                "code": crop.code,
                "available": model_registry.is_available(crop),
                "loaded": model_registry.is_loaded(crop.code),
            }
            for crop in list_crops()
        ],
        "version": "1.0.0"
    }

# Secure image serving endpoint
def _remote_image_url(key: str) -> str | None:
    """Signed URL from the remote image store when the local copy is missing (e.g. after a redeploy)."""
    try:
        return storage.get_storage().signed_url(key)
    except storage.StorageError as exc:
        logger.warning("Remote image lookup failed for %s (%s)", key, type(exc).__name__)
        return None


@app.get("/api/images/{folder}/{filename}", tags=["Media"])
def get_image(folder: str, filename: str, request: Request):
    """Safely stream stored images with path traversal defenses."""
    if folder not in ("originals", "results"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image folder specified."
        )
        
    # Guard against traversal
    safe_name = Path(filename).name
    if safe_name != filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed file path."
        )
        
    target_path = (settings.storage_dir / folder / safe_name).resolve()
    if not target_path.exists() or not target_path.is_file():
        if limited(f"img:{client_ip(request)}", settings.IMAGE_REDIRECT_PER_MINUTE):
            raise too_many_requests()
        remote = _remote_image_url(f"{folder}/{safe_name}")
        if remote:
            return RedirectResponse(remote, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested image could not be located."
        )
        
    # Ensure file is inside allowed directory
    if settings.storage_dir not in target_path.parents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )
        
    return FileResponse(str(target_path))

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Include routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(diseases.router)
app.include_router(dashboard.router)
app.include_router(crops.router)
app.include_router(tools.router)
app.include_router(treatments.router)
app.include_router(assistant.router)
app.include_router(radar.router)
app.include_router(farms.router)
app.include_router(internal.router)

# Mount frontend dist static files for seamless standalone execution
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets")
        app.mount("/leaf_ai/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets_leaf_ai")
        app.mount("/leaf_ai2/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets_leaf_ai2")

    @app.get("/leaf_ai/{full_path:path}")
    async def serve_leaf_ai_subpath(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/leaf_ai2/{full_path:path}")
    async def serve_leaf_ai2_subpath(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))

