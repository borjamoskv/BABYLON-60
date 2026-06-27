use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_30 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N3;
N5 -> N1;
N6 -> N4;
N7 -> N6;
N8 -> N7;
    }
}

fn main() {}
