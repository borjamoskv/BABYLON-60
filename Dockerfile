# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --all-extras
COPY . .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Non-root user creation (INV_C5)
RUN useradd -m -u 1000 app
USER app

# Copy environment and package
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/babylon60 /app/babylon60

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose API port
EXPOSE 8000

# Entrypoint to run the REST API server
CMD ["python", "-m", "babylon60.api.server"]
