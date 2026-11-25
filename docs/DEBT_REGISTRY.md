# Registro canónico de deuda técnica (DEBT_REGISTRY)

> **BABYLON-60 — Consolidación de enjambre (2026-11-09)**  
> Registro unificado de deudas técnicas, compromisos abiertos y estado de verificación causal.

| ID | Estado | Alcance | Evidencia / Seguimiento |
| --- | --- | --- | --- |
| **TD-RING0-001** | **Parcial** (Opción B cerrada; A y C abiertas) | Tests de `LinuxTpm2Gate` y `AwsNitroEnclaveGate` sin dispositivo | `cargo test --locked --lib ring0::wire::golden` (8 tests sin hardware) |
| **TD-RING0-002** | **Cerrada** | Taxonomía dual de términos Ring-N (confinamiento vs organización) | Aclaración formal en `docs/03_guides/agent_contracts.md` |
| **TD-RING0-003** | **Abierta** | Defecto de binding PCR0 en `AwsNitroEnclaveGate` (`pcr0_measurement` preconfigurado devuelto sin parsear documento CBOR) | Diagnosticado en `docs/04_audit/deuda_tecnica_t01_ring0_linux_gates.md`; `CLAIM-RING0-011` acotado a encoding |
| **TD-RING0-004** | **Abierta** | `parse_quote_response` vive bajo `#[cfg(target_os = "linux")]` en `src/ring0.rs`, impidiendo ejecución de sus tests en macOS | Requiere mover parser a `src/ring0/wire.rs` o seam sin `target_os` para testear en darwin |
| **TD-REL-001** | **Abierta** | `RELEASE_MANIFEST.json.ots` (recibo OpenTimestamps de 3.983 B) queda desincronizado al regenerar el manifiesto local | Requiere atestación OTS con red pública tras cierre de ciclo de release formal |
| **TD-GIT-001** | **Abierta** | Triaje de la rama divergente `feat/cognitive-pilot-v4` (32 commits sin equivalente en main, divergencia desde 2026-10-26) | Seguimiento asíncrono; fuera del lote de consolidación de enjambre 08-09/11 |

---

## Detalle de Deudas Técnicas

### TD-RING0-001: Arnés de prueba para Gates Linux sin hardware
- **Opción B (golden vectors): CERRADA.** Los encoders viven en `src/ring0/wire.rs`, sin `cfg(target_os)`; los vectores de `TPM2_Quote` (73 B) y NSM `Attestation` CBOR (73 B) son bit-exactos. Respaldan CLAIM-RING0-010 y CLAIM-RING0-011 (solo codificación).
- **Opción A (swtpm + CI Linux): ABIERTA.** Requiere un seam para la ruta del dispositivo (hoy `/dev/tpmrm0` está fija en `src/ring0.rs`) y un runner Linux con `tpm_vtpm_proxy`. Cubre `open()`, la ida y vuelta de `TPM2_Quote`, el parseo de `TPMS_ATTEST` y la cadena del AK.
- **Opción C (mock-nsm / runner Nitro): ABIERTA.** Requiere un seam equivalente para `/dev/nsm`. Cubre el `ioctl`, el parseo de la respuesta y el enlace de PCR0.
- Hasta cerrar A y C, los dos claims permanecen `experimental` con `required_for_release = false`.

### TD-RING0-002: Desambiguación de Taxonomía Ring-N
- **CERRADA.** Documentada en `docs/03_guides/agent_contracts.md`. Distingue estrictamente entre:
  1. *Taxonomía de ejecución/confinamiento:* Ring-0 (C-ABI/Rust lock-free) → Ring-1 (formal Lean 4/Z3) → Ring-2 (CI/batch) → Ring-3 (UI/docs).
  2. *Taxonomía organizacional de módulos:* Ring-0 (`00_ABZU_KERNEL`) → Ring-1 (`01_KISH_ENGINE`) → Ring-2 (`02_EDIN_SWARMS`).

### TD-RING0-003: Binding PCR0 en AWS Nitro Enclaves
- **ABIERTA.** En `AwsNitroEnclaveGate::attest_transition` (`src/ring0.rs`), el retorno inyecta `pcr_or_enclave_measurement: self.pcr0_measurement` (valor estático configurado en `open`), en lugar de decodificar el documento de atestación COSE devuelto por `/dev/nsm` y validar el hash de PCR0.
- Mientras no exista un parser CBOR/COSE para el payload de respuesta de Nitro, `CLAIM-RING0-011` queda restringido formalmente a la codificación de la petición.

### TD-RING0-004: Portabilidad de Tests de Parseo TPM2_Quote
- **ABIERTA.** La función `parse_quote_response` fue implementada e integrada en `src/ring0.rs` resolviendo el defecto de binding en TPM 2.0 (ahora valida `extraData == causal_digest`, `pcrDigest == expected_pcr`, y extrae la firma ECDSA real).
- Sin embargo, tanto la función como sus 3 tests (`tpm2_quote_response_golden_vector_parses`, `tpm2_quote_response_fails_closed`, `tpm2_quote_response_rejects_other_digest_or_pcr`) están confinados a `#[cfg(target_os = "linux")]`. Para ejecutarse en macOS durante CI local, deben trasladarse a `src/ring0/wire.rs`.

### TD-REL-001: Recibo OpenTimestamps post-consolidación
- **ABIERTA.** La actualización de `CLAIMS.toml` y posterior re-compilación del manifiesto de release modifica el hash SHA-256 de `RELEASE_MANIFEST.json`. El archivo `RELEASE_MANIFEST.json.ots` existente corresponde a la versión previa congelada. Se requiere un nuevo timestamping criptográfico tras la validación final del ciclo.

### TD-GIT-001: Triaje de rama histórica feat/cognitive-pilot-v4
- **ABIERTA.** La rama `feat/cognitive-pilot-v4` contiene 32 commits sobre el piloto cognitivo v4 iniciados el 2026-10-26. No forma parte de la dispersión de enjambre de Ring-0/seguridad del 08-09 de noviembre. Queda pendiente para un ciclo de auditoría cognitiva independiente.
