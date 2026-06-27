use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_13 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N1;
N5 -> N2;
N6 -> N2;
N7 -> N3;
N8 -> N7;
    }
}

fn main() {}
