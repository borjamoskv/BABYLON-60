# B60 control flow proofs

`b60 prove program.b60` compiles the actual source and checks the resulting pure
control flow with the Lean toolchain pinned in
[lean-toolchain](../../proof/lean/lean-toolchain). The CLI currently accepts
compiled `HALT` and `NOOP` operations, including source aliases that compile to
those operations. For example:

```text
NOOP
HALT
```

The raw bytecode API `Lean4Emitter::emit_bytecode_trace_proof` additionally models
`JUMP` with its two-byte little-endian target. The source compiler currently has
no `JUMP` syntax. The emitter returns `Result<String, String>` and rejects unknown
or unsupported opcodes, truncated operands, jumps outside instruction boundaries,
cycles, fallthrough without `HALT`, empty programs and inputs above 4,096 bytes.
It does not execute effectful instructions to collect a trace.

The generated Lean file checks that the instruction encoding equals the exact
byte stream, instruction boundaries are contiguous, jump targets are valid, and
the concrete execution reaches `HALT` without rejection within the VM fuel
limit. Program counter and fuel use `BitVec 64`; proof iteration and list indices
are bounded metadata. This is a model of the listed control instructions, not a
proof of the whole ISA or compiler correctness.

The CLI returns success only after the pinned Lean checker returns success. It
prints the source and bytecode BLAKE3 digests and the proof path. A missing or
rejecting checker returns an error; a file emitted before that error remains
unverified. This command does not provide hardware attestation or authorize an
effect.

Run the CLI regressions, including the real pinned checker and a mutated encoding
that Lean must reject, with:

```sh
cargo test --locked -p b60-lang --test prove_cli -- --include-ignored
```

The positive checker tests are explicitly ignored in ordinary Rust test runs
because they require the pinned Lean installation. The other rejection tests do
not require Lean and never use a fake checker to establish successful proof.
