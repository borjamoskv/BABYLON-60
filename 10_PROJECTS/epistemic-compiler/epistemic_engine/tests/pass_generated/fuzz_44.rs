use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_44 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N4;
N6 -> N5;
N7 -> N2;
    }
}

fn main() {}
