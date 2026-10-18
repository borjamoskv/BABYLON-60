# Stage 1: Build environment
FROM python:3.14-slim-bookworm AS builder

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
COPY src ./src
COPY 00_ABZU_KERNEL ./00_ABZU_KERNEL
COPY 01_KISH_ENGINE ./01_KISH_ENGINE
COPY 02_EDIN_SWARMS ./02_EDIN_SWARMS
COPY README.md LICENSE ./

RUN uv venv \
    && uv pip install maturin cffi setuptools \
    && uv sync --frozen --no-dev
COPY . .

# Stage 2: Minimal Runtime environment (Non-root user)
FROM python:3.14-slim-bookworm AS runner

LABEL org.opencontainers.image.title="BABYLON-60" \
      org.opencontainers.image.description="BABYLON-60 C5-REAL execution kernel: BFT ledgers, onco-transducer, exergy pipelines" \
      org.opencontainers.image.url="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.source="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.vendor="Borja Moskv" \
      org.opencontainers.image.licenses="Sovereign Dual-License (Non-Commercial / Enterprise)"

WORKDIR /app
RUN useradd -m -u 1000 babylon60

COPY --from=builder --chown=babylon60:babylon60 /app /app
COPY --from=builder /root/.local /home/babylon60/.local

ENV PATH="/home/babylon60/.local/bin:/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/01_KISH_ENGINE:/app/02_EDIN_SWARMS:/app:."

USER babylon60

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

ENTRYPOINT ["python", "-m", "babylon60.cli.main_dispatcher"]
CMD ["dashboard"]
