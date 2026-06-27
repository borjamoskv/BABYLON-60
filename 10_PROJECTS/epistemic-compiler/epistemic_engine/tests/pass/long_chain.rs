use epistemic_engine::{epistemic, Inference, Transition};

epistemic! {
    graph long_chain {
        L01 -> L02;
        L02 -> L03;
        L03 -> L04;
        L04 -> L05;
        L05 -> L06;
        L06 -> L07;
        L07 -> L08;
        L08 -> L09;
        L09 -> L10;
    }
}

fn main() {
    let l01 = Inference::<states::L01>::new("START".to_string(), 1.0);
    let l02: Inference<states::L02> = l01.apply();
    let l03: Inference<states::L03> = l02.apply();
    let l04: Inference<states::L04> = l03.apply();
    let l05: Inference<states::L05> = l04.apply();
    let l06: Inference<states::L06> = l05.apply();
    let l07: Inference<states::L07> = l06.apply();
    let l08: Inference<states::L08> = l07.apply();
    let l09: Inference<states::L09> = l08.apply();
    let _l10: Inference<states::L10> = l09.apply();
}
