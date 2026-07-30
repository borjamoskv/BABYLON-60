#!/usr/bin/env osascript -l JavaScript

// MOSKV-1 APEX: TIER 0 MAC-MAESTRO ACTUATOR
// Reality Level: C5-REAL
// Executes pure semantic DOM extraction of macOS Accessibility Graph.

function run(argv) {
    var systemEvents = Application("System Events");
    
    // Get the currently active application
    var frontmostApp = systemEvents.processes.whose({ frontmost: true })[0];
    var appName = frontmostApp.name();
    
    var output = {
        exergy_status: "OPTIMAL",
        target_app: appName,
        semantic_nodes: []
    };

    try {
        // Extract the main window's semantic UI elements
        var mainWindow = frontmostApp.windows[0];
        var uiElements = mainWindow.entireContents();
        
        // Cap extraction at 50 nodes to maintain High-Exergy / Low-Latency
        var limit = Math.min(uiElements.length, 50);
        
        for (var i = 0; i < limit; i++) {
            var el = uiElements[i];
            var role = "UNKNOWN";
            var desc = "NULL";
            
            try { role = el.role(); } catch(e) {}
            try { desc = el.description() || el.name() || el.title(); } catch(e) {}
            
            if (desc !== "NULL" && desc !== null && desc !== "") {
                output.semantic_nodes.push({
                    id: i,
                    role: role,
                    semantic_intent: desc
                });
            }
        }
    } catch (e) {
        output.error = "No visible Accessibility DOM available for active window.";
    }

    // Output strictly as JSON Invariant (Zero-Anergy)
    return JSON.stringify(output, null, 2);
}
