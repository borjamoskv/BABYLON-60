use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_27 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N3;
N5 -> N4;
N6 -> N2;
N7 -> N2;
N8 -> N4;
N9 -> N2;
N10 -> N8;
N11 -> N3;
N12 -> N6;
N13 -> N12;
N14 -> N2;
N15 -> N5;
N16 -> N8;
N17 -> N12;
N18 -> N8;
N19 -> N3;
    }
}

fn main() {}
