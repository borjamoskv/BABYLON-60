use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_0 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N4;
N6 -> N3;
N7 -> N1;
N8 -> N4;
N9 -> N5;
N10 -> N5;
N11 -> N5;
N12 -> N2;
N13 -> N11;
N14 -> N11;
N15 -> N4;
N16 -> N5;
N17 -> N11;
N18 -> N12;
N19 -> N9;
    }
}

fn main() {}
