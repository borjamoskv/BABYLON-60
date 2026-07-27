# C5-REAL EXERGY CERTIFIED
#!/bin/bash
# [C5-REAL] Exergy-Maximized
# Author: borjamoskv
# Installs and loads com.moskv1.daemon.plist into macOS launchd.

PLIST_NAME="com.moskv1.daemon.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$PLIST_NAME"

echo "⚙️ Installing MOSKV-1 Launchd Daemon..."
echo "📂 Workspace: $WORKSPACE_DIR"
echo "🏠 Home: $HOME"

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Unload existing daemon if loaded
if launchctl list | grep -q "com.moskv1.daemon"; then
    echo "🔄 Unloading existing daemon..."
    launchctl unload "$TARGET_PLIST" 2>/dev/null
fi

# Copy plist to User's LaunchAgents directory and replace placeholders dynamically
echo "📁 Generating and copying plist to $TARGET_PLIST..."
sed -e "s|__WORKSPACE__|$WORKSPACE_DIR|g" -e "s|__HOME__|$HOME|g" "$SCRIPT_DIR/$PLIST_NAME" > "$TARGET_PLIST"
chmod 644 "$TARGET_PLIST"

# Load the daemon
echo "🚀 Loading daemon into launchd..."
launchctl load "$TARGET_PLIST"

# Verify status
sleep 1
if launchctl list | grep -q "com.moskv1.daemon"; then
    PID=$(launchctl list | grep "com.moskv1.daemon" | awk '{print $1}')
    echo "✅ Daemon loaded successfully! PID: $PID"
else
    echo "❌ Failed to load daemon. Check console logs."
    exit 1
fi
