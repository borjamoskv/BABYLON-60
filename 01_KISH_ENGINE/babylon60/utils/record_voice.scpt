set babylonHome to (system attribute "BABYLON_HOME")
if babylonHome is "" then
    set babylonHome to (POSIX path of (path to home folder)) & "BABYLON-60"
end if
tell application "QuickTime Player"
    activate
    set new_recording to new audio recording
    start new_recording
    delay 10
    stop new_recording
    
    -- Guardar el documento
    set doc to first document
    set thePath to babylonHome & "/borja_sample.m4a"
    export doc in POSIX file thePath using settings preset "Audio Only"
    close doc without saving
end tell
