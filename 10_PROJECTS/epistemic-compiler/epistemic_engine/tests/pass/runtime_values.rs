use epistemic_engine::{epistemic, Inference, Transition, EpistemicNew};

epistemic! {
    graph values {
        Source -> Step1 [0.9];
        Step1 -> Step2 [0.8];
        Step2 -> Target [1.0];
    }
}

fn main() {
    let source = Inference::<states::Source>::new("EPISTEMIC_001".to_string(), 1.0);
    
    // Confidence drops by 0.9
    let step1: Inference<states::Step1> = source.apply();
    assert_eq!(step1.value, "EPISTEMIC_001");
    assert_eq!(step1.confidence, 0.9);

    // Confidence drops by 0.8
    let target: Inference<states::Target> = step1.apply().apply();
    assert_eq!(target.value, "EPISTEMIC_001");
    // 0.9 * 0.8 = 0.72 (with floating point epsilon tolerance)
    assert!((target.confidence - 0.72).abs() < f64::EPSILON);
}
