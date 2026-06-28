use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_49 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N4;
N6 -> N1;
N7 -> N6;
N8 -> N5;
    }
}

fn main() {}
