use epistemic_engine::epistemic;

epistemic! {
    graph duplicate {
        RawEvidence -> Evidence;
        RawEvidence -> Evidence; // DUPLICATE EDGE!
    }
}

fn main() {}
