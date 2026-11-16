---
name: c5-html-report-injection-audit
display_name: 'Auditoría de Inyección HTML en Generadores de Reportes'
description: 'Verifica el escape HTML de datos del ledger en exportadores Jinja2 y string.Template. Dispara con "inyección html", "xss reporte", "autoescape jinja", "auditar exportador", "escape de ledger".'

role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Auditoría de inyección HTML en generadores de reportes

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## Origen (evidencia verificada, BABYLON-60, 2026-10-14)
`jinja2.select_autoescape(["html","xml"])` compara el **sufijo del nombre de plantilla**. `base_report.html.j2` termina en `.j2`, así que Jinja renderizaba sin escape mientras el motor fallback `string.Template` sí escapaba. Un escape visible en una ruta no prueba el escape en la otra.

## Procedimiento
1. Localiza todos los motores de render (Jinja2 y fallback stdlib) con `grep -rn "Environment\|string.Template\|html.escape"`. Audita **cada uno**.
2. Jinja2: para plantillas `*.html.j2` usa `autoescape=True`. Marca `|safe` solo contenido estático de confianza (p. ej. CSS de tema cargado de fichero), nunca datos del ledger.
3. Prueba empírica obligatoria: inyecta `<script>alert(1)</script>"><img src=x onerror=1>` en todos los campos del certificado y renderiza con cada motor (`force_fallback=True` y `False`).
4. Aserciones: el cuerpo (sin `<style>`) no contiene `<script>alert` ni `<img src=x`, y sí contiene `&lt;script&gt;`.
5. Deja el test como regresión parametrizada en `tests/` (ejemplo: `tests/test_compliance_html_injection.py` en BABYLON-60).

## Informe Markdown
Los exportadores Markdown también interpolan datos del ledger: verifica un helper de escape (p. ej. `_md_escape`) en cada campo interpolado.

## Shell (zsh)
zsh no divide por palabras las variables sin comillas. Usa arrays para listas de ficheros:
```bash
F=(a.py b.py c.py)
git add -- "${F[@]}"
```
Nunca `git add -- $F`: falla con `pathspec ... did not match`.

## Límites
- Cubre inyección en HTML/Markdown generado; no sustituye una auditoría CSP ni de cabeceras del visor.
- Un test verde prueba los campos inyectados, no los que no se enumeraron: enumera todos los campos del DTO.
