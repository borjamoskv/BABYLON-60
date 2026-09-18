#!/usr/bin/env swift

import Foundation
import LocalAuthentication
import CryptoKit
import Security

func main() {
    let args = CommandLine.arguments
    var causalHash = "UNKNOWN"
    var message = "Aprobar mutación crítica en el KERNEL"

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
    context.touchIDAuthenticationAllowableReuseDuration = 0
    var error: NSError?

    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
        fputs("Biometría no disponible (¿Mac cerrado?): \(error?.localizedDescription ?? "Error desconocido")\n", stderr)
        exit(1)
    }

    let reason = "BABYLON-60 BFT Gate\nAcción: \(message)\nHash: \(causalHash)"
    context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, evaluateError in
        if success {
            do {
                // Generar firma real respaldada por el Secure Enclave (Hardware-Bound Attestation)
                // Usamos P256 ya que Ed25519 no está soportado nativamente en el enclave de macOS.
                let accessControl = SecAccessControlCreateWithFlags(
                    nil, 
                    kSecAttrAccessibleWhenUnlockedThisDeviceOnly, 
                    [.privateKeyUsage, .biometryCurrentSet], 
                    nil
                )!
                
                let authContext = LAContext()
                
                // Simulación de generación o recuperación de clave en Enclave
                let privateKey = try SecureEnclave.P256.Signing.PrivateKey()
                
                guard let dataToSign = causalHash.data(using: .utf8) else {
                    fputs("Error de codificación del hash causal.\n", stderr)
                    exit(1)
                }
                
                let signature = try privateKey.signature(for: dataToSign)
                let sigBase64 = signature.derRepresentation.base64EncodedString()
                let pubKeyBase64 = privateKey.publicKey.derRepresentation.base64EncodedString()
                
                // Retornar el payload criptográfico verificable a Iceoryx2 / BFT Ledger
                let jsonResponse = """
                {
                    "status": "ATTESTED",
                    "causal_hash": "\(causalHash)",
                    "secure_enclave_signature": "\(sigBase64)",
                    "public_key": "\(pubKeyBase64)"
                }
                """
                print(jsonResponse)
                exit(0)
            } catch {
                fputs("Error criptográfico del Secure Enclave: \(error)\n", stderr)
                exit(1)
            }
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
