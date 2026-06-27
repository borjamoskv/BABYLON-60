use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_1 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N0;
N6 -> N4;
N7 -> N2;
N8 -> N3;
    }
}

fn main() {}
