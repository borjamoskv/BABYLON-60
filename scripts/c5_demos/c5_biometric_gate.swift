import Foundation
import LocalAuthentication

let semaphore = DispatchSemaphore(value: 0)
let context = LAContext()
var error: NSError?

// Invariante C5-REAL: Fricción Biométrica requerida para mutación topológica
let reason = "BABYLON-60: Atestación Causal requerida para transición de estado al Punto Fijo Ω."

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
