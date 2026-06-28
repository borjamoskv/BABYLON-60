use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_9 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N0;
N6 -> N5;
N7 -> N1;
N8 -> N4;
N9 -> N1;
N10 -> N4;
N11 -> N3;
    }
}

fn main() {}
