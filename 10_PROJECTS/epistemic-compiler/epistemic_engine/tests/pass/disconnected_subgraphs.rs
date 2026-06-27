use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph disconnected {
        // Subgrafo A
        SourceA -> NodeA1;
        NodeA1 -> TargetA;

        // Subgrafo B
        SourceB -> NodeB1;
        NodeB1 -> TargetB;
    }
}

fn main() {
    let a = Inference::<states::SourceA>::new("A".to_string(), 1.0);
    let b = Inference::<states::SourceB>::new("B".to_string(), 0.9);

    let _a1: Inference<states::NodeA1> = a.apply();
    let _b1: Inference<states::NodeB1> = b.apply();
}
