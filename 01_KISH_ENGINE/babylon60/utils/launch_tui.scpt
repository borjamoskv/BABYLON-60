set babylonHome to (system attribute "BABYLON_HOME")
if babylonHome is "" then
    set babylonHome to (POSIX path of (path to home folder)) & "BABYLON-60"
end if
tell application "Terminal"
    activate
    do script "python3 " & quoted form of (babylonHome & "/01_KISH_ENGINE/babylon60/utils/watchdog_tui.py")
    set the bounds of the first window to {0, 0, 1000, 800}
end tell
