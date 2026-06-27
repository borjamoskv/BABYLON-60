use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_46 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N4;
N7 -> N2;
    }
}

fn main() {}
