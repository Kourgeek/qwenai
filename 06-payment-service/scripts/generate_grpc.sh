#!/usr/bin/env bash
# Generate gRPC Python stubs from payment.proto
# Run from project root: bash scripts/generate_grpc.sh

set -euo pipefail

echo "Generating gRPC Python stubs..."
python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=src/grpc_server \
    --grpc_python_out=src/grpc_server \
    protos/payment.proto

echo "Done. Generated src/grpc_server/payment_pb2.py and src/grpc_server/payment_pb2_grpc.py"
