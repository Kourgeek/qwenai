# ──────────────────────────────────────────────────────────────
# User Service — Dockerfile
# Base: python:3.12-slim
# Exposes: HTTP (FastAPI) + gRPC (same port via uvicorn)
# ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# ── dependencies layer (cached unless requirements change) ──
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    rm -rf /root/.cache

# ── application layer ──
COPY src/ src/

# ── runtime ───────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8085
EXPOSE 50053

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8085"]
