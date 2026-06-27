use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_45 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N2;
N6 -> N2;
N7 -> N5;
N8 -> N1;
N9 -> N0;
N10 -> N6;
N11 -> N10;
N12 -> N9;
N13 -> N7;
N14 -> N5;
N15 -> N7;
N16 -> N12;
N17 -> N9;
    }
}

fn main() {}
