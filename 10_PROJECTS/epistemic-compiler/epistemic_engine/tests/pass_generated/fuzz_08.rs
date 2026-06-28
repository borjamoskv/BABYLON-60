use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_8 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N3;
N6 -> N5;
N7 -> N0;
N8 -> N2;
N9 -> N1;
    }
}

fn main() {}
