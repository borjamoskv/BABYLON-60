use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph causal_chain {
        RawEvidence -> Evidence;
        Evidence -> Observable;
        Observable -> Derived;
        Derived -> Latent;
    }
}

fn main() {
    let raw = Inference::<states::RawEvidence>::new("Commit".to_string(), 1.0);
    let evidence = raw.apply();
    let observable = evidence.apply();
    let derived = observable.apply();
    let _latent = derived.apply();
}
