// SOFTWARE_ONLY: production helpers, software key, no call to main()/Touch ID.
import Foundation
import CryptoKit

func check(_ value: Bool) { precondition(value) }
func rejects(_ operation: () throws -> Void) {
    do { try operation(); fatalError("Malformed input accepted") } catch { }
}
do {
    if CommandLine.arguments.count > 1 {
        let args=CommandLine.arguments
        guard let hi=args.firstIndex(of: "--causal-hash"), hi+1<args.count,
              let pi=args.firstIndex(of: "--sign-hex"), pi+1<args.count else {
            throw SigningContractError.invalidHex
        }
        let hash=args[hi+1]
        let data=try signingContractPayload(causalHash: hash, signHex: args[pi+1])
        let key=try P256.Signing.PrivateKey(rawRepresentation: Data(repeating: 7,count: 32))
        let signature=try key.signature(for: data)
        print("""
        {"status":"ATTESTED","test_source":"SOFTWARE_ONLY","causal_hash":"\(hash)","public_key":"\(key.publicKey.x963Representation.base64EncodedString())","secure_enclave_signature":"\(signature.derRepresentation.base64EncodedString())"}
        """)
    } else {
        let data=Data([0,1,127,128,254,255])
        let hex=data.map {String(format:"%02x",$0)}.joined()
        let hash=SHA256.hash(data:data).map {String(format:"%02x",$0)}.joined()
        check(try strictSigningHex(hex)==data)
        check(try strictSigningHex(hex.uppercased())==data)
        for bad in ["","0","xyz","00 01","٠١","0g"] { rejects { _=try strictSigningHex(bad) } }
        rejects { _=try signingContractPayload(causalHash:"abc",signHex:hex) }
        rejects { _=try recordedBiometricKey(Data([1,2,3])) }
        for version in [1,3] {
            let record=try JSONEncoder().encode(BiometricKeyRecord(version:version,keyData:data))
            rejects { _=try recordedBiometricKey(record) }
        }
        let record=try JSONEncoder().encode(BiometricKeyRecord(version:2,keyData:data))
        check(try recordedBiometricKey(record)==data)
        for _ in 0..<64 { _=try signingContractPayload(causalHash:hash,signHex:hex) }
        for _ in 0..<512 {
            check(try signingContractPayload(causalHash:hash,signHex:hex)==data)
            rejects { _=try signingContractPayload(causalHash:hash,signHex:"ff") }
        }
        print("PASS: software-only Swift signing contract")
    }
} catch {
    fputs("Signing contract rejected: \(error)\n",stderr)
    exit(2)
}
