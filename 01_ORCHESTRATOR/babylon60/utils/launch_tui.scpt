tell application "Terminal"
    activate
    do script "python3 /Users/borjafernandezangulo/BABYLON-60/01_ORCHESTRATOR/babylon60/utils/watchdog_tui.py"
    set the bounds of the first window to {0, 0, 1000, 800}
end tell
