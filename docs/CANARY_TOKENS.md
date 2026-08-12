# Canary Tokens — Ω-11 (Honeypot)

<div align="center">

[![C5-REAL Compliant](https://img.shields.io/badge/C5--REAL-Verified-0052CC?style=for-the-badge&logo=shield)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AUDIT_VERDICT_C5_REAL.md)
[![Regime](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AXIOMATIZATION_C5_REAL.md)
[![License](https://img.shields.io/badge/Licencia-Soberana_INV__C5__17-008055?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/STATUS.md)

</div>

> Plantar credenciales FALSAS con alerta real. Si alguien las usa, el
> proveedor notifica la intrusión. Este fichero declara los señuelos
> para que `scripts/canary_check.py` (Ω-12) vigile su presencia.

## Cómo plantar (OPERADOR, ~10 min)

1. **AWS canary** — genera un par de credenciales falsas en
   https://canarytokens.org/generate (tipo "AWS Keys") apuntando a tu
   email/Telegram. Déjalas en un fichero `~/.aws/credentials.canary`
   (fuera del repo) y, si quieres tentar, en un `.env.canary` del repo
   IGNORADO por git. `canary_path: .env.canary`

2. **GitHub token canary** — mismo servicio, tipo "GitHub Token".
   `canary_path: .github_token.canary`

3. **Solana keypair canary** — genera un keypair vacío y anota su
   pubkey; si recibe fondos inesperados o se firma con él, hay fuga.
   `canary_path: .cortex/solana_keypair.canary.json`

## Regla

NUNCA uses una credencial canary para nada real. Su único valor es la
alarma. Si `scripts/canary_check.py` deja de ver una → posible purga maliciosa.

## Estado

- [ ] AWS canary plantado
- [ ] GitHub token canary plantado
- [ ] Solana keypair canary plantado
