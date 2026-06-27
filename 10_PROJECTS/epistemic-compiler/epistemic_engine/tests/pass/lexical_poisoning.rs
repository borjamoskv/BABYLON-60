use epistemic_engine::{epistemic, Inference, Transition, EpistemicNew};

epistemic! {
    graph lexical_poisoning {
        // Rust reserved keywords as raw identifiers
        r#fn -> r#struct;
        r#struct -> r#impl;
        
        // Shadowing internal macro struct names
        Inference -> Transition;
        Transition -> EpistemicNew;
        EpistemicNew -> PhantomData;
    }
}

fn main() {
    // Verify we can access the nodes via their actual identifiers
    let _a = Inference::<states::r#fn>::new("raw_ident".to_string(), 1.0);
    let _b = Inference::<states::Inference>::new("shadow_ident".to_string(), 1.0);
}
