use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_41 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N2;
N6 -> N1;
N7 -> N3;
    }
}

fn main() {}
