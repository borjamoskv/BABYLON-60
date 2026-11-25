# Deuda Técnica T-01: Ring-0 Linux Hardware Security Gates sin Atestación ni Verificación PCR

> **Nota de Consolidación (2026-11-09):** Este documento se conserva como registro causal del diagnóstico inicial.
> La gestión y seguimiento de esta deuda técnica está centralizada en [`DEBT_REGISTRY.md`](../DEBT_REGISTRY.md):
> - **TD-RING0-001 (Golden vectors de codificación):** CERRADA (Opción B) vía `src/ring0/wire.rs`. Opciones A (`swtpm`) y C (`mock-nsm`) permanecen ABIERTAS.
> - **TD-RING0-002 (Taxonomía de anillos Ring-N):** CERRADA vía aclaración en `agent_contracts.md`.
> - **TD-RING0-003 (Binding PCR en Nitro):** ABIERTA.
> - **Corrección Binding PCR TPM2:** RESUELTA e integrada en `src/ring0.rs` vía `parse_quote_response` (fail-closed, enlace causal y PCR real atestado).

**Fecha:** 2026-11-08  
**Severidad:** MEDIO  
**Componente:** `00_ABZU_KERNEL` / `src/ring0.rs`  
**Claims Asociados:** `CLAIM-RING0-010`, `CLAIM-RING0-011`  
**Estado:** REGISTRADO (Parcialmente mitigado / Seguimiento en DEBT_REGISTRY.md)

---

## 1. Contexto y Diagnóstico Causal

En `src/ring0.rs`, la arquitectura de compuertas hardware (`HardwareSecurityGate`) define tres backends de producción bajo directivas de compilación condicional:
1. `AppleSecureEnclaveGate` (`#[cfg(target_os = "macos")]`): Puente al Secure Enclave y Touch ID.
2. `LinuxTpm2Gate` (`#[cfg(target_os = "linux")]`, L248–L380): Comunicación directa con el Kernel Resource Manager (`/dev/tpmrm0`), construyendo tramas binarias `TPM2_Quote` (73 B, PCR 0/7/14 en banco SHA-256).
3. `AwsNitroEnclaveGate` (`#[cfg(target_os = "linux")]`, L385–L508): Comunicación vía ioctl (`_IOWR(0x0A, 0)`) con `/dev/nsm`, codificando peticiones `Attestation` en CBOR estático (73 B sin heap).

### Hallazgo 1: Brecha Código vs. Evidencia
A diferencia del backend macOS (respaldado por la campaña adversarial `tests/omega_mediation_campaign.rs`; la referencia previa a `tests/nemesis_wave_auth_ipc.py` apuntaba a un archivo que no existe en el repositorio), los dos backends Linux carecen de:
- Pruebas unitarias de codificación y decodificación de tramas binarias.
- Pruebas de integración o arnés con emuladores (`tpm2-abrmd`, `swtpm`, o mocks de `/dev/nsm`).
- Registro previo en el manifiesto epistémico `CLAIMS.toml`.
- La suite de tests en `src/ring0_tests.rs` se ejecuta exclusivamente sobre `MockHardwareGate` (bajo feature `test_mock_hardware`).

### Hallazgo 2: Defecto de Correctitud en Binding PCR (Falsa Atestación)
En ambos gates Linux, el método `attest_transition` lee la respuesta cruda del dispositivo para extraer la firma criptográfica (últimos 64 bytes), pero **no parsea ni verifica la estructura de medición PCR devuelta por el silicio**:
- En `LinuxTpm2Gate` (`src/ring0.rs:376`):
  ```rust
  Ok(HardwareReceipt {
      signature,
      public_key_id: self.ak_pubkey_id,
      pcr_or_enclave_measurement: self.expected_pcr_composite, // <-- Inyecta valor preconfigurado
  })
  ```
- En `AwsNitroEnclaveGate` (`src/ring0.rs:504`):
  ```rust
  Ok(HardwareReceipt {
      signature,
      public_key_id: self.enclave_key_id,
      pcr_or_enclave_measurement: self.pcr0_measurement, // <-- Inyecta valor preconfigurado
  })
  ```

**Impacto:** El recibo hardware emitido no demuestra que el firmware o los PCR del anfitrión coincidan con el estado esperado; simplemente reenvía el valor configurado estáticamente durante `open()`. Si un anfitrión arranca con un estado adulterado o una imagen distinta, la firma de la clave AK/Enclave se genera sobre el digest causal, pero la raíz Merkle y el ledger no quedan vinculados a la medición real observada por el hardware en el instante del salto de época.

---

## 2. Invariantes Afectadas

- **INV-OMEGA:** `Executed(e) => Authorized(e) & SignatureValid(e) & PolicyValid(e) & Fresh(e)`
- **INV_C5_HUME_GUILLOTINE:** Prohibido declarar verificado en silicio (`ATTESTED_IN_SILICON`) aquello que en tiempo de ejecución solo devuelve una constante o mock configurado.
- **INV_C5_ONWIRE_CANON:** Todo recibo debe contener evidencia criptográficamente vinculada al estado empírico del sustrato.

---

## 3. Registro de Claims en `CLAIMS.toml`

Se incorporan al manifiesto formal las siguientes entradas con estatus estrictamente `experimental`:

```toml
[claim.ring0_linux_tpm2_gate]
claim_id = "CLAIM-RING0-010"
statement = "LinuxTpm2Gate construye TPM2_Quote con qualifyingData=digest causal y PCR 0/7/14 en /dev/tpmrm0; atestación hardware no verificada en producción"
evidence = "cargo test --locked --lib ring0::linux_tpm2 --features cortex-persist"
status = "experimental"
evidence_level = "L2_IMPLEMENTATION"
component = "00_ABZU_KERNEL"
notes = "Deuda T-01: Sin harness de prueba unitaria ni de integración con TPM emulator (tpm2-abrmd/QEMU). Defecto de binding PCR en src/ring0.rs:376 donde pcr_or_enclave_measurement devuelve expected_pcr_composite (configurado) en vez de parsear y verificar los PCR reales de la respuesta del hardware."

[claim.ring0_aws_nitro_gate]
claim_id = "CLAIM-RING0-011"
statement = "AwsNitroEnclaveGate codifica petición Attestation CBOR (73 B) y consume ioctl en /dev/nsm; atestación hardware no verificada en producción"
evidence = "cargo test --locked --lib ring0::aws_nitro --features cortex-persist"
status = "experimental"
evidence_level = "L2_IMPLEMENTATION"
component = "00_ABZU_KERNEL"
notes = "Deuda T-01: Sin harness de prueba unitaria ni mock de driver /dev/nsm. Defecto de binding PCR en src/ring0.rs:504 donde pcr_or_enclave_measurement devuelve pcr0_measurement (configurado) en vez de parsear y verificar la medición real del documento de atestación Nitro."
```

---

## 4. Plan de Cierre y Verificación (Condición de Salida)

Para transicionar `CLAIM-RING0-010` y `CLAIM-RING0-011` de `experimental` a `verified_local`:
1. **Parser de `TPMS_ATTEST`:** Implementar extractor zero-alloc en `src/ring0.rs` que lea la estructura `TPM2B_ATTEST` retornada por `TPM2_Quote`, verifique el magic `TPM_GENERATED_VALUE` (0xFF544347), valide que `extraData` coincida con el digest causal, extraiga la lista de PCRs medidos y confirme coincidencia con `expected_pcr_composite`.
2. **Parser de Documento Nitro (COSE/CBOR):** Implementar decodificador CBOR estricto sin heap para extraer el mapa de PCRs del documento firmado por la clave de AWS Nitro Enclave.
3. **Arnés de Pruebas Mock / Emulador:**
   - Añadir tests unitarios que alimenten respuestas binarias grabadas (golden vectors de TPM 2.0 y Nitro Enclave) a funciones de validación aisladas.
   - Habilitar target CI en Linux utilizando `swtpm` o contenedor Docker con soporte TPM emulado.
