use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_4 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N3;
N5 -> N0;
N6 -> N0;
N7 -> N1;
N8 -> N6;
N9 -> N7;
N10 -> N8;
N11 -> N8;
N12 -> N8;
N13 -> N4;
N14 -> N4;
N15 -> N9;
    }
}

fn main() {}
