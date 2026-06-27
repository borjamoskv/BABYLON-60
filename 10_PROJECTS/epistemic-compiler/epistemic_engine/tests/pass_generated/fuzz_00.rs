use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_0 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N3;
N6 -> N0;
N7 -> N4;
N8 -> N2;
N9 -> N0;
N10 -> N4;
N11 -> N9;
N12 -> N5;
N13 -> N10;
N14 -> N13;
N15 -> N0;
N16 -> N11;
N17 -> N13;
N18 -> N6;
N19 -> N9;
    }
}

fn main() {}
