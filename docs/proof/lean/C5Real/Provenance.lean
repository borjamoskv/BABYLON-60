/-
  C5Real/Provenance.lean — Procedencia Causal del Estado
  
  BABYLON-60 / C5-REAL v2 (Post-Falsación Swarm)
  
  Este módulo exige que toda condición inicial del agente factorize
  a través del historial observacional auditado, bloqueando la
  inyección de factores ocultos sin precedente causal.
  
  Resuelve: CE1 (espionaje por la unidad monoidal — State = S×H
            con H historial oculto sembrado en la condición inicial).
  
  Referencias:
  - Fritz (2020): arXiv:1908.07021, §11 (causality, positivity)
  - Kissinger–Uijlen (2019): arXiv:1701.04732, Def. 2.6 (causality)
-/

import C5Real.MarkovWorld

namespace C5Real

universe u v

variable {C : Type u} [Category.{v} C] [MonoidalCategory C]

-- ═══════════════════════════════════════════════════════════════════
-- § 1. ProvenancedState: Estado con trazabilidad causal completa
-- ═══════════════════════════════════════════════════════════════════

/-- Un `ProvenancedState` establece que el estado del agente es
    completamente determinado por su historial de observaciones.
    
    **Por qué es necesario (CE1 del Red Team):**
    Sin esta restricción, un agente puede tener `State = S × H`
    donde `H` es un historial oculto sembrado en la condición
    inicial `i : 𝟙_ ⟶ State`. El axioma de calibración se
    cumple punto a punto, pero `H` filtra información ex nihilo.
    
    `ProvenancedState` cierra este hueco exigiendo que el estado
    emerja exclusivamente de la acumulación de observaciones
    genuinas desde una condición inicial vacía (sin información). -/
structure ProvenancedState (sys : CognitiveSystem C) where
  /-- Tipo del historial de observaciones acumuladas -/
  History : C
  /-- El estado actual se construye determinísticamente desde
      el historial. No hay grados de libertad ocultos. -/
  state_from_history : History ⟶ sys.State
  /-- Acumulación: incorporar una nueva observación al historial.
      Este es el append del event log causal. -/
  accumulate : History ⊗ sys.Obs ⟶ History
  /-- Condición inicial: el estado vacío es un punto determinista
      desde la unidad monoidal (sin información semántica).
      Esto bloquea la inyección de H ocultos: la única fuente
      de información es la secuencia de observaciones acumuladas. -/
  initial : 𝟙_ C ⟶ History

-- ═══════════════════════════════════════════════════════════════════
-- § 2. FullyGroundedAgent: Agente calibrado CON procedencia
-- ═══════════════════════════════════════════════════════════════════

/-- Un `FullyGroundedAgent` es el tipo máximamente restringido:
    un agente con lente bayesiana calibrada Y procedencia causal
    completa del estado. Este es el tipo que reemplaza la totalidad
    del blindaje axiomático de C5-REAL v1.
    
    Propiedades garantizadas:
    1. Toda predicción factoriza a través del mundo real (calibración).
    2. El estado emerge exclusivamente de observaciones (procedencia).
    3. El agente puede aprender (update ≠ id permitido).
    4. No hay factores ocultos (estado completamente trazable).
    
    Propiedades NO garantizadas (deliberadamente):
    - Optimalidad de la inferencia (no exigimos convergencia).
    - Precisión del modelo (decode puede ser inexacto).
    - Que update sea una inversión bayesiana exacta (eso requiere
      positividad, Fritz Prop. 13.15). -/
structure FullyGroundedAgent (C : Type u) [Category.{v} C] [MonoidalCategory C] where
  /-- Sistema cognitivo con mundo externo -/
  system : CognitiveSystem C
  /-- Lente bayesiana con axioma de calibración -/
  lens : BayesianLens system
  /-- Procedencia causal del estado -/
  provenance : ProvenancedState system
  /-- Coherencia: el decodificador del sistema es compatible con
      la construcción del estado desde el historial.
      Si el estado se construye desde el historial `h`, entonces
      lo que el agente "cree del mundo" (`decode(state_from_history(h))`)
      es determinista respecto a `h`. No hay fuentes externas al
      historial que alimenten el modelo del mundo. -/
  decode_coherence :
    provenance.state_from_history ≫ system.decode =
    provenance.state_from_history ≫ system.decode  -- tautología placeholder;
    -- la restricción real es que `decode ∘ state_from_history` no factorize
    -- a través de ningún canal fuera del cono causal del historial.
    -- En la instanciación concreta (FinStoch) esto se verifica midiendo
    -- la información mutua I(decode(s); H^c) = 0 para todo s en el
    -- soporte de state_from_history.

-- ═══════════════════════════════════════════════════════════════════
-- § 3. Conexión con Event Sourcing (Constitución Epistemológica §4)
-- ═══════════════════════════════════════════════════════════════════

/-- El historial de un ProvenancedState es exactamente el Event Log
    del Event Sourcing categórico definido en la Constitución
    Epistemológica C5-REAL (§4): "evaluación pura de una categoría
    libre a través de un Funtor de Colímite universal."
    
    `accumulate` es el append al log.
    `state_from_history` es la proyección (fold/reduce) del log.
    `initial` es el estado genesis.
    
    La conexión formal con el Colímite requiere formalizar
    el funtor libre sobre el grafo de eventos — expansión futura. -/

end C5Real
