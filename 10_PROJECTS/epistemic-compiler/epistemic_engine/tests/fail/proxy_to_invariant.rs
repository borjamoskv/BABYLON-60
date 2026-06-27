use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph causal_chain {
        Proxy -> Observable;
        Latent -> Invariant;
    }
}

fn main() {
    let proxy = Inference::<states::Proxy>::new("LOC".to_string(), 0.5);
    // ERROR: Transition no está implementado para Inference<states::Proxy> -> states::Invariant
    let _invariant: Inference<states::Invariant> = proxy.apply();
}
