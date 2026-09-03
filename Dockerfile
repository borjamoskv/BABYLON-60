# Stage 1: Build environment
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rustup \
    PATH="/opt/cargo/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    python3-dev \
    protobuf-compiler \
    libprotobuf-dev \
    clang \
    libclang-dev \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:/opt/cargo/bin:$PATH"

COPY pyproject.toml uv.lock Cargo.toml Cargo.lock* ./
COPY crates ./crates
COPY packages ./packages
COPY src ./src
COPY experiments ./experiments
COPY README.md LICENSE ./

RUN uv venv \
    && uv pip install maturin cffi setuptools \
    && uv sync --frozen --no-dev
COPY . .

# Stage 2: Minimal Runtime environment (Non-root user)
FROM python:3.12-slim-bookworm AS runner

LABEL org.opencontainers.image.title="BABYLON-60" \
      org.opencontainers.image.description="CORTEX C5-REAL execution kernel (BABYLON-60): BFT ledgers, onco-transducer, exergy pipelines" \
      org.opencontainers.image.url="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.source="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.vendor="Borja Moskv" \
      org.opencontainers.image.licenses="Sovereign Dual-License (Non-Commercial / Enterprise)"

WORKDIR /app
RUN useradd -m -u 1000 cortex

COPY --from=builder /app /app
COPY --from=builder /root/.local /home/cortex/.local

ENV PATH="/home/cortex/.local/bin:/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/packages:/app/experiments:."

USER cortex

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import babylon60; print('BABYLON-60 OK')" || exit 1

ENTRYPOINT ["python", "-m", "babylon60.cli.onco_transducer"]
CMD ["--help"]
