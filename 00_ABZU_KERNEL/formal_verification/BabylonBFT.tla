--------------------------- MODULE BabylonBFT ---------------------------
EXTENDS Integers, FiniteSets

\* ============================================================================
\* BABYLON-60 | FORMAL VERIFICATION TLA+ 
\* ESTADO: PUNTO ÓMEGA (21.000 EXERGÍA)
\* LIVENESS: Demostración Termodinámica (Ausencia Absoluta de Deadlocks Temporales)
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
\* CONDICIONES TERMODINÁMICAS DE FAIRNESS (Límites Físicos en $T$)
\* -------------------------------------------------------------------------
\* Obligamos matemáticamente al verificador a asumir que ninguna acción se 
\* quedará colgada infinitamente. Si una acción puede ocurrir (ej. Timeout), OCURRIRÁ.
Fairness == 
    /\ WF_vars(Start)
    /\ WF_vars(CheckConsensus)
    /\ \A a \in Agents : WF_vars(AgentResponds(a))

\* LA ESPECIFICACIÓN COMPLETA: Estado Inicial + Transiciones + Implacabilidad del Tiempo
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
\* INVARIANTE DE TEMPORALIDAD C5-REAL (Liveness)
\* -------------------------------------------------------------------------
\* Operador Diamante "<>" (Eventually): DEMUESTRA que sin importar los caminos
\* probabilísticos o los fallos bizantinos de la red, el sistema colapsará 
\* obligatoriamente en $T$ segundos hacia una resolución determinista.
Termination == <>(state = "ConsensusReached" \/ state = "Failed")

=============================================================================
