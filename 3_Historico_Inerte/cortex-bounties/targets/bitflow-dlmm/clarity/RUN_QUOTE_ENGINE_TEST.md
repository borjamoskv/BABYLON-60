# Running the Quote Engine Validation Fuzz Test

## Quick Start

From the `.bitflow-dlmm/clarity` directory, run:

```bash
source ~/.nvm/nvm.sh
nvm use node
FUZZ_SIZE=10 RANDOM_SEED=12345 npm test -- tests/dlmm-core-quote-engine-validation-fuzz.test.ts --run
```

## Progress Bar

The progress bar uses `/dev/tty` for real-time updates. It may not display in Cursor's integrated terminal. To see the progress bar:

1. **Run in a separate terminal** (Terminal.app on Mac):
   ```bash
   source ~/.nvm/nvm.sh
   nvm use node
   FUZZ_SIZE=100 RANDOM_SEED=12345 npm test -- tests/dlmm-core-quote-engine-validation-fuzz.test.ts --run
   ```

2. **Or check the test output** - the progress bar will still write to stderr, which should appear in the test output.

## Test Parameters

- `FUZZ_SIZE`: Number of transactions to run (default: 100)
- `RANDOM_SEED`: Random seed for reproducibility (default: Date.now())
- `MULTI_BIN_MODE`: Enable multi-bin swap testing (default: false)
  - Set to `true` to test both single-bin and multi-bin swaps (50/50 split)
  - When enabled, the test will generate swaps that require multiple bins

## What the Test Does

1. Performs random swaps (x-for-y and y-for-x)
   - **Single-bin mode** (default): Swaps on the active bin only
   - **Multi-bin mode** (`MULTI_BIN_MODE=true`): Mix of single-bin and multi-bin swaps (50/50)
2. Compares contract output against quote engine calculations from `pricing.py`
3. Detects exploits (when contract returns more than quote engine allows)
4. Logs results to `logs/quote-engine-validation/`

## Multi-Bin Mode

When `MULTI_BIN_MODE=true`:
- Test generates swaps that require multiple bins (exceeding active bin capacity)
- Uses swap router's `swap-x-for-y-simple-multi` / `swap-y-for-x-simple-multi` functions
- Validates against multi-bin quote engine calculations
- Tests bin discovery, traversal, and execution path validation

**Note**: For multi-bin swaps to work, the pool needs liquidity in multiple bins. The test will automatically discover bins with liquidity.

## Expected Output

You should see:
- Progress bar with stats (if running in a real terminal)
- Exploit detections (if any)
- Final summary with match rates


