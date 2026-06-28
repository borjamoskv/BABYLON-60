use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_39 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N4;
N6 -> N2;
N7 -> N5;
N8 -> N5;
N9 -> N0;
N10 -> N2;
N11 -> N4;
N12 -> N3;
N13 -> N8;
N14 -> N0;
N15 -> N0;
    }
}

fn main() {}
