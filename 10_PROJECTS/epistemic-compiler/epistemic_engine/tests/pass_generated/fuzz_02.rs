use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_2 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N1;
N5 -> N1;
N6 -> N2;
N7 -> N3;
N8 -> N5;
N9 -> N3;
N10 -> N1;
N11 -> N1;
    }
}

fn main() {}
