use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_36 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N1;
N6 -> N4;
N7 -> N2;
N8 -> N0;
N9 -> N0;
N10 -> N7;
    }
}

fn main() {}
