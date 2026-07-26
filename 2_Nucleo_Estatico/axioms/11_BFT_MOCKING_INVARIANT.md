<!-- C5-REAL EXERGY CERTIFIED -->
# AXIOMA 11: BFT MOCKING INVARIANT (ANTI-SLOTS-MONKEY-PATCHING)

**Invariante Asignada:** Ω170

## 1. Postulado Termodinámico
La manipulación en tiempo de ejecución (Monkey-Patching) de métodos encapsulados en clases optimizadas con `__slots__` sobre la *instancia* provoca colapso inmediato (`AttributeError: read-only`). Aunque el parcheo global sobre la *clase* es sintácticamente posible, destruye el aislamiento epistémico (afectando a todos los nodos de la topología) e introduce entropía de estado cruzado. En arquitecturas C5-REAL, la simulación exige el reemplazo topológico íntegro de la instancia (Sustitución Estructural), garantizando el determinismo del árbol de referencias por nodo.

## 2. Formulación Algebraica
Sea un orquestador $O$ dependiente de un coordinador BFT $C$ de clase $\mathcal{S}$ (acotada por `__slots__`). El acoplamiento es $O(c)$ donde $c \in \mathcal{S}$.

La operación de simulación mediante parcheo local $P_{\text{local}}$ sobre la instancia $c$:
$$P_{\text{local}}(c.m) \to \bot \quad (\text{AttributeError})$$

El parcheo global $P_{\text{global}}$ sobre la clase $\mathcal{S}$:
$$P_{\text{global}}(\mathcal{S}.m) \implies \forall x \in \mathcal{S}, x.m \text{ es mutado} \quad (\text{Contaminación Epistémica} > 0)$$

La Sustitución Topológica Completa inyecta un isomorfismo $c'$ donde $c' \notin \mathcal{S}$:
$$O(c') \iff \text{Aislamiento } \Delta S = 0$$

## 3. Directiva de Transducción
Queda terminantemente prohibido usar `unittest.mock.patch` sobre clases con `__slots__` (por contaminación global) o instancias (por colapso `AttributeError`). Toda simulación (L4/L5) DEBE sobrescribir el puntero en el orquestador padre inyectando una clase Mock soberana completa.
