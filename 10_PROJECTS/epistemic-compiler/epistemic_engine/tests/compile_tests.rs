#[test]
fn compile_tests() {
    let t = trybuild::TestCases::new();
    t.pass("tests/pass/*.rs");
    t.pass("tests/pass_generated/*.rs");
    t.compile_fail("tests/fail/*.rs");
    t.compile_fail("tests/fail_generated/*.rs");
}
