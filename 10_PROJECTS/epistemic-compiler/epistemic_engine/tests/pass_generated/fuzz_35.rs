use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_35 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N1;
N6 -> N3;
N7 -> N3;
N8 -> N4;
N9 -> N2;
N10 -> N3;
N11 -> N8;
N12 -> N6;
N13 -> N5;
N14 -> N7;
N15 -> N6;
    }
}

fn main() {}
