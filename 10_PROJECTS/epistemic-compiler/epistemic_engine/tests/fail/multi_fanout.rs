use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph multi_fanout {
        RawEvidence -> Evidence;
        RawEvidence -> Logs;
        Evidence -> Observable;
        Logs -> Observable;
    }
}

fn main() {
    let raw = Inference::<states::RawEvidence>::new("Multi".to_string(), 1.0);
    
    // Branch 1
    let evidence: Inference<states::Evidence> = raw.clone().apply();
    let _obs1: Inference<states::Observable> = evidence.apply();

    // Branch 2
    let logs: Inference<states::Logs> = raw.apply();
    let _obs2: Inference<states::Observable> = logs.apply();
}
