# Stage 1: Build React Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
# Empty VITE_API_BASE_URL ensures relative API calls in production
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Python Backend with YOLOv8 & PyTorch
FROM python:3.11-slim
WORKDIR /app

# Install system libraries needed by OpenCV / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies (CPU PyTorch for fast download & low memory)
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code, model weights, and built frontend
COPY backend/ ./backend/
COPY model/ ./model/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Setup non-root user (Hugging Face Spaces requirement UID 1000)
RUN useradd -m -u 1000 user && \
    mkdir -p /app/backend/data /app/backend/app/storage/originals /app/backend/app/storage/results && \
    chown -R user:user /app

USER user

ENV PYTHONPATH=/app/backend
ENV PORT=7860

EXPOSE 7860
EXPOSE 10000

WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
