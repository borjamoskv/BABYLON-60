use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_42 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N5;
N7 -> N6;
N8 -> N3;
N9 -> N5;
N10 -> N5;
N11 -> N4;
N12 -> N5;
N13 -> N7;
N14 -> N11;
    }
}

fn main() {}
