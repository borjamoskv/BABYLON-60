use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_41 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
    }
}

fn main() {}
