FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for asyncpg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install ".[dev]"

# Copy application source first
COPY src/ ./src/

# Copy proto files and generate Python gRPC code (after src is copied)
COPY proto/ ./proto/
RUN python -m grpc_tools.protoc \
    --proto_path=proto/catalog-service \
    --python_out=./src \
    --grpc_python_out=./src \
    catalog/v1/catalog.proto

# Ensure generated pb2 files are importable
ENV PYTHONPATH=/app/src

# Expose HTTP and gRPC ports
EXPOSE 8080 50051

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
