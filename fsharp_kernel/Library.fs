namespace FSharpKernel

type ValidationError =
    | InvalidDomain of int
    | InvalidPrimitive of int
    | InvalidModifier of int
    | ByzantineCombination of string

// ==========================================
// 5. CATEGORICAL 896 PRIMITIVES MODULE
// ==========================================
module Categorical896 =
    type CategoricalDomain =
        | D1_Structure = 1
        | D2_LimitsColimits = 2
        | D3_FunctorsAdjunctions = 3
        | D4_MonoidalEnriched = 4
        | D5_CategoricalLogicTopos = 5
        | D6_CollisionObstruction = 6
        | D7_Antipatterns = 7
        | D8_FiberedMetrics = 8

    type MorphismCost =
        | Finite of float
        | Infinity

    let calculateMorphismCost (seq: int list) (friction: float) : MorphismCost =
        match seq with
        | [] -> Infinity
        | _ -> Finite (float seq.Length + friction)

    let detectCollisions (activeIds: int list) : (int * int) list =
        let d6 = activeIds |> List.filter (fun id -> id >= 561 && id <= 672)
        let d7 = activeIds |> List.filter (fun id -> id >= 673 && id <= 784)
        [ for c in d6 do for a in d7 -> (c, a) ]

// ==========================================
// 1. STATE OBSERVER ONTOLOGY
// ==========================================
type ObserverDomain =
    | SOURCE = 0
    | MATRIX = 1
    | PULSE = 2
    | KINETIC = 3
    | LOGIC = 4
    | VECTOR = 5
    | STORAGE = 6
    | OSINT = 7
    | CLOCK = 8
    | COMPILER = 9

type ObserverPrimitive =
    | INIT = 0
    | PREDICT = 1
    | UPDATE = 2
    | INNOVATION = 3
    | GAIN = 4
    | COVARIANCE = 5
    | DRIFT_CHECK = 6
    | RECONSTRUCT = 7
    | SANITY_ASSERT = 8
    | FLUSH_LEDGER = 9

type ObserverModifier =
    | RAW = 0
    | ATOMIC = 1
    | KALMAN_EXTENDED = 2
    | LUENBERGER_RIGID = 3
    | PARTICLE_PF = 4
    | SLIDING_MODE = 5
    | QUANTIZED = 6
    | ADAPTIVE_R = 7
    | NEURAL_LATENT = 8
    | BFT_CONSENSUS = 9

type ObserverIdentity = {
    Domain: ObserverDomain
    Primitive: ObserverPrimitive
    Modifier: ObserverModifier
}

// ==========================================
// 2. NEURO-COGNITIVE CHAIN ONTOLOGY
// ==========================================
type NeuroDomain =
    | ENERGY_BOUND = 0
    | ATTRACTOR_DECAY = 1
    | COGNITIVE_DRIFT = 2
    | RESOURCE_EXHAUST = 3
    | SYBIL_REVERB = 4
    | BAYESIAN_FREE_ENERGY = 5
    | LATENT_TORQUE = 6
    | SURPRISAL_GATE = 7
    | TEMPORAL_PHASE = 8
    | DEEP_MCTS_DEPTH = 9

type NeuroPrimitive =
    | HOMEOSTASIS_INIT = 0
    | HOMEOSTASIS_MUTATE = 1
    | PREDICTION_GENERATE = 2
    | PREDICTION_AUDIT = 3
    | ATTENTION_FOCUS = 4
    | ATTENTION_QUANTIZE = 5
    | ACTION_DISPATCH = 6
    | ACTION_ASSERT = 7
    | LANGUAGE_COLLAPSE = 8
    | LANGUAGE_FLUSH = 9

type NeuroModifier =
    | RAW = 0
    | ATOMIC = 1
    | ACTIVE_INFERENCE = 2
    | LYAPUNOV_STABLE = 3
    | SPARSE_KV = 4
    | BFT_CONSENSUS = 5
    | FEEDFORWARD = 6
    | BACKPROP_ERROR = 7
    | SLIDING_SURFACE = 8
    | EPIDEMIC_PURGE = 9

type NeuroIdentity = {
    Domain: NeuroDomain
    Primitive: NeuroPrimitive
    Modifier: NeuroModifier
}

// ==========================================
// 3. TEST-TIME SCALING & AGENTIC HARNESS ONTOLOGY
// ==========================================
type TtsDomain =
    | ENTROPY_ALLOC = 0
    | LATENT_LOOKAHEAD = 1
    | POLICY_IMPROVE = 2
    | HARNESS_DISCOVERY = 3
    | PROGRAMMATIC_JIT = 4
    | SWARM_GRAPH = 5
    | TRI_TIER_MEMORY = 6
    | INFO_KV_EVICTION = 7
    | STAGE_DECOUPLE = 8
    | VECTOR_QUANT = 9

type TtsPrimitive =
    | INIT = 0
    | EXPAND = 1
    | EVALUATE = 2
    | BACKPROP = 3
    | PRUNE = 4
    | QUANTIZE = 5
    | ASSERT_BFT = 6
    | EXECUTE_SANDBOX = 7
    | RECONSTRUCT_STATE = 8
    | FLUSH_LEDGER = 9

type TtsModifier =
    | RAW = 0
    | ATOMIC = 1
    | ADAPTIVE_COT = 2
    | RETRO_ATTENTION = 3
    | FORWARD_INFLUENCE = 4
    | TURBO_QUANT = 5
    | META_PROPOSER = 6
    | FEEDFORWARD_OPEN = 7
    | SLIDING_WINDOW = 8
    | EPIDEMIC_PURGE = 9

type TtsIdentity = {
    Domain: TtsDomain
    Primitive: TtsPrimitive
    Modifier: TtsModifier
}

// ==========================================
// ALGEBRAIC PARSERS (Choice<'T, ValidationError>)
// ==========================================
module Parser =

    let parseObserver (d: int) (p: int) (m: int) : Choice<ObserverIdentity, ValidationError> =
        if d < 0 || d > 9 then Choice2Of2 (InvalidDomain d)
        elif p < 0 || p > 9 then Choice2Of2 (InvalidPrimitive p)
        elif m < 0 || m > 9 then Choice2Of2 (InvalidModifier m)
        else
            // Semantic validation rules (Make Byzantine states unrepresentable)
            // Rule: QUANTIZED modifier is incompatible with direct RAW domains.
            if m = 6 && d = 0 then
                Choice2Of2 (ByzantineCombination "Cannot apply QUANTIZED observer to raw SOURCE domain")
            else
                let domain = System.Enum.ToObject(typeof<ObserverDomain>, d) :?> ObserverDomain
                let primitive = System.Enum.ToObject(typeof<ObserverPrimitive>, p) :?> ObserverPrimitive
                let modifier = System.Enum.ToObject(typeof<ObserverModifier>, m) :?> ObserverModifier
                Choice1Of2 { Domain = domain; Primitive = primitive; Modifier = modifier }

    let parseNeuro (d: int) (p: int) (m: int) : Choice<NeuroIdentity, ValidationError> =
        if d < 0 || d > 9 then Choice2Of2 (InvalidDomain d)
        elif p < 0 || p > 9 then Choice2Of2 (InvalidPrimitive p)
        elif m < 0 || m > 9 then Choice2Of2 (InvalidModifier m)
        else
            // Semantic validation rules
            // Rule: LYAPUNOV_STABLE modifier cannot be initialized/mutated with raw energy bound (domain 0 + primitive 0/1 + modifier 3)
            if m = 3 && d = 0 && (p = 0 || p = 1) then
                Choice2Of2 (ByzantineCombination "Lyapunov stability cannot be guaranteed during raw homeostasis perturbation")
            else
                let domain = System.Enum.ToObject(typeof<NeuroDomain>, d) :?> NeuroDomain
                let primitive = System.Enum.ToObject(typeof<NeuroPrimitive>, p) :?> NeuroPrimitive
                let modifier = System.Enum.ToObject(typeof<NeuroModifier>, m) :?> NeuroModifier
                Choice1Of2 { Domain = domain; Primitive = primitive; Modifier = modifier }

    let parseTts (d: int) (p: int) (m: int) : Choice<TtsIdentity, ValidationError> =
        if d < 0 || d > 9 then Choice2Of2 (InvalidDomain d)
        elif p < 0 || p > 9 then Choice2Of2 (InvalidPrimitive p)
        elif m < 0 || m > 9 then Choice2Of2 (InvalidModifier m)
        else
            // Semantic validation rules
            // Rule: EXECUTE_SANDBOX primitive (7) cannot be run under RAW modifier (0) due to security isolation breach
            if p = 7 && m = 0 then
                Choice2Of2 (ByzantineCombination "Security breach: raw execution is banned inside execution sandboxes")
            else
                let domain = System.Enum.ToObject(typeof<TtsDomain>, d) :?> TtsDomain
                let primitive = System.Enum.ToObject(typeof<TtsPrimitive>, p) :?> TtsPrimitive
                let modifier = System.Enum.ToObject(typeof<TtsModifier>, m) :?> TtsModifier
                Choice1Of2 { Domain = domain; Primitive = primitive; Modifier = modifier }
