use epistemic_engine::epistemic;

epistemic! {
    graph invalid_provenance {
        Latent Hypothesis -> Observable RealWorldEvent [0.8];
    }
}

fn main() {}
