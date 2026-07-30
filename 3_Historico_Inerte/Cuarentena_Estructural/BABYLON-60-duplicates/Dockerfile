FROM python:3.12-slim

# C5-REAL Dockerfile for BABYLON-60 CORTEX

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rustup \
    PATH="/opt/cargo/bin:$PATH"

WORKDIR /app

# Install system dependencies, Rust, and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

# Copy Python manifests and Rust workspace
COPY pyproject.toml uv.lock ./
COPY strike_rs ./strike_rs

# Build Rust extensions
RUN cd strike_rs && cargo build --release

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application source
COPY . .

# Default ignition command
CMD ["uv", "run", "python", "-m", "babylon60.cli.onco_transducer"]
