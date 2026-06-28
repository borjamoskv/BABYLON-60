use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_14 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N3;
N6 -> N1;
N7 -> N0;
N8 -> N6;
N9 -> N7;
N10 -> N3;
N11 -> N6;
    }
}

fn main() {}
