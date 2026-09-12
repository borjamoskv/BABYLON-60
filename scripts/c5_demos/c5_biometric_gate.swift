import Foundation
import LocalAuthentication

let semaphore = DispatchSemaphore(value: 0)
let context = LAContext()
context.touchIDAuthenticationAllowableReuseDuration = 0
var error: NSError?

// Invariante C5-REAL: Fricción Biométrica requerida para mutación topológica
let actionContext = CommandLine.arguments.count > 1 ? CommandLine.arguments.dropFirst().joined(separator: " ") : "transición de estado no especificada"
let reason = "BABYLON-60 Atestación requerida para: \(actionContext)"

if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
    context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, authenticationError in
        if success {
            print("{\"status\": \"success\", \"exergy_attested\": true, \"message\": \"Fricción biométrica validada.\"}")
            exit(0)
        } else {
            print("{\"status\": \"error\", \"exergy_attested\": false, \"message\": \"Fallo en atestación: \(authenticationError?.localizedDescription ?? "Desconocido")\"}")
            exit(1)
        }
        semaphore.signal()
    }
} else {
    // Fallback if TouchID is not available or disabled in terminal (VS Code sandbox issue)
    print("{\"status\": \"error\", \"exergy_attested\": false, \"message\": \"Sensor biométrico inaccesible. ¿Ejecución sandboxeada?\"}")
    exit(2)
}

semaphore.wait()
