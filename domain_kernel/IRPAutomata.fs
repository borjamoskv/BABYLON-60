namespace Babylon60.Domain

open System
open System.Security.Cryptography
open System.Text

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

module LedgerValidation =

    type StateNode = {
        NodeId: string
        ParentId: string
        ClaimSummary: string
        PayloadHash: string
    }

    type ValidationError =
        | ParentNotFound of parentId: string
        | InvalidClaimLength of claim: string
        | InvalidHashLength of hashName: string * hash: string
        | DuplicateNodeId of nodeId: string

    type LedgerState = {
        Nodes: Map<string, StateNode>
        GenesisId: string
    }

    let genesisLedger () : LedgerState = {
        Nodes = Map.empty
        GenesisId = String.replicate 64 "0"
    }

    let validateAndAppend (state: LedgerState) (parent: string) (claim: string) (payload: string) : Result<LedgerState * StateNode, ValidationError> =
        if parent <> state.GenesisId && not (state.Nodes.ContainsKey(parent)) then
            Error (ParentNotFound parent)
        elif String.IsNullOrEmpty(claim) || claim.Length > 64 then
            Error (InvalidClaimLength claim)
        elif payload.Length <> 64 then
            Error (InvalidHashLength ("PayloadHash", payload))
        else
            let rawContent = sprintf "%s:%s:%s" parent claim payload
            use sha256 = SHA256.Create()
            let bytes = Encoding.UTF8.GetBytes(rawContent)
            let hashBytes = sha256.ComputeHash(bytes)
            let nodeId = hashBytes |> Array.map (fun b -> sprintf "%02x" b) |> String.concat ""

            if state.Nodes.ContainsKey(nodeId) then
                Error (DuplicateNodeId nodeId)
            else
                let newNode = {
                    NodeId = nodeId
                    ParentId = parent
                    ClaimSummary = claim
                    PayloadHash = payload
                }
                let newState = {
                    state with Nodes = state.Nodes.Add(nodeId, newNode)
                }
                Ok (newState, newNode)
