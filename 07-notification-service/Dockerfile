FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for grpcio wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application source
COPY src/ ./src/

# Copy proto files and generate Python gRPC code
COPY src/grpc_server/notification.proto ./proto/
RUN pip install grpcio-tools && \
    python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=./src/grpc_server \
    --grpc_python_out=./src/grpc_server \
    notification.proto

# Ensure generated pb2 files are importable
# PYTHONPATH includes /app/src for 'from src.grpc_server import ...'
# and /app/src/grpc_server so bare 'import notification_pb2' in pb2_grpc.py resolves
ENV PYTHONPATH=/app/src:/app/src/grpc_server

# Expose HTTP port
EXPOSE 8086

# Expose gRPC port
EXPOSE 50057

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8086"]
