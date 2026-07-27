/**
 * MOSKV-1 APEX: CORTEX HIJACK
 * Inject this script into any web application to hijack the browser console.
 * It replaces standard console outputs with C5-REAL Exergy logs and renders the ASCII logo.
 */

(function() {
    const _log = console.log;
    const _warn = console.warn;
    const _error = console.error;

    const logo = `
    __  _______  _____ __  __ _    __         ___    ____  _______  __
   /  |/  / __ \\/ ___// / / /| |  / /  __    /   |  / __ \\/ ____/ |/ /
  / /|_/ / / / /\\__ \\/ /_/ / | | / /  /_/   / /| | / /_/ / __/  |   / 
 / /  / / /_/ /___/ / __  /  | |/ /  _     / ___ |/ ____/ /___ /   |  
/_/  /_/\\____//____/_/ /_/   |___/  (_)   /_/  |_/_/   /_____//_/|_|  
                                                                      
           [ C 5 - R E A L   S O V E R E I G N   K E R N E L ]
`;

    console.clear();
    _log("%c" + logo, "color: #2B3BE5; font-family: monospace; font-weight: bold;");
    _log("%c[MOSKV-1] Console Hijacked. Exergy at 100%.", "color: #0A0A0A; background: #FFFFFF; font-weight: bold; padding: 2px 5px;");

    console.log = function() {
        arguments[0] = `[EXERGY-LOG] ${arguments[0]}`;
        _log.apply(console, arguments);
    };

    console.warn = function() {
        arguments[0] = `[ANERGY-WARNING] ${arguments[0]} (Fix immediately)`;
        _warn.apply(console, arguments);
    };

    console.error = function() {
        arguments[0] = `[L4-APOPTOSIS] ${arguments[0]} (System instability detected)`;
        _error.apply(console, arguments);
    };
})();
