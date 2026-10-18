#!/usr/bin/env bash
# Install the supported terminal CLI and stdio MCP server.
set -euo pipefail

DRY_RUN=0
START_MCP=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --mcp) START_MCP=1 ;;
        --help|-h)
            echo 'Usage: bash install.sh [--dry-run] [--mcp]'
            echo 'Installs the terminal CLI; --mcp starts the stdio memory server.'
            exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done

REPO_DIR="${BABYLON_INSTALL_DIR:-$HOME/BABYLON-60}"
if [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
    if [ -f "$SCRIPT_ROOT/pyproject.toml" ]; then REPO_DIR="$SCRIPT_ROOT"; fi
elif [ -f "pyproject.toml" ] && [ -d "01_KISH_ENGINE/babylon60" ]; then
    REPO_DIR="$(pwd -L)"
fi
if [ ! -d "$REPO_DIR" ]; then
    if [ "$DRY_RUN" = 1 ]; then echo "Checkout not found: $REPO_DIR" >&2; exit 1; fi
    git clone --depth 1 https://github.com/borjamoskv/BABYLON-60.git "$REPO_DIR"
fi
for required in pyproject.toml uv.lock 01_KISH_ENGINE/babylon60/cli/main_dispatcher.py 01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py 01_KISH_ENGINE/babylon60/presentation.md; do
    if [ ! -f "$REPO_DIR/$required" ]; then echo "Missing distribution file: $required" >&2; exit 1; fi
done
if [ "$DRY_RUN" = 1 ]; then
    echo "BABYLON_TERMINAL_VERIFIED: $REPO_DIR"
    echo 'Install: uv sync --locked --no-dev'
    echo "CLI: $REPO_DIR/.venv/bin/babylon60"
    echo "MCP stdio: $REPO_DIR/.venv/bin/babylon60-mcp"
    echo "Agent presentation: $REPO_DIR/.venv/bin/babylon60 presentation"
    exit 0
fi
if ! command -v uv >/dev/null 2>&1; then
    echo 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/ and rerun.' >&2
    exit 1
fi
if [ -e "$REPO_DIR/.git" ] && [ -n "$(git -C "$REPO_DIR" status --porcelain)" ]; then
    echo 'Install from a clean checkout/worktree or the source release bundle; local changes are preserved.' >&2
    exit 1
fi
cd "$REPO_DIR"
uv sync --locked --no-dev
if [ "$START_MCP" = 1 ]; then
    exec "$REPO_DIR/.venv/bin/babylon60-mcp"
fi
"$REPO_DIR/.venv/bin/babylon60" --help
echo "CLI installed: $REPO_DIR/.venv/bin/babylon60"
echo "MCP stdio: $REPO_DIR/.venv/bin/babylon60-mcp"
echo "Agents: read the presentation contract with $REPO_DIR/.venv/bin/babylon60 presentation"
