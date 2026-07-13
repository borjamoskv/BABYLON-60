# Proof-of-Route (PoR): Contextual Router with Counterfactual Evaluation and Verifiable SLAs

## The Axiom
> El activo central no es la blockchain, sino una **capa de decisión auditable** que responde: ¿Qué decidió el router? ¿Por qué lo decidió? ¿Qué evidencia posterior indica que fue una buena decisión?

---

## I. Uncertainty-Aware Utility Equation (LCB/UCB)
El router no asume certezas absolutas, opera bajo estimaciones calibradas. La decisión se rige por:

$$ m^* = \arg\max_{m \in \mathcal{M}} \left[ LCB(Q_m) - \lambda UCB(L_m) - \mu UCB(C_m) - \rho P_{fail}(m) - \eta R_{priv} - \kappa R_{comp} \right] $$

- **LCB (Lower Confidence Bound)** para la Calidad ($Q$): Castiga la incertidumbre y evita modelos inestables.
- **UCB (Upper Confidence Bound)** para Latencia ($L$) y Coste ($C$): Penaliza el riesgo de picos inesperados.
- **$P_{fail}$**: Probabilidad de fallo o fallback.
- **$R_{priv}, R_{comp}$**: Restricciones booleanas duras (Privacidad, Residencia de datos).

---

## II. Counterfactual Evaluation & Shadow Routing
El "regret" no surge mágicamente. Se requieren mecanismos rigurosos:

1. **Selection Propensity ($\pi(m|x)$)**: 
   Registramos la probabilidad de haber elegido cada modelo. Esto habilita evaluación *off-policy* (IPS / Doubly Robust) sin necesidad de hacer shadow routing masivo.
2. **Adaptive Shadow Routing**: 
   Muestreo controlado. Prohibido en peticiones con PII/Secretos. Escalado dinámicamente según la caída de confianza ($LCB \downarrow$) o detección de drift.
3. **Real Outcome Signals**: 
   El SLA real no es el "Elo", es la probabilidad de éxito de la tarea: $P(\text{Task Success}|x) \ge \tau$. Ej: Tests pasados en código, CSAT en soporte, Extracción vs Ground Truth.

---

## III. Cryptographic Evidence Hierarchy
Para defender los prompts de baja entropía ante ataques de diccionario, el compromiso abandona el hash simple por un HMAC con clave de tenencia:

$$ H_{prompt} = \text{HMAC}_{K}(\text{canonical\_prompt}) $$

### Evidence Levels (0 to 5)
| Nivel | Evidencia | Prueba Matemática / Física |
|---|---|---|
| **0** | Internal Log | El sistema afirma una métrica local. |
| **1** | Router Signed Event | El Router asume criptográficamente su declaración. |
| **2** | Merkle Root Anchored | Inmutabilidad y orden temporal (Blockchain). |
| **3** | Provider Signed Receipt | El proveedor de Inferencia atestigua uso/modelo. |
| **4** | TEE/Hardware Attestation | Verificación física de la caja de ejecución (Enclave). |
| **5** | Verifiable Outcome | Señal de éxito real y auditable (Tests, Revisor). |

---

## IV. MVP Phasing Matrix
- **Fase 1 (Event Ledger):** Gateway LiteLLM + HMAC + Firmas Ed25519. (Nivel 1)
- **Fase 2 (Uncertainty Router):** $LCB/UCB$ math + Selection Propensity $\pi$.
- **Fase 3 (Safe Shadow):** Evaluadores por dominio + Regret tracking.
- **Fase 4 (Proof-of-Route):** Merkle Anchoring horario/diario. (Nivel 2)
- **Fase 5 (Utility SLA):** Venta de $P(\text{success})$ condicionado a constraints (TTFT, Cost, Compliance).
