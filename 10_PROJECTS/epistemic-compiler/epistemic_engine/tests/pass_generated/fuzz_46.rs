use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_46 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N1;
N5 -> N4;
N6 -> N2;
N7 -> N4;
N8 -> N6;
    }
}

fn main() {}
