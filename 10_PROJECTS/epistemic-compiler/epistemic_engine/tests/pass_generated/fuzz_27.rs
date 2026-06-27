use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_27 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N1;
N5 -> N4;
N6 -> N5;
N7 -> N1;
    }
}

fn main() {}
