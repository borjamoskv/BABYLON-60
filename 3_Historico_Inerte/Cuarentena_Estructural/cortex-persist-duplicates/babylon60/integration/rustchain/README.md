# RustChain Staking & Open Judge SDK Integration

Provides direct integration with the RustChain network for self-improvement staking and Open Judge gates.

## Architecture

This module implements the following components:
1. **`RustChainClient`**: Async client that connects to the RPC gate, with a fail-safe offline fallback mode.
2. **`RustChainWallet`**: Ed25519-based wallet that manages keypairs and generates compliant RTC addresses.
3. **`Staking`**: A fail-safe `stake_and_acquire` flow that checks RPC gate health before signing transactions.
4. **`LangChain Tool`**: A `BaseTool` subclass (`RustChainStakingTool`) implementing the `stake_and_acquire_skill` interface.
5. **`MCP Server Tool`**: FastMCP bindings exposing `stake_and_acquire_skill` to other agents.
6. **`Open Judge Gates`**: Three default implementations of the `Judge` interface:
   - `ASTLintJudge`: Performs static AST analysis (e.g. banning terms like `eval`/`exec`, finding bare excepts).
   - `TestRunnerJudge`: Spawns sandbox tests in a temporary directory via subprocess.
   - `PolicyJudge`: Enforces constraints (e.g. max line limits, banned libraries, min comment ratio).
   - Cryptographic verdict signing and verification utilities via Ed25519.

## Quickstart

### Staking

```python
import asyncio
from cortex.integration.rustchain import RustChainWallet, RustChainClient, stake_and_acquire

async def main():
    wallet = RustChainWallet.create()
    client = RustChainClient(mock_mode=True)
    
    # Lock RTC stake and acquire skill
    try:
        receipt = await stake_and_acquire(
            wallet=wallet,
            client=client,
            skill="cortex_cognitive_scaling",
            amount=100
        )
        print("Staking success:", receipt["tx_hash"])
    except Exception as e:
        print("Staking failed:", e)

asyncio.run(main())
```

### Verification of Verdicts

```python
from cortex.integration.rustchain import ASTLintJudge

judge = ASTLintJudge()
code = "print('Hello World')"

# Sign and verify
verdict = judge.sign_verdict(priv_key_bytes, passed=True, reasons=[])
is_valid = judge.verify_verdict(verdict, pub_key_bytes)
```
