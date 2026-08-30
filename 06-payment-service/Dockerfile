# =============================================================================
# HyperScale Payment Service — Dockerfile
# =============================================================================
FROM python:3.12-slim AS base

# Prevent Python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for asyncpg and hiredis
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Copy and install Python dependencies
# ---------------------------------------------------------------------------
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source and proto files
COPY src/ src/
COPY proto/ ./proto/

# Generate Python gRPC code (after grpcio-tools is installed)
RUN python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=./src \
    --grpc_python_out=./src \
    v1/payment.proto

# Set PYTHONPATH so generated modules are importable
ENV PYTHONPATH=/app/src

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
EXPOSE 8082
EXPOSE 50056
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8082"]
