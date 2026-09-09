#!/usr/bin/env swift

import Foundation
import LocalAuthentication

func main() {
    let args = CommandLine.arguments
    var causalHash = "UNKNOWN"
    var message = "Aprobar mutación crítica en el KERNEL"

    // Parse simple args: --causal-hash <hash> --message <msg>
    var i = 1
    while i < args.count {
        if args[i] == "--causal-hash" && i + 1 < args.count {
            causalHash = args[i+1]
            i += 2
        } else if args[i] == "--message" && i + 1 < args.count {
            message = args[i+1]
            i += 2
        } else {
            i += 1
        }
    }

    let context = LAContext()
    var error: NSError?

    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
        fputs("Biometría no disponible (¿Mac cerrado?): \(error?.localizedDescription ?? "Error desconocido")\n", stderr)
        exit(1)
    }

    let reason = "BABYLON-60 Causal Gate\nAcción: \(message)\nHash: \(causalHash)"
    context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, evaluateError in
        if success {
            print("SIGNED_TOUCHID:\(causalHash)")
            exit(0)
        } else {
            if let err = evaluateError {
                fputs("Auth error: \(err.localizedDescription)\n", stderr)
            }
            exit(1)
        }
    }

    // Mantener el hilo principal vivo para que macOS pueda renderizar la interfaz gráfica (UI)
    RunLoop.main.run()
}

main()
