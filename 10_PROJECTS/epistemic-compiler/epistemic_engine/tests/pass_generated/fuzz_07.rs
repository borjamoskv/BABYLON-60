use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_7 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N2;
N6 -> N4;
N7 -> N4;
N8 -> N5;
N9 -> N4;
N10 -> N5;
N11 -> N5;
N12 -> N1;
N13 -> N4;
N14 -> N7;
    }
}

fn main() {}
