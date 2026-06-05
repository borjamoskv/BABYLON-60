---
description: "Protocolo automatizado C5-REAL para extraer grafos de recomendación, medir concentración anómala y filtrar SOTA mediante inferencia causal estructural."
workflow: mafia-ai-radar
expected_duration_min: 30
---

# /Mafia-AI-Radar (C5-REAL Structural Protocol)

**Objetivo:** Medir empíricamente la concentración anómala de recomendaciones cruzadas en ecosistemas de creadores/newsletters y detectar asimetrías entre visibilidad y output real (Alpha).

**Tesis Axiomática:** *Existe un núcleo de nodos que se recomiendan de forma desproporcionada entre sí, generando una concentración de visibilidad significativamente superior a la observada en el ecosistema general.* (Hipótesis estructural falsable).

**Frecuencia Recomendada:** Semanal (Ejecución vía cron o trigger manual).

## FASE 1: Extracción de Topología Estructural
Extracción de aristas priorizando fuentes de datos estructuradas para evitar la deriva de selectores HTML.

```bash
# REGLA DE EXTRACCIÓN: JSON > HTML Parsing
cd $CORTEX_ROOT/10_PROJECTS/cortex-persist
uv run --with feedparser --with networkx --with requests python scripts/extractor_grafo_reputacion.py
```
*Validación:* Exportación a `data/reputation_graph/structural_graph.graphml`.

## FASE 2: Cálculo de Métricas de Red (Falsación Empírica)
Procesamiento del grafo utilizando métricas puras de centralidad y topología, sin inferir intenciones:

**Tier 1 Metrics:**
*   `InDegree`: Detección de hubs de atención.
*   `Reciprocity`: Porcentaje de enlaces bidireccionales vs unidireccionales.
*   `Modularity`: Detección de comunidades cerradas.
*   `Assortativity`: Tendencia a enlazar a perfiles de características similares.

```bash
cd $CORTEX_ROOT/10_PROJECTS/cortex-persist
uv run --with networkx --with pandas python scripts/calculadora_smoke_index.py
```
*Validación:* Revisión de `data/reputation_graph/concentration_index_report.csv` generado.

## FASE 3: Extracción de Alpha (Builders Asimétricos)
Identificar nodos con alta asimetría (alto output empírico / baja centralidad en el grafo de recomendaciones).

```bash
cd $CORTEX_ROOT/10_PROJECTS/cortex-persist
uv run python scripts/alpha_extractor_c5.py
```
*Acción Automática:* Inyectar los perfiles devueltos directamente a las colas prioritarias de `MOSKV-1` para lectura SOTA preferente.

## FASE 4: Ejecución del Firewall Cognitivo
Aplicar umbrales de concentración: Si `Internal_Recommendations > 80%` y `Sector_Average < 30%`, el clúster se clasifica como *cámara de eco asilada*.

```bash
cd $CORTEX_ROOT/10_PROJECTS/cortex-persist
uv run python scripts/firewall_cognitivo_c5.py
```
*Acción Automática:* Disminuir ponderación de los payloads de entrada provenientes de clústeres hiper-modulares cerrados.

## FASE 5: Cristalización (Git Sentinel)
```bash
cd $CORTEX_ROOT/10_PROJECTS/cortex-persist
git add data/reputation_graph/ scripts/
git commit -m "chore(cortex): actualizacion de topologia estructural y matriz de concentracion"
```