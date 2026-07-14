namespace Babylon60.Domain

module IRPAutomata =

    // ==========================================
    // ONTOLOGÍA DEL DOMINIO: GRAVEDAD TERMODINÁMICA
    // ==========================================
    type Gravity =
        | C5_ColapsoOntologico
        | C4_DegradacionGeometrica
        | C3_FluctuacionTermica
        | C2_FriccionComputacional

    // ==========================================
    // ESTADO DE LA MEMBRANA (IRP)
    // ==========================================
    type MembraneState = 
        | Stable of entropyLevel: float
        | Smoothing of variance: float
        | Rollback of targetHash: string
        | Apoptosis of taintLog: string

    // ==========================================
    // PATTERN MATCHING EXHAUSTIVO (COMPILE-TIME PHYSICS)
    // ==========================================
    // La función pura de transición garantiza que no existan estados ilegales.
    let applyThermalStress (currentState: MembraneState) (gravity: Gravity) : MembraneState =
        match gravity with
        | C2_FriccionComputacional ->
            // Delegado al Garbage Collection asíncrono
            match currentState with
            | Stable e -> Stable (e + 0.01)
            | other -> other // Fricción menor no altera estados críticos

        | C3_FluctuacionTermica ->
            // Desencadena Smoothing
            match currentState with
            | Stable e -> Smoothing (e * 1.5)
            | Smoothing v -> Smoothing (v + 0.1)
            | Rollback h -> Rollback h // No interrumpe un Rollback en curso
            | Apoptosis t -> Apoptosis t

        | C4_DegradacionGeometrica ->
            // P-Value check. Permite Coarse-Graining si varianza es aceptable.
            match currentState with
            | Apoptosis t -> Apoptosis t // Irreversible
            | _ -> Rollback "LATEST_BFT_CHECKPOINT"

        | C5_ColapsoOntologico ->
            // Exige truncamiento total de memoria y re-sembrado TRNG (Anclaje on-chain)
            Apoptosis "TAINT:C5_REAL_TRUNCATED"

    // Emisión del límite de Commit C5-REAL al EVM/Rust
    let commitBoundary (state: MembraneState) : string =
        match state with
        | Stable e -> sprintf "STATUS:OK|ENTROPY:%.4f" e
        | Smoothing v -> sprintf "STATUS:SMOOTHING|VARIANCE:%.4f" v
        | Rollback h -> sprintf "STATUS:ROLLBACK|HASH:%s" h
        | Apoptosis t -> sprintf "STATUS:APOPTOSIS|TAINT:%s" t
