/-
  C5Real/MarkovWorld.lean — Semántica Externa para Sistemas Cognitivos
  
  BABYLON-60 / C5-REAL v2 (Post-Falsación Swarm)
  
  Este módulo introduce el objeto-mundo W y el canal de observación real
  que ancla la inferencia del agente a una verdad causal externa.
  
  Resuelve: V3 (sin semántica externa), V8 (independencia axioma/clase),
            CE1 (espionaje por unidad monoidal).
  
  Referencias:
  - Fritz (2020): arXiv:1908.07021, Def. 2.1 (Markov category)
  - Smithe (2020): arXiv:2006.01631 (Bayesian updates compose optically)
  - Cho–Jacobs (2019): arXiv:1709.00322 (disintegration, Bayesian inversion)
-/

import Mathlib.CategoryTheory.Category.Basic
import Mathlib.CategoryTheory.Monoidal.Category

namespace C5Real

universe u v

variable {C : Type u} [Category.{v} C] [MonoidalCategory C]

-- ═══════════════════════════════════════════════════════════════════
-- § 1. CognitiveSystem: Agente embebido en un entorno externo
-- ═══════════════════════════════════════════════════════════════════

/-- Un `CognitiveSystem` modela un agente que infiere sobre un mundo
    externo `W` a través de observaciones filtradas `obs : W ⟶ Obs`.

    El agente mantiene un estado interno `State` y un decodificador
    `decode : State ⟶ W` que proyecta su modelo interno al espacio
    del mundo. El agente NUNCA accede a `W` directamente.

    Esta estructura resuelve el defecto arquitectónico fundamental
    de C5-REAL v1: la ausencia de un referente externo hacía que
    "alucinación" no fuera ni definible en la signatura. -/
structure CognitiveSystem (C : Type u) [Category.{v} C] [MonoidalCategory C] where
  /-- Estado interno del agente (belief state) -/
  State : C
  /-- Espacio de observaciones accesibles al agente -/
  Obs : C
  /-- Mundo externo (ground truth) — opaco al agente -/
  World : C
  /-- Canal de observación real: cómo el mundo genera observaciones.
      Este es el proceso generativo verdadero, inaccesible al agente
      pero contra el cual se mide la calibración. -/
  obs : World ⟶ Obs
  /-- Decodificador: proyección del modelo interno al espacio-mundo.
      Representa la "creencia del agente sobre el mundo".
      decode(state) ∈ W es "lo que el agente cree que está pasando". -/
  decode : State ⟶ World

-- ═══════════════════════════════════════════════════════════════════
-- § 2. Propiedades derivadas de CognitiveSystem
-- ═══════════════════════════════════════════════════════════════════

/-- La predicción implícita del agente: lo que espera observar
    dado su estado interno. Este es el morfismo compuesto
    `decode ≫ obs`, que pasa por el mundo modelado. -/
def CognitiveSystem.implicitPredict (sys : CognitiveSystem C) :
    sys.State ⟶ sys.Obs :=
  sys.decode ≫ sys.obs

end C5Real
