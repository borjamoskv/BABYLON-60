use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph multi_incoming {
        SourceA -> TargetC;
        SourceB -> TargetC;
    }
}

fn main() {
    let a = Inference::<states::SourceA>::new("A".to_string(), 1.0);
    let b = Inference::<states::SourceB>::new("B".to_string(), 0.9);

    let _c1: Inference<states::TargetC> = a.apply();
    let _c2: Inference<states::TargetC> = b.apply();
}
