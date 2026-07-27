#!/bin/bash
# Helper script to parse CLI arguments and convert to environment variables
# Usage: ./scripts/fuzz-args.sh <vitest-command> [--size N] [--seed N] [--multi-bin]

VITEST_CMD="$1"
shift  # Remove first arg (vitest command)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --size)
      export FUZZ_SIZE="$2"
      shift 2
      ;;
    --size=*)
      export FUZZ_SIZE="${1#*=}"
      shift
      ;;
    --seed)
      export RANDOM_SEED="$2"
      shift 2
      ;;
    --seed=*)
      export RANDOM_SEED="${1#*=}"
      shift
      ;;
    --multi-bin)
      export MULTI_BIN_MODE="true"
      shift
      ;;
    *)
      # Unknown argument, pass through to vitest
      VITEST_ARGS="$VITEST_ARGS $1"
      shift
      ;;
  esac
done

# Run vitest with remaining args
exec $VITEST_CMD $VITEST_ARGS

