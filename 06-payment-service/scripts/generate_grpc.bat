@echo off
REM Generate gRPC Python stubs from payment.proto
REM Run this from the project root after installing grpcio-tools
echo Generating gRPC Python stubs...
python -m grpc_tools.protoc -Iprotos --python_out=src\grpc_server --grpc_python_out=src\grpc_server protos/payment.proto
echo Done. Generated src/grpc_server/payment_pb2.py and src/grpc_server/payment_pb2_grpc.py
