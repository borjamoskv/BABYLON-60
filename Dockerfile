# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY . .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/babylon60 /app/babylon60
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python", "-m", "babylon60"]
