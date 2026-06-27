use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_25 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N2;
N7 -> N2;
N8 -> N6;
N9 -> N0;
N10 -> N3;
N11 -> N5;
    }
}

fn main() {}
