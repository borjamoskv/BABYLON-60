use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_35 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N1;
N5 -> N0;
N6 -> N4;
N7 -> N0;
N8 -> N7;
    }
}

fn main() {}
