use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_39 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N3;
N6 -> N2;
N7 -> N1;
N8 -> N3;
N9 -> N3;
    }
}

fn main() {}
