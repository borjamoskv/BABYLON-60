use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_19 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N2;
N6 -> N5;
    }
}

fn main() {}
