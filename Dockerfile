# Eén image met backend + gebouwde frontend. Gebruikt door deploy/docker-compose.yml (zie deploy/README.md).

# --- 1. Frontend bouwen ---------------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- 2. Backend ------------------------------------------------------------------
FROM python:3.13-slim
WORKDIR /app/backend

COPY backend/requirements.txt ./
# Testpakketten (pytest, httpx) zijn niet nodig op de server.
RUN sed '/^# Alleen voor tests/,$d' requirements.txt > requirements-prod.txt \
    && pip install --no-cache-dir -r requirements-prod.txt

COPY backend/app ./app
COPY --from=frontend /frontend/dist /app/static

ENV DATABASE_PATH=/data/app.db \
    FRONTEND_DIR=/app/static \
    PYTHONUNBUFFERED=1

EXPOSE 8080
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
