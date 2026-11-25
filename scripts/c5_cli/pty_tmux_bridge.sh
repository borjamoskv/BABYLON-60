#!/bin/bash
# 🛡️ TMUX-PTY-Bridge-OMEGA (C5-REAL v2.0)
# Physical socket bridge for TUI automation.

SOCKET="/tmp/tmux_bridge.sock"
CMD="$1"
SESSION="$2"

if [ -z "$CMD" ] || [ -z "$SESSION" ]; then
    echo "Usage: $0 [spawn|read|history|wait|inject|resize|status|kill] [session_name] [args...]"
    exit 1
fi

case "$CMD" in
    spawn)
        EXEC_CMD="$3"
        if [ -z "$EXEC_CMD" ]; then
            echo "Error: spawn requires a command"
            exit 1
        fi
        # Check if already exists
        tmux -S "$SOCKET" has-session -t "$SESSION" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "Session $SESSION already exists."
            exit 0
        fi
        tmux -S "$SOCKET" new-session -d -s "$SESSION" "$EXEC_CMD"
        echo "Spawned session $SESSION running: $EXEC_CMD"
        ;;
    read)
        tmux -S "$SOCKET" capture-pane -t "$SESSION" -p
        ;;
    history)
        tmux -S "$SOCKET" capture-pane -S -32768 -t "$SESSION" -p
        ;;
    wait)
        PATTERN="$3"
        TIMEOUT="${4:-10}"
        if [ -z "$PATTERN" ]; then
            echo "Error: wait requires a pattern"
            exit 1
        fi
        START_TIME=$(date +%s)
        while true; do
            CURRENT_TIME=$(date +%s)
            ELAPSED=$((CURRENT_TIME - START_TIME))
            if [ $ELAPSED -ge $TIMEOUT ]; then
                echo "Timeout of ${TIMEOUT}s reached waiting for pattern: $PATTERN"
                exit 1
            fi
            # Capture and grep
            if tmux -S "$SOCKET" capture-pane -t "$SESSION" -p 2>/dev/null | grep -E "$PATTERN" > /dev/null; then
                exit 0
            fi
            sleep 0.2
        done
        ;;
    inject)
        KEYS="$3"
        if [ -z "$KEYS" ]; then
            echo "Error: inject requires keys"
            exit 1
        fi
        tmux -S "$SOCKET" send-keys -t "$SESSION" "$KEYS"
        ;;
    resize)
        WIDTH="$3"
        HEIGHT="$4"
        if [ -z "$WIDTH" ] || [ -z "$HEIGHT" ]; then
            echo "Error: resize requires width and height"
            exit 1
        fi
        tmux -S "$SOCKET" resize-window -t "$SESSION" -x "$WIDTH" -y "$HEIGHT"
        ;;
    status)
        tmux -S "$SOCKET" has-session -t "$SESSION" 2>/dev/null
        if [ $? -eq 0 ]; then
            REAL_PID=$(tmux -S "$SOCKET" list-panes -t "$SESSION" -F '#{pane_pid}')
            echo "ONLINE (PID: $REAL_PID)"
        else
            echo "OFFLINE"
        fi
        ;;
    kill)
        tmux -S "$SOCKET" kill-session -t "$SESSION" 2>/dev/null
        echo "Killed session $SESSION"
        ;;
    *)
        echo "Unknown command: $CMD"
        exit 1
        ;;
esac
