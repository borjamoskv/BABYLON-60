# Stage 1: Build environment
FROM python:3.14-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock Cargo.toml Cargo.lock* ./
COPY crates ./crates
COPY src ./src
COPY 00_ABZU_KERNEL ./00_ABZU_KERNEL
COPY 01_KISH_ENGINE ./01_KISH_ENGINE
COPY 02_EDIN_SWARMS ./02_EDIN_SWARMS
COPY README.md LICENSE ./
COPY docs/skills.json docs/skills-lock.json ./docs/
COPY .agents/skills ./.agents/skills

RUN uv sync --locked --no-dev --no-editable \
    && uv pip check
COPY . .

# Stage 2: Minimal Runtime environment (Non-root user)
FROM python:3.14-slim-trixie AS runner

LABEL org.opencontainers.image.title="BABYLON-60" \
      org.opencontainers.image.description="BABYLON-60 C5-REAL execution kernel: BFT ledgers, onco-transducer, exergy pipelines" \
      org.opencontainers.image.url="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.source="https://github.com/borjamoskv/BABYLON-60" \
      org.opencontainers.image.vendor="Borja Moskv" \
      org.opencontainers.image.licenses="Sovereign Dual-License (Non-Commercial / Enterprise)"

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 babylon60

COPY --from=builder --chown=babylon60:babylon60 /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME="/home/babylon60"

USER babylon60

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

ENTRYPOINT ["python", "-m", "babylon60.cli.main_dispatcher"]
CMD ["dashboard"]
