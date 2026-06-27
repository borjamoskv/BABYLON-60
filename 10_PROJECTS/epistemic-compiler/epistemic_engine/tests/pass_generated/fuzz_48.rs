use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_48 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N0;
N5 -> N2;
N6 -> N0;
N7 -> N5;
N8 -> N3;
N9 -> N3;
N10 -> N7;
N11 -> N0;
N12 -> N8;
N13 -> N8;
N14 -> N13;
N15 -> N10;
N16 -> N1;
    }
}

fn main() {}
