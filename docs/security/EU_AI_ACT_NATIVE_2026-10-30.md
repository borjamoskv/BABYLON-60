# Validación nativa local de Secure Enclave

La validación real del backend local ha terminado con **VERIFIED**. Se conserva la clave existente, se fija su clave pública antes de firmar y se verifica un desafío único mediante un verificador independiente del código Rust. El usuario ha elegido conectar el expediente más adelante: no se provisionan revisores ni se crea un expediente.

## Instalación preparada

Directorio: `~/.babylon60/regulatory/native-20261030T024520Z`, accesible también mediante `~/.babylon60/regulatory/current`.

| Componente | Estado |
| --- | --- |
| `babylon60_regulatory_gate` | Binario local compilado sin `test_mock_hardware`, fijado por SHA-256 |
| `c5_biometric_gate` | Helper Swift compilado desde la fuente revisada, fijado por SHA-256 |
| `operator-policy.json` | `native_validation.status: VERIFIED`; cero revisores; perfil de publicación `unconfigured` |
| `l0.sqlite` | Esquema inicializado; cero hechos y cero transiciones |
| `regulatory-cli` | Punto de entrada comprobado; carga la política, binario y ledger de esta instalación |

```bash
~/.babylon60/regulatory/current/regulatory-cli --help
```

El comando protegido sin perfil ni expediente se rechaza antes de solicitar biometría. Para continuar se necesitan un perfil real, las autoridades de revisión y su expediente. La publicación sigue sin estar autorizada.

## Evidencia de hardware

Se inspeccionó la clave pública del registro existente mediante `CryptoKit.SecureEnclave.P256.Signing.PrivateKey`, sin modificarlo ni solicitar autenticación. La huella SHA-256 de la clave pública SEC1 es `fd7e4f541f712d8ed5d717ae2fdc3df71807e97b130f1d375d3b964120845c4a`. La clave se fijó en la política externa antes del desafío.

La única solicitud biométrica utilizó contexto nuevo, reutilización cero, biometría sin autenticación alternativa y plazo acotado. El helper nativo firmó el desafío; Rust verificó el resultado y Python cryptography verificó independientemente ECDSA P-256/SHA-256 sobre los mismos bytes canónicos. Se comprobó que el desafío contiene el nonce esperado y los digests del binario y backend.

Comprobación completada a las `2026-10-30T02:50:48Z`.

- Binario Rust: `9163e5ad9b0626e3970cb0c082b63d81fd99370e872007714c4f2c4b5daa3ea2`.
- Configuración del backend: `ab7e4bcbc006857e9e2b2935c906dc1490659afc4bc1ecfaffdd9354d4112d52`.
- Evidencia independiente completa: `3eda8102d2e59190285de8d76c461665b023ca2cd94406ea2478fe986d3d6bd2`.

El informe completo está en `~/.babylon60/regulatory/current/validation/verification.json`. El registro de proceso y la inspección pública se conservan al lado. La [respuesta firmada pública](evidence/regulatory-native-20261030/challenge.json) permite reproducir la comprobación criptográfica sin otra solicitud de autenticación. Es evidencia histórica; no sustituye la validación de otra instalación o binario.

Las comprobaciones posteriores rechazaron cambios de nonce, binario, backend, finalidad, firma, clave y declaración de autorización. No se creó un ledger durante el desafío; la inicialización posterior del ledger vacío fue una operación separada. El registro de clave permaneció idéntico.

La firma acredita esta comprobación local. No proporciona una medición PCR ni atestación remota del código: `measurement_status` sigue siendo `UNAVAILABLE`. La integridad del helper, política, cuenta local y sistema operativo forma parte del entorno de confianza. La documentación de [Apple sobre claves en Secure Enclave](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave) describe el mecanismo utilizado.

## Cierre de Clippy y límites

El aviso previo de `src/flash_defense.rs` ya estaba corregido en el árbol vigente al iniciar esta continuación. Se verificó `cargo clippy --locked --bin babylon60_regulatory_gate -- -D warnings` sin exclusiones, con resultado correcto. No se volvió a modificar ese archivo.

La comprobación ampliada detectó `clippy::type_complexity` en una prueba de `src/omega_mediation.rs`. Se sustituyó la anotación compleja por un alias local de tipo, sin cambiar la prueba ni su comportamiento. Después, `cargo clippy --locked --all-targets -- -D warnings` pasó sin exclusiones y la regresión `every_signed_field_is_bound` pasó con `--locked`.

| Comprobación final | Resultado |
| --- | --- |
| Batería Python de evaluación, recibos, CLI, publicación y contrato biométrico | 161 pruebas correctas, sin omisiones |
| Ring-0 con mocks limitados a pruebas | 25 pruebas correctas |
| Regresión del alias de tipo corregido | 1 prueba correcta |
| Ruff de archivos Python afectados | Correcto |
| Actionlint de CI y publicación | Correcto |
| Semántica documental, presupuesto y topología | Correctos; alcance workspace, sin telemetría global de listeners |
| Firma real y siete alteraciones comprobadas sin otra autenticación | Firma válida; todas las alteraciones rechazadas |

La batería incluye `tests/test_regulatory_native_validation.py`, que vuelve a verificar el desafío histórico y sus alteraciones sin invocar hardware. Su ejecución no certifica por sí sola el estado actual del enclave.

La validación no aprueba ningún sistema ni acredita conformidad jurídica. No se ha publicado, no se ha configurado Production remoto y no se ha emitido una autorización de publicación. El [informe inicial](EU_AI_ACT_GATE_2026-10-30.md) conserva el estado anterior; este documento registra el cierre del pendiente hardware para esta instalación local.
