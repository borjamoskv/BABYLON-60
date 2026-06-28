use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_0 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N4;
N6 -> N1;
N7 -> N4;
N8 -> N3;
N9 -> N2;
N10 -> N0;
N11 -> N7;
N12 -> N0;
N13 -> N1;
N14 -> N2;
    }
}

fn main() {}
