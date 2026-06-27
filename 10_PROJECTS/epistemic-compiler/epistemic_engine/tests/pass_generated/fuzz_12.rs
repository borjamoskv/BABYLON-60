use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_12 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N3;
N5 -> N3;
N6 -> N3;
N7 -> N3;
N8 -> N1;
N9 -> N6;
    }
}

fn main() {}
