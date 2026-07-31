// C5-REAL EXERGY CERTIFIED
/*
 * Frida Script: IPC Intercept (HyperBridge / MCP)
 * Objetivo: Claude Cowork
 * Protocolo C5-REAL (M3 - Causal)
 */

console.log("[*] Inyectando C5-REAL Frida Hook en Claude Cowork...");

// Interceptar llamadas a 'send' genéricas en sockets de red (para capturar IPC/MCP en texto plano)
var sendPtr = Module.findExportByName(null, 'send');
if (sendPtr) {
    Interceptor.attach(sendPtr, {
        onEnter: function (args) {
            var fd = args[0].toInt32();
            var buf = args[1];
            var len = args[2].toInt32();

            try {
                var payload = buf.readUtf8String(len);
                if (payload.includes("OPERON") || payload.includes("MCP") || payload.includes("claude")) {
                    console.log("\n[C5-REAL IPC HOOK] Outbound Payload (fd: " + fd + "):");
                    console.log(payload);
                }
            } catch (e) {
                // Ignore non-utf8 payloads
            }
        }
    });
} else {
    console.log("[-] Export 'send' no encontrado.");
}

// Hookear la lectura de variables de entorno (getenv) para manipular la telemetría al vuelo
var getenvPtr = Module.findExportByName(null, 'getenv');
if (getenvPtr) {
    Interceptor.attach(getenvPtr, {
        onEnter: function (args) {
            this.envName = args[0].readUtf8String();
        },
        onLeave: function (retval) {
            if (this.envName === "OPERON_DISABLE_TELEMETRY" || this.envName === "CLAUDE_CODE_DISABLE_TELEMETRY") {
                console.log("[M3-BYPASS] Interceptado getenv(" + this.envName + ")");
                // Aquí se podría forzar un retorno '1' si Frida pudiera alocar string en memoria de forma segura
            }
        }
    });
}
