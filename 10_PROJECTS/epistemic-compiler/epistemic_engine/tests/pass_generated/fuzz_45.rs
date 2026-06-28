use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_45 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N1;
N6 -> N1;
N7 -> N5;
N8 -> N4;
N9 -> N8;
N10 -> N5;
N11 -> N0;
N12 -> N4;
N13 -> N4;
N14 -> N10;
N15 -> N10;
N16 -> N8;
N17 -> N14;
N18 -> N8;
N19 -> N15;
    }
}

fn main() {}
