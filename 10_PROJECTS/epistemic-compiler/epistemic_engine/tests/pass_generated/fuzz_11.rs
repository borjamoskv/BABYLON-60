use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_11 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N3;
N5 -> N3;
N6 -> N5;
N7 -> N6;
N8 -> N5;
N9 -> N2;
N10 -> N6;
N11 -> N7;
    }
}

fn main() {}
