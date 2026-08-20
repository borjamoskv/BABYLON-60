# 🔄 cortex-system — MEJORAlo Perpetual Loop & Retraining Engine

> **ESTADO:** Congelado / Vault Histórico  
> **Transducción en Producción:** [`scripts/c5_cortex/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex) y [`packages/babylon60/transducers/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/transducers)

---

## 📐 Estructura de Ficheros

| Fichero | Descripción Técnica |
|---|---|
| [`daemons/mejora_loop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/cortex-system/daemons/mejora_loop.py) | **MEJORAlo Perpetual Loop**: Demonio de monitoreo continuo de salud de proyectos y auto-disparo de olas de mejora. |
| [`offline/retraining_loop.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/cortex-system/offline/retraining_loop.py) | Estructura base / stub para bucles de reentrenamiento offline de modelos de lenguaje. |

---

## 📊 Fórmula del Decay Score (Puntuación de Degradación)

El demonio escanea la base de datos `cortex.db` y evalúa la urgencia de optimización de un proyecto mediante la siguiente función ponderada:

$$\text{Decay Score} = \min\Big(100, \text{Error Score} + \text{Ghost Score} + \text{Staleness Score} + \text{Recency Score}\Big)$$

Donde:
* **$\text{Error Score} = \min(10 \times \text{errores activos}, 30)$**
* **$\text{Ghost Score} = \min(12 \times \text{tareas fantasma}, 25)$**
* **$\text{Staleness Score} = \min\left(25, \left\lfloor\frac{\text{horas inactivo} - 72}{24}\right\rfloor \times 5\right)$**
* **$\text{Recency Score} = 20$** (si nunca se ha ejecutado una ola `/mejoralo`)

Si $\text{Decay Score} \ge 40$, el demonio activa una ola `/mejoralo` respetando un tiempo de enfriamiento (*cooldown*) de 30 minutos.
