# TORCH — single container: React UI + FastAPI (for Render, Railway, Fly.io, etc.)
FROM node:20-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Same-origin API when served by FastAPI
ENV VITE_API_BASE=
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app/backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /build/frontend/dist ./static

ENV TORCH_SERVE_STATIC=true
ENV TORCH_ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

# Render/Railway set PORT; local default 8010
ENV PORT=8010
EXPOSE 8010

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8010}"]
