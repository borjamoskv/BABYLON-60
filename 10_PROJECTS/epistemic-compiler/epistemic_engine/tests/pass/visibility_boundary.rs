use epistemic_engine::{epistemic, Inference, Transition, EpistemicNew};

mod cortex_persist {
    pub mod graph_layer {
        use epistemic_engine::epistemic;
        
        epistemic! {
            graph deep_namespace {
                CortexInit -> Validation;
                Validation -> DbCommit;
            }
        }
    }
}

fn main() {
    let _init = Inference::<cortex_persist::graph_layer::states::CortexInit>::new(
        "Cortex v4".to_string(), 
        1.0
    );
}
