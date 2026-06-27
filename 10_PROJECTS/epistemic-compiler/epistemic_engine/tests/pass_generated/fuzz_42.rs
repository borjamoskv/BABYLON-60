use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_42 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N1;
N6 -> N2;
N7 -> N5;
N8 -> N5;
N9 -> N5;
N10 -> N1;
N11 -> N3;
N12 -> N11;
N13 -> N0;
N14 -> N11;
N15 -> N11;
N16 -> N2;
N17 -> N11;
N18 -> N6;
    }
}

fn main() {}
