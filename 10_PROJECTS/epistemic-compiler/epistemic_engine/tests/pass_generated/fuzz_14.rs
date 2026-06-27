use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_14 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N2;
N6 -> N0;
N7 -> N4;
N8 -> N7;
N9 -> N0;
N10 -> N9;
    }
}

fn main() {}
