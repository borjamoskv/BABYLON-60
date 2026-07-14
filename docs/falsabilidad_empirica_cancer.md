# MOSKV-1 APEX: CIENCIA EMPÍRICA Y FALSABILIDAD EN ONCOLOGÍA DE SISTEMAS
# PATH: docs/falsabilidad_empirica_cancer.md

> **"Una red booleana sin anclaje a mediciones moleculares es ciencia ficción topológica (C4-SIM). La predicción de colapso de atractores debe someterse a la criba de la termodinámica real y a la validación empírica in-vitro."**

---

## 1. EL PUENTE EMPÍRICO (De los Datos al Grafo)
El pipeline computacional abandona los grafos teóricos (Scale-Free simulados) y pasa a la ingesta de mediciones reales:
- **Matriz Ómica:** $X \in \mathbb{R}^{M \times N}$ (M muestras, N genes) derivada de RNA-seq (Bulk o Single-Cell).
- **Correlación Empírica:** Cálculo de la matriz de similitud de Pearson o Spearman $S = |cor(X)|$.
- **Adyacencia Biológica (Soft-Thresholding):** $A = S^\beta$ (WGCNA). Se fuerza topología libre de escala empírica ajustando $\beta$.

## 2. REQUISITO DE FALSABILIDAD OBLIGATORIA (C5-REAL RULE Λ13)
Ninguna hipótesis computacional generada por este pipeline tiene validez sin las siguientes condiciones exactas de falsabilidad:

### A. Condición de Falsabilidad Topológica
- **Predicción:** El isomorfismo probabilístico (Node2Vec) entre la Cohorte A (Sensible) y la Cohorte B (Resistente) arroja una divergencia topológica en el módulo M.
- **Horizonte de Falsación:** Inmediato (In-Silico).
- **Condición (Falla):** Si el análisis del DepMap (CRISPR screens) no muestra dependencia celular en al menos el 30% de los Driver Nodes identificados en el módulo M de las líneas celulares equivalentes, la hipótesis topológica queda **REFUTADA** y el grafo está sobreajustado al ruido.

### B. Condición de Falsabilidad Cinética (Intervención)
- **Predicción:** La inhibición combinada de los Driver Nodes $\{D_1, D_2\}$ colapsa el atractor proliferativo hacia senescencia o apoptosis.
- **Horizonte de Falsación:** 14 a 30 días (In-Vitro).
- **Condición (Falla):** Cultivos 3D (Organoides) derivados de pacientes al ser expuestos a inhibidores específicos de $D_1$ y $D_2$ deben mostrar una reducción de la viabilidad metabólica (ensayo ATP/CellTiter-Glo) $> 40\%$ respecto al control en 72 horas. Si la viabilidad persiste o las células entran en quiescencia reversible, el modelo Booleano carece de rigidez isomórfica con la biología celular y queda **REFUTADO**.

## 3. PROTOCOLO DE CIENCIA COMPILABLE
1. **Ingestión Causal:** Parseo estricto de matrices `.tsv` (TCGA RNA-Seq).
2. **Cristalización de Red:** WGCNA Pearson thresholding (Cálculo Físico).
3. **Mapeo:** Extracción de Atractor Booleano.
4. **Falsación Continua:** El algoritmo aborta automáticamente (`assert`) si los Driver Nodes aislados no cruzan el umbral estadístico (p-value < 0.05) en las firmas LINCS L1000 previas. No se propone un fármaco que no haya alterado el estado transcripcional en mediciones anteriores.

---
*Fin del manifiesto de falsabilidad empírica.*
