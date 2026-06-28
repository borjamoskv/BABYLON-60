use epistemic_engine::epistemic;

epistemic! {
    graph fail_fuzz_38 {
        N0 -> N1;
N1 -> N2;
N2 -> N3;
N3 -> N4;
N4 -> N5;
N5 -> N6;
N6 -> N7;
N7 -> N8;
N8 -> N9;
N9 -> N10;
N10 -> N11;
N11 -> N12;
N12 -> N13;
N13 -> N14;
N14 -> N15;
N15 -> N16;
N16 -> N17;
N17 -> N18;
N18 -> N19;
N19 -> N0;
    }
}

fn main() {}
