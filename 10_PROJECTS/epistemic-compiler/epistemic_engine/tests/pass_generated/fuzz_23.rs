use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_23 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N1;
N7 -> N1;
N8 -> N2;
N9 -> N3;
N10 -> N4;
N11 -> N9;
N12 -> N10;
N13 -> N4;
N14 -> N12;
    }
}

fn main() {}
