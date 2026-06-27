use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_47 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N3;
N6 -> N5;
N7 -> N5;
N8 -> N6;
N9 -> N2;
N10 -> N7;
N11 -> N2;
N12 -> N10;
N13 -> N9;
N14 -> N5;
N15 -> N12;
N16 -> N0;
N17 -> N1;
N18 -> N15;
    }
}

fn main() {}
