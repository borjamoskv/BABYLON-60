# Proof-of-Route: Utility SLA Specification (Artefacto 4)

## 1. Ontología del SLA (Nivel de Servicio)
El SLA no se define por el "uptime del router", sino por la **calidad contrafactual de sus decisiones** ($Regret_{proxy}$). Un enrutador multi-LLM cumple su SLA si y solo si, la utilidad de las rutas primarias elegidas no es estadísticamente inferior a las alternativas descubiertas mediante shadow routing.

## 2. Definición Formal de Utilidad ($U$)

La utilidad observada de una ejecución $e$ se define como una función lineal restrictiva de penalizaciones, acotada al dominio $[0, 10000]$ Basis Points.

\[
U(e) = \lambda_Q Q(e) + \lambda_L L(e) + \lambda_C C(e) - \mathbb{I}_{fail} P_{fail} - \mathbb{I}_{privacy} P_{privacy}
\]

**Invariante de Pesos:** $\lambda_Q + \lambda_L + \lambda_C = 1.0$

Donde:
*   $Q(e) \in [0, 10000]$: Calidad observada por el juez (Basis Points).
*   $L(e) = \max\left(0, 10000 \cdot \max\left(0, 1 - \frac{\text{ttft\_ms}}{\text{max\_ttft\_ms}}\right)\right)$: Transformación lineal de latencia, acotada superiormente por `max_ttft_ms` (ej. 10000 ms).
*   $C(e) = \max\left(0, 10000 \cdot \max\left(0, 1 - \frac{\log(1 + \text{cost\_microusd})}{\log(1 + \text{max\_cost\_microusd})}\right)\right)$: Transformación logarítmica de coste, para penalizar incrementos exponenciales de precio (ej. `max_cost` = 1000000 µUSD).
*   $\mathbb{I}_{fail}$: Función indicatriz de fallo de inferencia o circuito roto.
*   $P_{fail} = 5000$: Penalización fija por fallo.
*   $P_{privacy} = 20000$: Penalización letal por fuga de datos a shadow model prohibido. Toda fuga garantiza $U < 0$.

## 3. Thresholds de Cumplimiento (Regret Aceptable)

El **Observed Proxy Regret** ($R_{proxy}$) para una petición $i$ evaluando un shadow model $m \in S_i$ se define estrictamente garantizando $R \ge 0$:
\[
R(m, i) = \max\Big(0, U(m, x_i) - U(\text{primary}_i, x_i)\Big)
\]

El SLA se audita mensualmente sobre el Regret Ponderado por Propensión (Inverse Propensity Score, IPS) **a nivel de cada evaluación shadow**, no por request global:
\[
\widehat{R}_{IPS} = \frac{\sum_{i=1}^{N} \sum_{m \in S_i} \frac{1}{\pi(m|x_i)} R(m, i)}{\sum_{i=1}^{N} \sum_{m \in S_i} \frac{1}{\pi(m|x_i)}}
\]

### Límites por Categoría
| Categoría | Varianza | Tolerancia de Regret $P_{95}$ | Regret Medio Aceptable |
| :--- | :--- | :--- | :--- |
| **Coding** | Alta | $\le 1500$ Basis Points | $\le 400$ Basis Points |
| **Math** | Baja (Determinista) | $\le 500$ Basis Points | $\le 100$ Basis Points |
| **Creative** | Extrema | $\le 2500$ Basis Points | $\le 800$ Basis Points |

## 4. Condiciones de Incumplimiento y Remedios

El SLA se considera **roto** y detonará créditos de remediación si en una ventana de evaluación (ej. 1M de requests):
1. **Regret Sistémico:** El $\widehat{R}_{IPS}$ medio supera el límite aceptable para cualquier categoría.
2. **Latencia Falsa:** Más del 1% de los receipts muestran divergencia entre el TTFT estimado (T0) y el observado (T1) mayor a $1500$ ms.
3. **Violación de Privacidad:** Cualquier $P_{privacy}$ registrado en un Shadow Router. Invalida instantáneamente el contrato de enrutamiento.

## 5. Esquema de Reporting Criptográfico

El Auditor extraerá un muestreo aleatorio de la raíz Merkle (T3) y solicitará los receipts (T0-T1-T2) correspondientes.
El Router debe proveer:
1. `DecisionReceipt` firmado demostrando la elección en T0 (y las propensiones $\pi(m|x_i)$ declaradas pre-ejecución).
2. `ExecutionReceipt` de la ruta primaria y de los shadows $S_i$.
3. `EvaluationReceipt` de la evaluación contrafactual bajo los mismos jueces.
*Toda evidencia con firma inválida o timestamp invertido cuenta automáticamente como $U(primary)=0$ y $Regret=10000$.*
