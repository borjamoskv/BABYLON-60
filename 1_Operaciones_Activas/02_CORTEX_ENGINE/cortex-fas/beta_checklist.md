# Beta Cerrada — Checklist Operativo

## Pre-launch (Day 0)
- [ ] API live (Fly.io o Hetzner)
- [ ] SSL activo (Let's Encrypt)
- [ ] Dashboard activo (Streamlit)
- [ ] Stripe plan Starter (€49) activo
- [ ] Webhook registrado (stripe listen)
- [ ] DB migraciones aplicadas
- [ ] Health check OK (GET /health)

## Usuarios piloto (Day 1–3)
- [ ] 5–10 invitaciones manuales (email directo)
- [ ] 1 caso de uso asignado por usuario
- [ ] API key entregada manualmente
- [ ] Canal de feedback (email o DM)

## KPIs semana 1 (Day 7)
- [ ] Activaciones: ≥ 3 usuarios (usaron /stress_test al menos 1 vez)
- [ ] Retención 7d: ≥ 1 usuario volvió en 7 días
- [ ] Conversión: ≥ 1 free → paid

## Queries de telemetría (ejecutar en Postgres)

-- Activaciones
SELECT COUNT(*) FROM users WHERE activated_at IS NOT NULL;

-- Retención 7d
SELECT email, retained FROM retention_7d;

-- Conversión
SELECT * FROM conversion_funnel;

-- Requests por usuario
SELECT u.email, COUNT(l.id) AS requests
FROM users u
LEFT JOIN usage_logs l ON l.user_id = u.id
GROUP BY u.email ORDER BY requests DESC;

## Criterio de decisión (Day 7)

Si NO hay:
- activación → problema de onboarding
- repetición → problema de valor percibido
- conversión → problema de pricing o propuesta

Entonces no es problema técnico. Es problema de mercado.
Pivot o kill. Sin anestesia.
