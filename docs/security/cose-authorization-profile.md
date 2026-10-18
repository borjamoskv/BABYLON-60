# Perfil COSE de autorización del executor

Este documento fija el perfil que acepta `SignedAuthorization`. La implementación es deliberadamente más estrecha que COSE en general; recibos y otros mensajes pueden definir perfiles distintos.

## Estructura aceptada

- El envelope es `COSE_Sign1` con payload embebido.
- La cabecera protegida contiene el algoritmo (`EdDSA` o `ES256`) y `kid`.
- `kid` debe coincidir byte por byte con la clave pública admitida por la política. No se acepta `kid` en la cabecera no protegida ni una segunda copia ambigua.
- El algoritmo y `kid` no pueden ser sustituidos por campos no protegidos. Los parámetros `crit` no se aceptan hasta que el executor implemente y verifique explícitamente su semántica.
- El payload es el registro de longitud fija de 214 bytes, con los campos en el orden y endianness definidos por `AuthorizationPayload::to_canonical_bytes`.
- `expires_at` es el límite superior exclusivo: la autorización caduca cuando `now >= expires_at`.

La firma se verifica antes de comparar el payload con la intención, la política y el estado del recurso. Una entrada que no cumple este perfil falla cerrada como `MalformedAuthorization` o con el error criptográfico correspondiente.

## Regresiones

La suite cubre firma válida y corrupta, payload ausente o de longitud incorrecta, `kid` solo no protegido, `kid` duplicado/conflictivo y encabezados críticos no soportados. Las entradas rechazadas deben fallar antes de reservar el nonce o aplicar el efecto. La cobertura criptográfica existente incluye las rutas Ed25519 y P-256.
