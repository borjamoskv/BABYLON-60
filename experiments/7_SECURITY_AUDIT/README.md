# 7_SECURITY_AUDIT — Motores de Auditoría de Seguridad y Supply Chain

Herramientas activas de auditoría forense, detección de dependencias fantasma y análisis de supply chain CI/CD.

| Script | Propósito |
|---|---|
| `existence_gap.py` | Motor de detección de imports/módulos fantasma (57KB, activo) |
| `ci_supply_chain.py` | Auditor de supply chain en workflows CI/CD |
| `dashboard.html` | Dashboard interactivo de resultados de auditoría |
| `poc_c5_ultimate_falsification.py` | PoC de falsación C5-REAL completa |
| `fix_slopsquatting.py` | Reparador de typosquatting en dependencias |

> Motor principal: `existence_gap.py` — detecta huecos de existencia (slopsquatting, dependency confusion, CI injection).
