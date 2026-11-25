--------------------------- MODULE BabylonBFT ---------------------------
EXTENDS Integers, FiniteSets

\* ============================================================================
\* BABYLON-60 | FORMAL VERIFICATION TLA+ 
\* ALCANCE: modelo abstracto de un orquestador y un quórum
\* LIVENESS: terminación eventual bajo weak fairness; sin cota física
\* ============================================================================

CONSTANTS Agents, Quorum

VARIABLES state, responded, agreeing

vars == <<state, responded, agreeing>>

\* Estado inicial del nodo orquestador.
Init == 
    /\ state = "Init"
    /\ responded = {}
    /\ agreeing = {}

\* Transición: Start
Start ==
    /\ state = "Init"
    /\ state' = "Generating"
    /\ UNCHANGED <<responded, agreeing>>

\* Transición: Agentes respondiendo (incluyendo timeouts y fallos)
AgentResponds(a) ==
    /\ state = "Generating"
    /\ a \notin responded
    /\ responded' = responded \union {a}
    /\ \/ agreeing' = agreeing \union {a}
       \/ UNCHANGED agreeing
    /\ UNCHANGED state

\* Transición: Colapso BFT
CheckConsensus ==
    /\ state = "Generating"
    /\ \/ Cardinality(agreeing) >= Quorum  
       \/ Cardinality(responded) = Cardinality(Agents) 
    /\ state' = IF Cardinality(agreeing) >= Quorum THEN "ConsensusReached" ELSE "Failed"
    /\ UNCHANGED <<responded, agreeing>>

\* Función de Transición Global
Next == Start \/ (\E a \in Agents : AgentResponds(a)) \/ CheckConsensus

\* -------------------------------------------------------------------------
\* HIPÓTESIS DE WEAK FAIRNESS (sin límites físicos)
\* -------------------------------------------------------------------------
\* Weak fairness exige que una acción continuamente habilitada no se posponga
\* para siempre; no establece un plazo ni modela fallos de red.
Fairness == 
    /\ WF_vars(Start)
    /\ WF_vars(CheckConsensus)
    /\ \A a \in Agents : WF_vars(AgentResponds(a))

\* ESPECIFICACIÓN: estado inicial, transiciones y fairness
Spec == Init /\ [][Next]_vars /\ Fairness

\* -------------------------------------------------------------------------
\* INVARIANTES DE SEGURIDAD (Safety)
\* -------------------------------------------------------------------------
TypeOK == 
    /\ state \in {"Init", "Generating", "ConsensusReached", "Failed"}
    /\ responded \subseteq Agents
    /\ agreeing \subseteq Agents
    /\ agreeing \subseteq responded

StrictConsensus == 
    (state = "ConsensusReached") => (Cardinality(agreeing) >= Quorum)

\* -------------------------------------------------------------------------
\* PROPIEDAD TEMPORAL (Liveness)
\* -------------------------------------------------------------------------
\* Eventually: el modelo pide alcanzar ConsensusReached o Failed bajo Spec.
\* No modela consenso entre réplicas, autenticación, mensajes, ni tiempo real.
Termination == <>(state = "ConsensusReached" \/ state = "Failed")

=============================================================================
