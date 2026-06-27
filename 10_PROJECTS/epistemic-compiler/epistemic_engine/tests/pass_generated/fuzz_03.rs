use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_3 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N0;
N6 -> N3;
N7 -> N6;
N8 -> N2;
N9 -> N4;
N10 -> N7;
N11 -> N10;
N12 -> N2;
N13 -> N11;
N14 -> N9;
N15 -> N12;
N16 -> N12;
    }
}

fn main() {}
