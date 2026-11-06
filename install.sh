#!/usr/bin/env bash
# Install the supported terminal CLI and stdio MCP server.
set -euo pipefail

DRY_RUN=0
START_MCP=0
CLIENT=''
while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --mcp) START_MCP=1; shift ;;
        --client)
            if [ "$#" -lt 2 ] || [ "$2" != codex ]; then
                echo 'Expected --client codex.' >&2; exit 2
            fi
            CLIENT="$2"; shift 2 ;;
        --help|-h)
            echo 'Usage: bash install.sh [--dry-run] [--client codex | --mcp]'
            echo 'Installs the terminal CLI; --client codex activates Codex; --mcp starts the stdio memory server.'
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done
if [ -n "$CLIENT" ] && [ "$START_MCP" = 1 ]; then
    echo '--client cannot be combined with --mcp; activate Codex separately before starting the stdio server.' >&2
    exit 2
fi

REPO_DIR="${BABYLON_INSTALL_DIR:-$HOME/BABYLON-60}"
if [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
    if [ -f "$SCRIPT_ROOT/pyproject.toml" ]; then REPO_DIR="$SCRIPT_ROOT"; fi
elif [ -f "pyproject.toml" ] && [ -d "01_KISH_ENGINE/babylon60" ]; then
    REPO_DIR="$(pwd -L)"
fi
if [ ! -d "$REPO_DIR" ]; then
    if [ "$DRY_RUN" = 1 ]; then echo "Checkout not found: $REPO_DIR" >&2; exit 1; fi
    git clone --depth 1 https://github.com/borjamoskv/BABYLON-60.git "$REPO_DIR" >&2
fi
for required in pyproject.toml uv.lock 01_KISH_ENGINE/babylon60/cli/main_dispatcher.py 01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py 01_KISH_ENGINE/babylon60/presentation.md; do
    if [ ! -f "$REPO_DIR/$required" ]; then echo "Missing distribution file: $required" >&2; exit 1; fi
done
CLI="$REPO_DIR/.venv/bin/babylon60"
SERVER="$REPO_DIR/.venv/bin/babylon60-mcp"
if [ "$DRY_RUN" = 1 ]; then
    echo "BABYLON_TERMINAL_VERIFIED: $REPO_DIR"
    echo 'Install: uv sync --locked --no-dev --no-editable'
    echo "CLI: $CLI"
    echo "MCP stdio: $SERVER"
    printf 'Agent presentation: %q presentation\n' "$CLI"
    if [ -n "$CLIENT" ]; then
        printf 'Setup preview after installation (not executed): %q setup --client codex --dry-run\n' "$CLI"
        echo 'Installation and activation are planned only; no executables or global settings are changed.'
    elif [ "$START_MCP" = 1 ]; then
        printf 'Start after installation: %q\n' "$SERVER"
    else
        echo 'Codex integration: not activated.'
        printf 'Activate after installation: %q setup --client codex\n' "$CLI"
    fi
    exit 0
fi
if ! command -v uv >/dev/null 2>&1; then
    echo 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/ and rerun.' >&2
    exit 1
fi
if [ -e "$REPO_DIR/.git" ]; then
    if ! changes="$(git -C "$REPO_DIR" status --porcelain)"; then
        echo 'Cannot verify checkout state.' >&2; exit 1
    fi
    if [ -n "$changes" ]; then
        echo 'Install from a clean checkout/worktree or the source release bundle; local changes are preserved.' >&2
        exit 1
    fi
fi
cd "$REPO_DIR"
# Installer output must never precede JSON-RPC on the stdio server's stdout.
# Install the wheel so excluded experiments are not exposed through an editable .pth.
uv sync --locked --no-dev --no-editable >&2
if [ ! -x "$CLI" ] || [ ! -x "$SERVER" ]; then
    echo 'Installation did not create the CLI and MCP executables.' >&2
    exit 1
fi
if [ "$START_MCP" = 1 ]; then
    exec "$SERVER"
fi
if [ -n "$CLIENT" ]; then
    "$CLI" setup --client "$CLIENT"
else
    "$CLI" --help
fi
echo "CLI installed: $CLI"
echo "MCP stdio: $SERVER"
printf 'Agents: read the presentation contract with %q presentation\n' "$CLI"
if [ -z "$CLIENT" ]; then
    echo 'Codex integration: not activated.'
    printf 'Next step: %q setup --client codex\n' "$CLI"
else
    echo 'Next step: open a new Codex conversation to load Babylon; application of the preferences is not yet evaluated.'
fi
