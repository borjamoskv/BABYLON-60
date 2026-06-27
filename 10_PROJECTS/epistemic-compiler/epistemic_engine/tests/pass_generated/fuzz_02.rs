use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_2 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N0;
N6 -> N5;
    }
}

fn main() {}
