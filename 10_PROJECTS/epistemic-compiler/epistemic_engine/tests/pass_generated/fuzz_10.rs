use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_10 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N3;
N6 -> N1;
N7 -> N1;
N8 -> N0;
N9 -> N6;
N10 -> N7;
N11 -> N0;
N12 -> N10;
N13 -> N11;
N14 -> N12;
N15 -> N9;
N16 -> N2;
N17 -> N0;
N18 -> N11;
    }
}

fn main() {}
