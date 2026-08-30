FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for asyncpg (libpq-dev) and grpc_tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files and install Python packages
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]"

# Copy application source first
COPY src/ ./src/

# Copy proto files and generate Python gRPC code
COPY proto/ ./proto/
RUN pip install grpcio-tools && \
    python -m grpc_tools.protoc \
    --proto_path=proto/auth-service \
    --python_out=./src \
    --grpc_python_out=./src \
    auth/v1/auth.proto

# Create __init__.py for generated package
RUN touch src/auth/__init__.py src/auth/v1/__init__.py 2>/dev/null; true

# Ensure generated pb2 files are importable
ENV PYTHONPATH=/app/src

# Expose the gRPC port
EXPOSE 50052

# Run the application (FastAPI on 8080, gRPC on 50052)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
