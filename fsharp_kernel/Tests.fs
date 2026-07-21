namespace FSharpKernel.Tests

open FSharpKernel

module OntologyTests =
    
    let assertEqual expected actual msg =
        if expected <> actual then
            failwithf "Test Failure: %s (Expected: %A, Got: %A)" msg expected actual

    let testObserverParsing () =
        // Test valid observer parse
        match Parser.parseObserver 0 1 2 with
        | Choice1Of2 obs -> 
            assertEqual ObserverDomain.SOURCE obs.Domain "Domain match"
            assertEqual ObserverPrimitive.PREDICT obs.Primitive "Primitive match"
            assertEqual ObserverModifier.KALMAN_EXTENDED obs.Modifier "Modifier match"
        | Choice2Of2 err -> failwithf "Unexpected error: %A" err

        // Test invalid range
        match Parser.parseObserver 10 0 0 with
        | Choice2Of2 (InvalidDomain 10) -> ()
        | res -> failwithf "Expected InvalidDomain 10, got %A" res

        // Test Byzantine combination rule (m=6 QUANTIZED on d=0 SOURCE)
        match Parser.parseObserver 0 0 6 with
        | Choice2Of2 (ByzantineCombination msg) -> 
            if not (msg.Contains("Cannot apply QUANTIZED")) then
                failwithf "Unexpected Byzantine message: %s" msg
        | res -> failwithf "Expected ByzantineCombination error, got %A" res

    let testNeuroParsing () =
        // Test valid neuro parse
        match Parser.parseNeuro 5 4 2 with
        | Choice1Of2 neuro ->
            assertEqual NeuroDomain.BAYESIAN_FREE_ENERGY neuro.Domain "Domain match"
            assertEqual NeuroPrimitive.ATTENTION_FOCUS neuro.Primitive "Primitive match"
            assertEqual NeuroModifier.ACTIVE_INFERENCE neuro.Modifier "Modifier match"
        | Choice2Of2 err -> failwithf "Unexpected error: %A" err

        // Test Lyapunov stability restriction
        match Parser.parseNeuro 0 0 3 with
        | Choice2Of2 (ByzantineCombination _) -> ()
        | res -> failwithf "Expected ByzantineCombination for Lyapunov homeostasis, got %A" res

    let testTtsParsing () =
        // Test valid TTS parse
        match Parser.parseTts 1 2 3 with
        | Choice1Of2 tts ->
            assertEqual TtsDomain.LATENT_LOOKAHEAD tts.Domain "Domain match"
            assertEqual TtsPrimitive.EVALUATE tts.Primitive "Primitive match"
            assertEqual TtsModifier.RETRO_ATTENTION tts.Modifier "Modifier match"
        | Choice2Of2 err -> failwithf "Unexpected error: %A" err

        // Test Sandbox RAW execution security breach rule
        match Parser.parseTts 0 7 0 with
        | Choice2Of2 (ByzantineCombination _) -> ()
        | res -> failwithf "Expected Security breach error for raw sandbox execution, got %A" res

    let runAll () =
        printfn "[F# C5-REAL] Running FSharpKernel Ontology Tests..."
        testObserverParsing ()
        testNeuroParsing ()
        testTtsParsing ()
        printfn "[F# C5-REAL] All F# Ontology Invariants Verified (100%% PASSED)."
