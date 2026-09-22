#!/usr/bin/env swift

import Foundation
import LocalAuthentication
import CryptoKit
import Security

// Códigos de salida canónicos sexagesimales (C5-REAL Standard)
enum C5ExitCode: Int32 {
    case success = 0              // 0x00: Atestación de hardware exitosa
    case genericError = 1         // 0x01: Error de sintaxis / argumentos CLI
    case cannotEvaluate = 60      // 0x3C: Sin capacidad de evaluación biométrica ni passcode
    case notInteractive = 61      // 0x3D: Subproceso sin sesión interactiva de WindowServer (Sandbox)
    case clamshellLocked = 62     // 0x3E: Modo clamshell (tapa cerrada sin sensor TouchID externo)
    case userCancel = 63          // 0x3F: Cancelación deliberada por el operador o timeout
    case enclaveCryptoError = 64  // 0x40: Falla en Secure Enclave / CryptoKit
}

func emitErrorJson(status: String, code: Int?, description: String, exitCode: C5ExitCode) -> Never {
    let escapedDesc = description.replacingOccurrences(of: "\"", with: "\\\"")
    let json = """
    {"status":"\(status)","la_code":\(code ?? -1),"description":"\(escapedDesc)","c5_exit":\(exitCode.rawValue)}
    """
    fputs("\(json)\n", stderr)
    exit(exitCode.rawValue)
}

func main() {
    let args = CommandLine.arguments
    var causalHash = "UNKNOWN"
    var message = "Aprobar mutación crítica en el KERNEL"
    var forceBiometricsOnly = false

    var i = 1
    while i < args.count {
        if args[i] == "--causal-hash" && i + 1 < args.count {
            causalHash = args[i+1]
            i += 2
        } else if args[i] == "--message" && i + 1 < args.count {
            message = args[i+1]
            i += 2
        } else if args[i] == "--force-biometrics-only" {
            forceBiometricsOnly = true
            i += 1
        } else if args[i] == "--help" || args[i] == "-h" {
            print("Uso: c5_biometric_gate.swift --causal-hash <HASH> [--message <MSG>] [--force-biometrics-only]")
            exit(0)
        } else {
            i += 1
        }
    }

    let context = LAContext()
    context.touchIDAuthenticationAllowableReuseDuration = 0
    var error: NSError?

    // Selección adaptativa de política:
    // 1. Intento primario: Biometría estricta (TouchID en chasis o Magic Keyboard).
    // 2. Si falla por clamshell / biometría no disponible y no se forzó exclusividad biométrica:
    //    Conmutar a .deviceOwnerAuthentication (soporte para Apple Watch Series 7 y Passcode seguro).
    var targetPolicy: LAPolicy = .deviceOwnerAuthenticationWithBiometrics
    var canEval = context.canEvaluatePolicy(targetPolicy, error: &error)

    if !canEval && !forceBiometricsOnly {
        if let laErr = error as? LAError {
            if laErr.code == .biometryNotAvailable || laErr.code == .biometryNotEnrolled || laErr.code == .biometryLockout {
                var ownerError: NSError?
                if context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &ownerError) {
                    targetPolicy = .deviceOwnerAuthentication
                    canEval = true
                    error = nil
                }
            }
        }
    }

    guard canEval else {
        let laErr = error as? LAError
        let code = laErr?.code.rawValue
        let desc = error?.localizedDescription ?? "Evaluación de política denegada"

        if let err = laErr {
            switch err.code {
            case .notInteractive:
                emitErrorJson(status: "NOT_INTERACTIVE", code: code, description: desc, exitCode: .notInteractive)
            case .biometryNotAvailable:
                emitErrorJson(status: "CLAMSHELL_OR_NO_BIOMETRICS", code: code, description: desc, exitCode: .clamshellLocked)
            case .passcodeNotSet, .biometryNotEnrolled:
                emitErrorJson(status: "AUTHENTICATION_UNCONFIGURED", code: code, description: desc, exitCode: .cannotEvaluate)
            default:
                emitErrorJson(status: "CANNOT_EVALUATE", code: code, description: desc, exitCode: .cannotEvaluate)
            }
        } else {
            emitErrorJson(status: "CANNOT_EVALUATE", code: nil, description: desc, exitCode: .cannotEvaluate)
        }
    }

    let reason = "BABYLON-60 BFT Gate\nAcción: \(message)\nHash: \(causalHash)"
    context.evaluatePolicy(targetPolicy, localizedReason: reason) { success, evaluateError in
        if success {
            do {
                // Generar firma real respaldada por el Secure Enclave (Hardware-Bound Attestation P-256)
                let privateKey = try SecureEnclave.P256.Signing.PrivateKey()

                guard let dataToSign = causalHash.data(using: .utf8) else {
                    emitErrorJson(status: "ENCODING_ERROR", code: nil, description: "Fallo de codificación UTF-8 del hash", exitCode: .genericError)
                }

                let signature = try privateKey.signature(for: dataToSign)
                let sigBase64 = signature.derRepresentation.base64EncodedString()
                let pubKeyBase64 = privateKey.publicKey.derRepresentation.base64EncodedString()

                let jsonResponse = """
                {
                    "status": "ATTESTED",
                    "causal_hash": "\(causalHash)",
                    "policy_used": "\(targetPolicy == .deviceOwnerAuthenticationWithBiometrics ? "TouchID" : "AppleWatch_or_Passcode")",
                    "secure_enclave_signature": "\(sigBase64)",
                    "public_key": "\(pubKeyBase64)"
                }
                """
                print(jsonResponse)
                exit(C5ExitCode.success.rawValue)
            } catch {
                emitErrorJson(status: "SECURE_ENCLAVE_CRYPTO_ERROR", code: nil, description: "\(error)", exitCode: .enclaveCryptoError)
            }
        } else {
            let laErr = evaluateError as? LAError
            let code = laErr?.code.rawValue
            let desc = evaluateError?.localizedDescription ?? "Autenticación fallida"

            if let err = laErr {
                switch err.code {
                case .userCancel, .systemCancel, .appCancel:
                    emitErrorJson(status: "OPERATOR_ABORT", code: code, description: desc, exitCode: .userCancel)
                case .notInteractive:
                    emitErrorJson(status: "NOT_INTERACTIVE", code: code, description: desc, exitCode: .notInteractive)
                case .biometryNotAvailable:
                    emitErrorJson(status: "BIOMETRY_LOCKED", code: code, description: desc, exitCode: .clamshellLocked)
                default:
                    emitErrorJson(status: "AUTH_FAILED", code: code, description: desc, exitCode: .userCancel)
                }
            } else {
                emitErrorJson(status: "AUTH_FAILED", code: nil, description: desc, exitCode: .userCancel)
            }
        }
    }

    RunLoop.main.run()
}

main()
