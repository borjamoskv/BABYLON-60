# Autorización de una solicitud concreta

`babylon60 approve` solicita una firma biométrica de la solicitud completa. Un
registro `APPROVED` escrito directamente en SQLite no concede permisos. Los
registros anteriores sin evidencia firmada siguen disponibles para auditoría,
pero requieren una autorización nueva para ejecutar acciones críticas.

Antes de aprobar, el operador debe provisionar `BABYLON_ENCLAVE_PINNED_PUBKEY`
con su clave pública P-256 de confianza, en hexadecimal o Base64 (SEC1/X9.63 o
SPKI DER). La clave debe obtenerse y verificarse por un canal de confianza; copiar
la clave que devuelve una solicitud desconocida no establece identidad. Una firma
válida demuestra posesión de esa clave. Su procedencia hardware depende del
provisionamiento del operador y no se demuestra con las pruebas de software.

Guarda exactamente el objeto que evaluará el consumidor en `task.json`, incluidos
el comando, parámetros y destino si forman parte de la tarea:

```json
{"execution_id":"deploy-001","action":"deploy","command":"deploy staging","parameters":{"target":"staging"}}
```

```sh
babylon60 approve deploy-001 --task-file task.json --db /ruta/causal_gate.db
babylon60 approve deploy-001 --decision REJECTED --db /ruta/causal_gate.db
```

La firma liga todos los campos, una caducidad máxima de 300 segundos y un nonce.
Cambiar el identificador, la acción, el comando o los parámetros invalida el
permiso. La denegación revoca la aprobación anterior para ese identificador.
`--risk` se conserva por compatibilidad y no permite degradar el requisito de
firma. No hay una autorización global de bifurcación; el consumidor debe pasar
la tarea concreta. `is_allowed` comprueba permisos; no consume una autorización
ni ejecuta una operación. El control de un único uso del executor Rust sigue
siendo independiente.

El helper firma los bytes recibidos mediante `--sign-hex`; `--causal-hash` contiene
su prehash SHA-256 para P-256. CLI, gateway y adaptador Rust verifican la firma,
la clave provisionada y la correspondencia del hash. Una salida vacía, una salida
de éxito sin evidencia o un error de biometría no autorizan la solicitud. No hay
reintentos automáticos. El gateway solo comprueba un desafío local y no autoriza
una transacción del executor.

El servicio `babylon_authorityd` exige una clave Ed25519 explícita mediante
`BABYLON_AUTHORITY_ED25519_SEED` y una política cuya autoridad coincida con ella.
No existe clave de respaldo. Este servicio de firma de política no certifica
biometría y su clave privada debe provisionarse fuera del cliente proponente.
Una instalación que utilizara la antigua clave pública de respaldo debe revocar
esa autoridad en su política antes de volver a prestar servicio.

La distribución soportada es terminal/MCP. Desde un checkout limpio o un paquete
descomprimido, `bash install.sh --dry-run` verifica los archivos sin instalar;
`bash install.sh` instala las dependencias bloqueadas y muestra la ayuda de la
CLI. `bash install.sh --mcp` inicia el servidor de memoria por stdio. El puente
del kernel descrito en `guide_kernel_mcp.md` necesita un checkout completo y su
entorno independiente. No se recuperan la interfaz web ni los instaladores de
doble clic.
