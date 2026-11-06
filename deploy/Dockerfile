# ============================================================================
# AGENTS.ARCHI / BABYLON-60 — Minimal Sovereign Attestation Container
# Model: BYOC (Bring Your Own Compute) | Alpine Scratch Linux
# ============================================================================

# Stage 1: Build binary
FROM rust:1.80-alpine AS builder

RUN apk add --no-cache musl-dev

WORKDIR /app
COPY . .

RUN cargo build --release -p babylon-attest

# Stage 2: Minimal runtime image
FROM alpine:3.20

RUN apk add --no-cache ca-certificates

WORKDIR /root
COPY --from=builder /app/target/release/babylon-attest /usr/local/bin/babylon-attest

ENV BABYLON_HOME=/var/lib/babylon
RUN mkdir -p /var/lib/babylon

VOLUME ["/var/lib/babylon"]

EXPOSE 6060

ENTRYPOINT ["babylon-attest"]
CMD ["serve", "--port", "6060", "--host", "0.0.0.0"]
