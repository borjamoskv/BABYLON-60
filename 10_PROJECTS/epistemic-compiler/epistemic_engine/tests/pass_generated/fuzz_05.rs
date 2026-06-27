use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_5 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N3;
N5 -> N0;
N6 -> N0;
N7 -> N3;
N8 -> N5;
N9 -> N6;
N10 -> N5;
N11 -> N8;
N12 -> N10;
N13 -> N3;
N14 -> N6;
N15 -> N12;
N16 -> N4;
    }
}

fn main() {}
