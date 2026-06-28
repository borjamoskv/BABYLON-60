use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_19 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N4;
    }
}

fn main() {}
