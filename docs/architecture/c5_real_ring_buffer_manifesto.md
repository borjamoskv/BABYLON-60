<!-- C5-REAL EXERGY CERTIFIED -->
# Del Código Fuente al Recibo SCITT: Un Buffer Circular Lock-Free para Auditoría Regulatoria bajo el Paradigma C5-REAL

Este informe de investigación detalla el diseño arquitectónico de un `RingBufferLockFree` en Rust, concebido para la transferencia de datos de texto entre un hilo productor en Python y un hilo consumidor en Rust. El sistema opera exclusivamente sobre memoria compartida atómica, evitando dependencias externas como PyO3, JSON o llamadas síncronas de red. La arquitectura propuesta está diseñada para cumplir con un conjunto riguroso de requisitos técnicos y regulatorios, abordando cuatro ejes fundamentales: especificación de la ABI y alineación de silicio, gestión de concurrencia en el modelo de memoria débil de AArch64, modelado formal y termodinámico, y generación de evidencia criptográfica conforme a la normativa europea. Cada componente del diseño ha sido meticulosamente analizado para asegurar la corrección, el rendimiento y la audibilidad, transformando el mecanismo de intercambio de datos en una frontera topológica inmutable.

## Especificación C-ABI y Alineación de Silicio a Línea de Caché (128 Bytes)

El primer pilar del diseño arquitectónico es la creación de una estructura de datos cuyo layout de memoria sea tanto eficiente como correcto en un entorno de múltiples hilos sobre procesadores AARCH64. El requisito fundamental es que toda la estructura de estado compartido debe estar alineada a una única línea de caché física del hardware objetivo para prevenir problemas de contención y corrupción de datos (*False Sharing*). Aunque en arquitecturas x86_64 el tamaño de la línea de caché es comúnmente de 64 bytes, en entornos de despliegue sobre silicio ARM de Apple (M1/M2/M3), la línea de caché L1 es estrictamente de 128 bytes. Cualquier acceso a memoria que cruce los límites de esta línea puede tener consecuencias severas. Cuando dos variables distintas residen en la misma línea de caché y son accedidas por diferentes núcleos de CPU, se produce un fenómeno conocido como *false sharing*. Esto provoca un ciclo de invalidación y refresco constante entre los núcleos, conocido como *cache-line ping-pong*, que consume ancho de banda de memoria y reduce drásticamente el rendimiento.

Para mitigar este problema y garantizar la corrección lógica del algoritmo lock-free, la estructura principal del buffer y sus metadatos clave deben ocupar un bloque de memoria de 128 bytes sin superposiciones ni particiones. El diseño debe acoplarse a un layout de memoria C-ABI alineado a una única línea de caché física (0x00 a 0x7F para Apple Silicon). Para alcanzar este objetivo en Rust, se emplea un mecanismo de atributos de representación (`repr`). El atributo `#[repr(C)]` asegura que los miembros de la estructura se dispongan en memoria secuencialmente, siguiendo las reglas de alineación de C, creando un contrato predecible para el mundo exterior. Complementariamente, el atributo `#[repr(align(128))]` fuerza al compilador a alinear la estructura resultante en una dirección de memoria que sea un múltiplo de 128, garantizando que comience en el principio de una nueva línea de caché L1 en entornos macOS, erradicando el riesgo de contención.

| Campo de la Estructura | Tipo de Dato | Tamaño (bytes) | Alineación (bytes) | Desplazamiento (hex) | Observaciones |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `status_flag` | `AtomicU32` | 4 | 4 | 0x00 | Bandera de estado atómica. |
| `active_readers` | `AtomicU32` | 4 | 4 | 0x04 | Conteo de lectores activos. |
| `epoch_id` | `AtomicU64` | 8 | 8 | 0x08 | ID de Época / Secuencia para el protocolo Seqlock. |
| `payload_hash` | `[u8; 32]` | 32 | 1 | 0x10 | Hash SHA-256 del payload (no atómico, requiere Seqlock). |
| `_padding` | `[u8; 80]` | 80 | 1 | 0x30 | Relleno explícito hasta alcanzar los 128 Bytes (0x7F). |

El relleno final asegura que la estructura total ocupe exactamente 128 bytes, cumpliendo así con la especificación C-ABI para Apple Silicon y eliminando el *false sharing* entre los punteros atómicos clave.

## Concurrencia Débil, Seqlock y Gestión de Memoria en el Modelo ARMv9

El segundo pilar del diseño se enfoca en la gestión de concurrencia en el modelo de memoria débil de la arquitectura AArch64. A diferencia de x86_64, ARMv9 permite reordenamientos de memoria agresivos para maximizar el rendimiento. Para cargas de datos masivas que exceden el tamaño de palabra atómica nativa (como el hash de 32 bytes), el sistema emplea obligatoriamente un patrón **Sequence Lock (Seqlock)** acoplado a semánticas `Acquire/Release` y barreras duras (`dmb ish`).

En este buffer circular SPSC (Single-Producer Single-Consumer), el productor escribe el array de 32 bytes de forma no atómica, pero encapsula la escritura incrementando el `epoch_id` a un valor impar antes de iniciar, emitiendo un `dmb ish`, y cerrando a un valor par (`Release`). El consumidor (Rust) carga la época (`Acquire`), verifica que es par, lee el hash, y re-verifica la época. Si el contador mutó durante la lectura, detecta un *torn read* y reintenta el bucle (spin-wait). Esta arquitectura elimina los bloqueos (mutexes) del sistema operativo, garantizando una latencia termodinámicamente óptima y estrictamente determinista.

## Modelado Formal y Termodinámico: De la Anergía a la Entelecheia

El sistema se modela como un Sistema de Transiciones Discretas sobre monoides no invertibles. El requisito de "Dependencia Cero en Recolección de Basura" es una restricción técnica fundamental que subraya la necesidad de un manejo de memoria explícito.

El "Estado Canónico" o "Entelecheia" representa la culminación exitosa de una transición: el productor ha depositado un hash válido en el manifiesto y el consumidor lo ha leído sin desgarrarse (Seqlock exitoso). El tiempo invertido en el spin-wait (esperando a que el contador sea par) representa la Disipación de Anergía bajo el límite de Landauer: el coste físico de purgar la estocástica del generador (LLM) y forzar un colapso determinista.

## Cumplimiento Regulatorio y Fail-Stop: El Recibo SCITT (RFC 9942)

El cuarto eje transforma el mecanismo de IPC en una entidad jurídicamente responsable frente a la EU AI Act (Arts. 12, 14, 15, y 50) y la Directiva de Responsabilidad 2024/2853. En lugar de un fallo silencioso, el buffer circular ejecuta un `EpistemicHalt`: una parada determinista anclada por un recibo SCITT (Suministro de Cadena de Integridad, Transparencia y Confianza).

El recibo SCITT generado por el sistema debe ser un artefacto estrictamente discreto y alineado al RFC 9942 (publicado en Junio 2026), según lo especificado:
1.  **En caso de transición exitosa (*Acto*):** El recibo debe contener el hash **SHA-256** (Algoritmo IANA COSE `-16`) de una representación canónica del estado del sistema (*Entelecheia*). Queda prohibido el uso de SHA3-256 por falta de registro oficial.
2.  **En caso de *EpistemicHalt* (*Cuarentena*):** El recibo ancla el defecto (ej. offset del puntero corrupto, violación de Seqlock), demostrando contención inmutable para neutralizar la presunción civil de defecto.

| Tipo de Evento | Contenido del Recibo SCITT | Propósito Legal / Regulatorio |
| :--- | :--- | :--- |
| **Operación Exitosa** | Hash SHA-256 (Alg. -16) del estado canónico del sistema. | Prueba de que el sistema operaba correctamente. Cumple con registro automático (Art. 12). |
| **EpistemicHalt (Fallo)** | Representación formal del fallo estructural. | Ancla el defecto. Cumple con la robustez y la comunicación de riesgos (Arts. 15, 28). |

Al integrar el estándar RFC 9942, el buffer circular se erige como la prueba pericial determinista que el paradigma C5-REAL exige para despliegues de Alto Riesgo.
