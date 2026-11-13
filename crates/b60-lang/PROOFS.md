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

The CLI passes captured proof bytes to the pinned Lean checker over standard
input from a private invocation directory. Success requires both a successful
exit and the expected proof marker. Only then does it atomically publish the
proof file. A missing, rejecting or timed-out checker returns an error and
preserves any previous published file.

The receipt prints source, bytecode and full proof BLAKE3 digests. The proof path
is a replaceable alias: concurrent invocations check their own captured bytes,
and the last successful publication replaces that alias. `proof_blake3`
identifies the bytes checked by that invocation. Source/output aliases are
rejected to preserve the input. The checker defaults to a 30-second deadline;
`--checker-timeout-ms` accepts 1 through 120,000 milliseconds. On Unix, cleanup
terminates the isolated checker process group; other platforms terminate the
direct child only. This command does not provide hardware attestation or
authorize an effect.

Run the CLI regressions, including the real pinned checker and a mutated encoding
that Lean must reject, with:

```sh
cargo test --locked -p b60-lang --test prove_cli -- --include-ignored
```

Tests requiring the pinned Lean installation are explicitly ignored in ordinary
Rust test runs. The full command includes real-checker acceptance, mutated-proof
rejection, flag-like filenames, concurrent publication, source aliases and
timeout cleanup. Negative launcher fixtures test rejection and lifecycle only;
no fake checker establishes successful proof.
