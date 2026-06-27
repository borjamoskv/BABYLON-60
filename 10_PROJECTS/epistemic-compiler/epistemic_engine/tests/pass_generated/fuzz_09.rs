use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_9 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N0;
N6 -> N1;
N7 -> N5;
N8 -> N2;
N9 -> N2;
N10 -> N3;
N11 -> N4;
    }
}

fn main() {}
