# Stage 1: Build environment
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rustup \
    PATH="/opt/cargo/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    protobuf-compiler \
    libprotobuf-dev \
    clang \
    libclang-dev \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock ./
COPY strike_rs ./strike_rs
RUN cd strike_rs && cargo build --release
RUN uv sync --frozen --no-dev
COPY . .

# Stage 2: Minimal Runtime environment (Non-root user)
FROM python:3.12-slim AS runner

WORKDIR /app
RUN useradd -m -u 1000 appuser

COPY --from=builder /app /app
COPY --from=builder /root/.local /home/appuser/.local

ENV PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

CMD ["python", "-m", "babylon60.cli.onco_transducer"]
