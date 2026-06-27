use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_42 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N0;
N5 -> N3;
N6 -> N1;
N7 -> N0;
N8 -> N6;
N9 -> N6;
N10 -> N2;
N11 -> N2;
N12 -> N1;
N13 -> N10;
N14 -> N11;
N15 -> N7;
N16 -> N3;
N17 -> N12;
    }
}

fn main() {}
