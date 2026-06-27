use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_43 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N3;
N5 -> N3;
N6 -> N1;
N7 -> N1;
N8 -> N4;
N9 -> N1;
N10 -> N1;
N11 -> N3;
    }
}

fn main() {}
