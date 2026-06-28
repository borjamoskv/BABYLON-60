use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_6 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N1;
N6 -> N0;
N7 -> N3;
N8 -> N3;
N9 -> N2;
N10 -> N8;
N11 -> N2;
N12 -> N11;
N13 -> N1;
N14 -> N4;
    }
}

fn main() {}
