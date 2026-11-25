#![no_main]
use libfuzzer_sys::fuzz_target;
use babylon60_fuzz::{fuzz_parse_instruction, fuzz_eval_step};

fuzz_target!(|data: &[u8]| {
    let _ = fuzz_parse_instruction(data);
    let _ = fuzz_eval_step(data);
});
