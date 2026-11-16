# Contrato de ejecución — Lote 3

Resultado: cerrar C0413 y C0418 mediante rechazo explícito y SW100-R3-0001
mediante despacho del objeto inmutable ligado al destino autorizado.
Únicas fuentes productivas: scripts/c5_git_utils/c5_distill_public_mirror.sh y
scripts/c5_git_utils/c5_ship.sh. Se permiten tests, evidencia y registro.

Aceptación: reproducciones previas en fixtures, rechazos sin efecto observable,
snapshot de blobs completo, referencia/destino/configuración congelados, hash
SHA-256 del efecto y recibo conforme al gate existente; revisión independiente,
pytest dirigido, bash -n, ShellCheck y controles documentales.

Contratos aplicados: Ring-0 (atestación, hash, rechazo, replay), Ring-1 (PoC de
concurrencia), Ring-2 (Git, lockfiles, revisión) y Ring-3 (shell/documentos).
No ejecutar Git remoto, commits, merges, Swift o biometría reales. No fabricar
ATTESTED. Los publicadores de test son registros sin red ni efectos protegidos.
La integración Secure Enclave y el push real quedan NO_VERIFICADOS.
Codebase-memory no está expuesto en esta sesión; descubrimiento acotado por rg.
