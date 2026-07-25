# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --all-extras
COPY . .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
LABEL maintainer="borjamoskv"
LABEL org.opencontainers.image.source="https://github.com/borjamoskv/BABYLON-60"
LABEL org.opencontainers.image.description="C5-REAL Execution Kernel API"
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

# Healthcheck to verify C5-REAL attestation
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Entrypoint to run the REST API server
CMD ["python", "-m", "babylon60.api.server"]
