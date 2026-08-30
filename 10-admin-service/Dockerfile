# ---- Base image ----
FROM python:3.12-slim AS base

# ---- Builder stage ----
FROM base AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# ---- Production stage ----
FROM base
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ ./src/
EXPOSE 8085
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8085"]
