#!/bin/bash
# C5-REAL: KV Cache Entropy Enforcer
# Injects sync_vault_uuids.py into the local .git/hooks/pre-commit
# Enforces Ω38 and prevents session accumulation (Exergy Optimizer Bloat).

HOOK_PATH=".git/hooks/pre-commit"

if [ ! -f "$HOOK_PATH" ]; then
    echo "[-] Error: pre-commit hook not found at $HOOK_PATH"
    exit 1
fi

if grep -q "sync_vault_uuids.py" "$HOOK_PATH"; then
    echo "[+] KV Cache Entropy Purge is already active in Git Sentinel."
else
    sed -i '' 's/exit 0/python3 scripts\/sync_vault_uuids.py || echo "[!] WARNING: Could not sync vault UUIDs."\nexit 0/' "$HOOK_PATH"
    echo "[+] KV Cache Entropy Purge injected into Git Sentinel."
fi
