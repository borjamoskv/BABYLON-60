# Canary Tokens — Ω-11 (Honeypot)

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
alarma. Si `canary_check.py` deja de ver una → posible purga maliciosa.

## Estado

- [ ] AWS canary plantado
- [ ] GitHub token canary plantado
- [ ] Solana keypair canary plantado
