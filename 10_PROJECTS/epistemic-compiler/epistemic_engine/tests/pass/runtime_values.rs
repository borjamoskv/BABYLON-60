use epistemic_engine::{epistemic, Inference, Transition, EpistemicNew};

epistemic! {
    graph values {
        Source -> Step1;
        Step1 -> Step2;
        Step2 -> Target;
    }
}

fn main() {
    let source = Inference::<states::Source>::new("EPISTEMIC_001".to_string(), 0.95);
    
    // In current implementation, apply() preserves value and confidence
    let step1: Inference<states::Step1> = source.apply();
    assert_eq!(step1.value, "EPISTEMIC_001");
    assert_eq!(step1.confidence, 0.95);

    let target: Inference<states::Target> = step1.apply().apply();
    assert_eq!(target.value, "EPISTEMIC_001");
    assert_eq!(target.confidence, 0.95);
}
