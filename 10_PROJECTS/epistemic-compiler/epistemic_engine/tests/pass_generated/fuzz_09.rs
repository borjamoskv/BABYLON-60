use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_9 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N3;
N5 -> N0;
N6 -> N4;
N7 -> N4;
N8 -> N4;
    }
}

fn main() {}
