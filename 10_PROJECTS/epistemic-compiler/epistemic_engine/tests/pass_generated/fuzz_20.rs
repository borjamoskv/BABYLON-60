use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_20 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N1;
N5 -> N2;
N6 -> N5;
N7 -> N6;
N8 -> N2;
N9 -> N2;
    }
}

fn main() {}
