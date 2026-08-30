FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies for asyncpg and hiredis
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source
COPY src/ ./src/

# Copy proto files and generate Python gRPC code
COPY proto/ ./proto/
RUN pip install grpcio-tools && \
    python -m grpc_tools.protoc \
    --proto_path=proto/catalog \
    --python_out=./src \
    --grpc_python_out=./src \
    v1/catalog.proto

# Ensure generated pb2 files are importable
ENV PYTHONPATH=/app/src

# Expose HTTP port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8081"]
