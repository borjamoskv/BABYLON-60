use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_48 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N1;
N6 -> N3;
N7 -> N3;
N8 -> N4;
N9 -> N2;
N10 -> N0;
N11 -> N2;
N12 -> N1;
    }
}

fn main() {}
