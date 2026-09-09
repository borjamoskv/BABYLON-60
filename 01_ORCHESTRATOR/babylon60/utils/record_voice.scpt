tell application "QuickTime Player"
    activate
    set new_recording to new audio recording
    start new_recording
    delay 10
    stop new_recording
    
    -- Guardar el documento
    set doc to first document
    set thePath to "/Users/borjafernandezangulo/BABYLON-60/borja_sample.m4a"
    export doc in POSIX file thePath using settings preset "Audio Only"
    close doc without saving
end tell
