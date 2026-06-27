use epistemic_engine::epistemic;

epistemic! {
    graph fail_fuzz_36 {
        N0 -> N1;
N1 -> N2;
N2 -> N3;
N3 -> N4;
N4 -> N5;
N5 -> N6;
N6 -> N0;
    }
}

fn main() {}
