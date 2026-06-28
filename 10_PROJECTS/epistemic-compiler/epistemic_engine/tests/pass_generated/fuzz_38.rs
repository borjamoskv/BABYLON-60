use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_38 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N4;
N6 -> N3;
N7 -> N1;
N8 -> N3;
N9 -> N4;
N10 -> N6;
N11 -> N7;
N12 -> N0;
N13 -> N4;
N14 -> N11;
N15 -> N8;
    }
}

fn main() {}
