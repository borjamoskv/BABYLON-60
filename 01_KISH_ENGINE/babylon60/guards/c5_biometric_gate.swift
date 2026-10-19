#!/usr/bin/env swift

import Foundation
import LocalAuthentication
import CryptoKit
import Security
import AppKit
import Darwin

/// Detección automática en silicio del entorno emisor (Antigravity, Claude Code, ChatGPT, Codex, Cursor, Terminal)
func detectCallingEnvironment() -> String {
    let env = ProcessInfo.processInfo.environment

    // 1. Detección por variables de entorno explícitas
    if env["ANTIGRAVITY_AGENT"] != nil || env["ANTIGRAVITY_CONVERSATION_ID"] != nil || env["ANTIGRAVITY_APP_DATA_DIR"] != nil {
        return "Antigravity"
    }
    if env["CLAUDE_CODE_ENTRYPOINT"] != nil || env["CLAUDE_SESSION_ID"] != nil || env["CLAUDE_PROJECT_ROOT"] != nil {
        return "Claude Code"
    }
    if env["CODEX_SESSION"] != nil || env["OPENAI_CODEX"] != nil {
        return "Codex"
    }
    if env["CURSOR_TRACE_ID"] != nil || env["CURSOR_AGENT"] != nil {
        return "Cursor"
    }
    if env["WINDSURF_SESSION"] != nil {
        return "Windsurf"
    }

    // 2. Inspección del árbol de procesos de Darwin vía sysctl (sub-microsegundo, cero subshell)
    var currentPid = getpid()
    for _ in 0..<8 {
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, currentPid]
        var proc = kinfo_proc()
        var size = MemoryLayout<kinfo_proc>.size
        if sysctl(&mib, 4, &proc, &size, nil, 0) == 0 {
            let parentPid = proc.kp_eproc.e_ppid
            if parentPid <= 1 { break }
            
            var parentMib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, parentPid]
            var parentProc = kinfo_proc()
            var parentSize = MemoryLayout<kinfo_proc>.size
            if sysctl(&parentMib, 4, &parentProc, &parentSize, nil, 0) == 0 {
                let comm = withUnsafeBytes(of: parentProc.kp_proc.p_comm) { rawPtr -> String in
                    let ptr = rawPtr.baseAddress!.assumingMemoryBound(to: CChar.self)
                    return String(cString: ptr)
                }.lowercased()
                
                if comm.contains("antigravity") { return "Antigravity" }
                if comm.contains("claude") { return "Claude Code" }
                if comm.contains("chatgpt") { return "ChatGPT" }
                if comm.contains("codex") { return "Codex" }
                if comm.contains("cursor") { return "Cursor" }
                if comm.contains("windsurf") { return "Windsurf" }
                if comm.contains("aider") { return "Aider" }
                if comm.contains("iterm") { return "iTerm2" }
                if comm.contains("ghostty") { return "Ghostty" }
                if comm.contains("warp") { return "Warp" }
                if comm.contains("terminal") { return "Terminal macOS" }
            }
            currentPid = parentPid
        } else {
            break
        }
    }

    if let termProgram = env["TERM_PROGRAM"] {
        if termProgram.contains("iTerm") { return "iTerm2" }
        if termProgram.contains("Apple_Terminal") { return "Terminal macOS" }
        if termProgram.contains("ghostty") { return "Ghostty" }
        if termProgram.contains("vscode") { return "VS Code" }
        if termProgram.contains("Warp") { return "Warp" }
        return termProgram
    }

    return "Terminal / Shell"
}


enum SigningContractError: Error {
    case invalidHex, causalHashMismatch, unavailableAccessControl
    case legacyKeyRequiresMigration, keyStorageFailure, invalidSignature
}
func strictSigningHex(_ value: String) throws -> Data {
    let bytes = Array(value.utf8)
    guard !bytes.isEmpty, bytes.count % 2 == 0 else { throw SigningContractError.invalidHex }
    func nibble(_ byte: UInt8) throws -> UInt8 {
        switch byte {
        case 48...57: return byte - 48
        case 65...70: return byte - 65 + 10
        case 97...102: return byte - 97 + 10
        default: throw SigningContractError.invalidHex
        }
    }
    var data = Data()
    data.reserveCapacity(bytes.count / 2)
    for i in stride(from: 0, to: bytes.count, by: 2) {
        data.append(try (nibble(bytes[i]) << 4) | nibble(bytes[i + 1]))
    }
    return data
}
func signingContractPayload(causalHash: String, signHex: String) throws -> Data {
    guard try strictSigningHex(causalHash).count == 32 else { throw SigningContractError.invalidHex }
    if signHex.isEmpty { return Data(causalHash.utf8) } // Existing digest-only CLI.
    let payload = try strictSigningHex(signHex)
    let digest = SHA256.hash(data: payload).map { String(format: "%02x", $0) }.joined()
    guard digest == causalHash.lowercased() else { throw SigningContractError.causalHashMismatch }
    return payload
}
struct BiometricKeyRecord: Codable {
    let version: Int
    let keyData: Data
}
func recordedBiometricKey(_ data: Data) throws -> Data {
    guard let record = try? JSONDecoder().decode(BiometricKeyRecord.self, from: data),
          record.version == 2, !record.keyData.isEmpty else {
        throw SigningContractError.legacyKeyRequiresMigration
    }
    return record.keyData
}
func persistBiometricKey(_ keyData: Data, at path: String) throws {
    let bytes = try JSONEncoder().encode(BiometricKeyRecord(version: 2, keyData: keyData))
    let fd = open(path, O_WRONLY | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR)
    guard fd >= 0 else { throw SigningContractError.keyStorageFailure }
    let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    try file.write(contentsOf: bytes)
    try file.synchronize()
    try file.close()
}

func main() {
    let args = CommandLine.arguments

    if args.contains("--help") || args.contains("-h") {
        print("""
        Uso: c5_biometric_gate --action <acción> [--prompt <motivo>] [--agent <agente>] [--scope <ámbito>] --causal-hash <hash> [--sound <sonido>] [--no-sound] [--preview]

        Parámetros:
          --action <acción>       Qué se va a ejecutar (obligatorio o vía --message)
          --prompt <texto>        Prompt del usuario o motivo específico que disparó la mutación
          --reason / --detail     Alias de --prompt
          --agent <agente>        Nombre del agente (si se omite, se auto-detecta: Antigravity, Claude Code, ChatGPT, Codex, Cursor)
          --scope <ámbito>        Archivo, carpeta o repositorio afectado
          --causal-hash <hash>    Hash SHA-256 de la mutación
          --sign-hex <hex>        Firma directamente los bytes crudos decodificados de este hex (si se omite, firma el hash causal en UTF-8)
          --sound <nombre>        Sonido de alerta (default: Ping, opciones: Tink, Glass, Hero, Submarine)
          --no-sound / --silent   Suprime el sonido de alerta
          --anonymous             No adjunta el nombre de usuario local en el recibo
          --preview               Muestra la representación visual del modal sin solicitar biometría
          --help, -h              Muestra esta ayuda
        """)
        exit(0)
    }

    var action = ""
    var prompt = ""
    var passedAgent = ""
    var scope = "BABYLON-60"
    var causalHash = ""
    var soundName = "Ping"
    var playSound = true
    var anonymous = false
    var isPreview = false
    var signHex = ""

    var i = 1
    while i < args.count {
        let arg = args[i]
        if (arg == "--action" || arg == "--message" || arg == "-m") && i + 1 < args.count {
            action = args[i+1]
            i += 2
        } else if (arg == "--prompt" || arg == "--reason" || arg == "--detail" || arg == "-p") && i + 1 < args.count {
            prompt = args[i+1]
            i += 2
        } else if (arg == "--agent" || arg == "-a") && i + 1 < args.count {
            passedAgent = args[i+1]
            i += 2
        } else if (arg == "--scope" || arg == "-s") && i + 1 < args.count {
            scope = args[i+1]
            i += 2
        } else if arg == "--causal-hash" && i + 1 < args.count {
            causalHash = args[i+1]
            i += 2
        } else if arg == "--sound" && i + 1 < args.count {
            soundName = args[i+1]
            i += 2
        } else if arg == "--no-sound" || arg == "--silent" || arg == "--quiet" {
            playSound = false
            i += 1
        } else if arg == "--anonymous" {
            anonymous = true
            i += 1
                } else if arg == "--sign-hex" && i + 1 < args.count {
            signHex = args[i+1]
            i += 2
        } else if arg == "--preview" {
            isPreview = true
            i += 1
        } else {
            if action.isEmpty && !arg.hasPrefix("-") {
                action = arg
            }
            i += 1
        }
    }

    if args.contains("--sign-hex") && signHex.isEmpty {
        fputs("Invalid --sign-hex: expected nonempty hexadecimal.\n", stderr)
        exit(1)
    }

    if action.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
        action = "Aprobar mutación crítica"
    }

    // Auto-detección inteligente del entorno emisor + rol específico del agente
    let detectedEnv = detectCallingEnvironment()
    let env = ProcessInfo.processInfo.environment
    let specificAgent: String
    if !passedAgent.isEmpty && passedAgent != "MOSKV-1 (Ring-1)" {
        specificAgent = passedAgent
    } else if let e = env["C5_AGENT"] ?? env["AGENT_NAME"] ?? env["SUBAGENT_ROLE"] ?? env["AGENT_ROLE"] {
        specificAgent = e
    } else {
        specificAgent = "Pair Agent"
    }

    let finalAgent: String
    if specificAgent.contains(detectedEnv) {
        finalAgent = specificAgent
    } else {
        finalAgent = "\(detectedEnv) · \(specificAgent)"
    }

    var finalHash = causalHash.trimmingCharacters(in: .whitespacesAndNewlines)
    if finalHash.isEmpty || finalHash == "UNKNOWN" {
        if !isPreview {
            fputs("--causal-hash obligatorio para una atestación real.\n", stderr)
            exit(1)
        }
        let payload = "\(action)|\(prompt)|\(finalAgent)|\(scope)|\(Date().timeIntervalSince1970)"
        let digest = SHA256.hash(data: Data(payload.utf8))
        finalHash = digest.map { String(format: "%02x", $0) }.joined()
    }

    let shortHash: String
    if finalHash.count > 16 {
        shortHash = "\(finalHash.prefix(8))…\(finalHash.suffix(6))"
    } else {
        shortHash = finalHash
    }

    func wrapIndented(prefix: String, text: String, maxLine: Int = 38) -> [String] {
        let cleanText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if cleanText.isEmpty { return [] }
        if prefix.count + cleanText.count <= maxLine {
            return ["\(prefix)\(cleanText)"]
        }
        var lines: [String] = []
        let words = cleanText.components(separatedBy: " ")
        var current = ""
        let continuationPrefix = "│   "
        let maxFirstLine = maxLine - prefix.count
        let maxContinuation = maxLine - continuationPrefix.count
        
        for word in words {
            let limit = lines.isEmpty ? maxFirstLine : maxContinuation
            if current.isEmpty {
                current = word
            } else if current.count + word.count + 1 <= limit {
                current += " " + word
            } else {
                lines.append(lines.isEmpty ? "\(prefix)\(current)" : "\(continuationPrefix)\(current)")
                current = word
            }
        }
        if !current.isEmpty {
            lines.append(lines.isEmpty ? "\(prefix)\(current)" : "\(continuationPrefix)\(current)")
        }
        return lines
    }

    // Estructura visual: Origen primero para que Borja sepa INMEDIATAMENTE qué IA llama
    var reasonLines: [String] = []
    reasonLines.append("┌─ [C5-GATE · TOUCH ID]")
    reasonLines.append(contentsOf: wrapIndented(prefix: "├▸ Origen : ", text: finalAgent, maxLine: 38))
    reasonLines.append(contentsOf: wrapIndented(prefix: "├▸ Acción : ", text: action, maxLine: 38))
    if !prompt.isEmpty {
        reasonLines.append(contentsOf: wrapIndented(prefix: "├▸ Motivo : ", text: prompt, maxLine: 38))
    }
    if !scope.isEmpty {
        reasonLines.append(contentsOf: wrapIndented(prefix: "├▸ Ámbito : ", text: scope, maxLine: 38))
    }
    reasonLines.append("└▸ Causal : \(shortHash)")
    let reason = reasonLines.joined(separator: "\n")

    if isPreview {
        print("=== [C5-GATE MODAL PREVIEW] ===")
        print(reason)
        print("================================")
        exit(0)
    }

    let dataToSign: Data
    do {
        dataToSign = try signingContractPayload(causalHash: finalHash, signHex: signHex)
    } catch {
        fputs("Contrato causal inválido: \(error)\n", stderr)
        exit(1)
    }

    if playSound {
        DispatchQueue.global(qos: .userInteractive).async {
            if let sound = NSSound(named: NSSound.Name(soundName)) {
                sound.play()
            } else if let sound = NSSound(named: "Ping") {
                sound.play()
            }
        }
    }

    let sessionUser = ProcessInfo.processInfo.userName
    let fullUserName = NSFullUserName()

    let context = LAContext()
    context.touchIDAuthenticationAllowableReuseDuration = 0
    context.localizedFallbackTitle = ""
    context.localizedCancelTitle = "Rechazar"

    var error: NSError?
    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
        fputs("Biometría no disponible: \(error?.localizedDescription ?? "Error desconocido")\n", stderr)
        exit(1)
    }
    let policy: LAPolicy = .deviceOwnerAuthenticationWithBiometrics
    DispatchQueue.main.asyncAfter(deadline: .now() + 30) {
        context.invalidate()
        fputs("Plazo biométrico agotado; operación abortada.\n", stderr)
        exit(1)
    }

    context.evaluatePolicy(policy, localizedReason: reason) { success, evaluateError in
        if success {
            do {
                guard let accessControl = SecAccessControlCreateWithFlags(
                    nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                    [.privateKeyUsage, .biometryCurrentSet], nil
                ) else { throw SigningContractError.unavailableAccessControl }

                let keyPath: String
                if let envPath = ProcessInfo.processInfo.environment["BABYLON_ENCLAVE_KEY_PATH"] {
                    keyPath = envPath
                } else {
                    let home = FileManager.default.homeDirectoryForCurrentUser.path
                    let cortexDir = (home as NSString).appendingPathComponent(".config/cortex")
                    try FileManager.default.createDirectory(atPath: cortexDir, withIntermediateDirectories: true)
                    keyPath = (cortexDir as NSString).appendingPathComponent("enclave_p256.key")
                }

                let privateKey: SecureEnclave.P256.Signing.PrivateKey
                if FileManager.default.fileExists(atPath: keyPath) {
                    let record = try Data(contentsOf: URL(fileURLWithPath: keyPath))
                    privateKey = try SecureEnclave.P256.Signing.PrivateKey(
                        dataRepresentation: try recordedBiometricKey(record),
                        authenticationContext: context
                    )
                } else {
                    let key = try SecureEnclave.P256.Signing.PrivateKey(
                        compactRepresentable: false, accessControl: accessControl,
                        authenticationContext: context
                    )
                    try persistBiometricKey(key.dataRepresentation, at: keyPath)
                    privateKey = key
                }

                let signature = try privateKey.signature(for: dataToSign)
                guard privateKey.publicKey.isValidSignature(signature, for: dataToSign) else {
                    throw SigningContractError.invalidSignature
                }
                let sigBase64 = signature.derRepresentation.base64EncodedString()
                let pubKeyBase64 = privateKey.publicKey.x963Representation.base64EncodedString()
                
                let userField = anonymous ? "null" : "\"\(sessionUser)\""
                let fullNameField = anonymous ? "null" : "\"\(fullUserName)\""
                let promptField = prompt.isEmpty ? "null" : "\"\(prompt.replacingOccurrences(of: "\"", with: "\\\""))\""

                let jsonResponse = """
                {
                    "status": "ATTESTED",
                    "operator_user": \(userField),
                    "operator_name": \(fullNameField),
                    "causal_hash": "\(finalHash)",
                    "short_hash": "\(shortHash)",
                    "action": "\(action.replacingOccurrences(of: "\"", with: "\\\""))",
                    "prompt": \(promptField),
                    "scope": "\(scope.replacingOccurrences(of: "\"", with: "\\\""))",
                    "agent": "\(finalAgent.replacingOccurrences(of: "\"", with: "\\\""))",
                    "secure_enclave_signature": "\(sigBase64)",
                    "public_key": "\(pubKeyBase64)",
                    "timestamp": \(Date().timeIntervalSince1970)
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

    RunLoop.main.run()
}

#if !BIOMETRIC_CONTRACT_TEST
main()
#endif
