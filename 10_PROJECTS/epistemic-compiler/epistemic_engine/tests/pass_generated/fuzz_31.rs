use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_31 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N3;
N5 -> N3;
N6 -> N2;
N7 -> N4;
N8 -> N2;
N9 -> N3;
N10 -> N0;
N11 -> N0;
N12 -> N1;
    }
}

fn main() {}
