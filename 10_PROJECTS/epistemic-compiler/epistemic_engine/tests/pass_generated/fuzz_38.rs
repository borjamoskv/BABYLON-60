use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_38 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N4;
N6 -> N2;
N7 -> N5;
N8 -> N2;
    }
}

fn main() {}
