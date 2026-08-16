# C5-REAL EXERGY CERTIFIED - SOVEREIGN CONTAINER IMAGE
# Target: ghcr.io/borjamoskv/babylon-60

# Stage 1: Rust Bare-Metal C-ABI Builder
FROM rust:1.85-slim as builder

WORKDIR /build
COPY src/06_apps/mcp_c5_abi_bridge/c5_abi_core.rs .

RUN rustc --crate-type cdylib -C opt-level=3 -C lto=thin -C panic=abort c5_abi_core.rs -o libc5_abi_core.so

# Stage 2: Minimal Production Runtime
FROM python:3.12-slim

LABEL org.opencontainers.image.title="BABYLON-60 Sovereign Container"
LABEL org.opencontainers.image.description="C5-REAL High-Exergy Engine & MCP C-ABI Bridge"
LABEL org.opencontainers.image.source="https://github.com/borjamoskv/BABYLON-60"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Copy compiled C-ABI shared library and MCP server
COPY --from=builder /build/libc5_abi_core.so /app/scratch/libc5_abi_core.so
COPY src/06_apps/mcp_c5_abi_bridge/mcp_server.py /app/mcp_server.py

RUN chmod +x /app/mcp_server.py

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python3", "/app/mcp_server.py"]
