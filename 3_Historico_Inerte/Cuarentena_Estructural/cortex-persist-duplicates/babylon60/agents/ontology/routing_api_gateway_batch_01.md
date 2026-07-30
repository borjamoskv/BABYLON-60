# ONTOLOGY-FORGE-OMEGA: API GATEWAY, ROUTING & COMMUNICATIONS (BATCH 1)
**Dominio:** Ruteo de Eventos, API Gateway (FastAPI), Comunicaciones Inter-Agente y Tunnels en C5-REAL
**Sys_ID:** `borjamoskv` | **Estado:** C5-REAL

## MATRIZ 1: 20 PRIMITIVAS DE COLAPSO (RTE-P01..20)
Mecanismos elementales de fallo de red, colisión de rutas y fugas en la capa de transporte API.

| ID | Primitiva | Mecanismo Causal | Activación (Trigger) | Sensor (Síntoma) | Escala Temporal | Gravedad | Intervención |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **RTE-P01** | `OP_GIL_BLOCK_ROUTE` | Bloqueo del event loop de FastAPI debido a llamada síncrona de I/O en la ruta. | Uso de `requests.get` o `time.sleep` en ruta ordinaria. | Caída en picado del throughput / Latencia > 2s. | MS | P0 | Refactorizar ruta a asíncrona (`async def`) nativa. |
| **RTE-P02** | `OP_SCHEMA_MISMATCH` | Falla en validación de esquema en la petición entrante del API. | Estructura JSON no cumple con el modelo Pydantic. | Status Code 422 Unprocessable Entity en responses. | MS | P1 | Validar esquema en el cliente antes de la transmisión. |
| **RTE-P03** | `OP_ROUTING_LOOP` | Bucle de redirección circular de eventos entre subagentes del Swarm. | Configuración de topología de eventos cíclica sin control de TTL. | Desborde de pila de llamadas / Uso de CPU al 100%. | Segundos | P0 | Inyectar decrementador de Max-Hops en cabecera. |
| **RTE-P04** | `OP_HEADER_STRIP` | Pérdida de token de procedencia durante stripping de cabeceras HTTP. | Reverse proxy mal configurado elimina cabeceras personalizadas. | Campo `CORTEX-TAINT` ausente en el JSON de backend. | MS | P0 | Forzar inclusión de firma en payload encriptado principal. |
| **RTE-P05** | `OP_CROSS_QUERY` | Acceso cruzado no autorizado a endpoints de distintos inquilinos (tenants). | Ruta carece de binding de validación de tenant_id. | Datos expuestos de Tenant B en respuesta a Tenant A. | O(1) | P0 | Middleware de autorización a nivel de Edge API. |
| **RTE-P06** | `OP_PORT_CLASH` | Colisión de puertos locales al inicializar el servidor web o proxy local. | Puerto predefinido ya ocupado por otro proceso del host. | `OSError: [Errno 98] Address already in use`. | O(1) | P1 | Asignación de puerto dinámica con validación previa. |
| **RTE-P07** | `OP_CONN_DROP` | Cierre inesperado del socket por timeout del proxy keep-alive. | Inferencia de backend excede el tiempo máximo de inactividad de red. | `ConnectionResetError` o HTTP status 504 Gateway Timeout. | Segundos | P1 | Habilitar respuestas parciales (streaming chunks) o polling. |
| **RTE-P08** | `OP_BODY_OVERFLOW` | Desbordamiento de memoria por envío de payloads de petición gigantescos. | Carga de base de datos completa en crudo a través del endpoint REST. | `MemoryError` o crash del proceso de FastAPI. | MS | P0 | Establecer limitación de tamaño de petición en 10MB. |
| **RTE-P09** | `OP_CORS_EXPLOIT` | Exposición de endpoints locales a orígenes web maliciosos. | Configuración accidental de CORS con wildcard asterisco `*`. | Cabecera `Access-Control-Allow-Origin: *` en producción. | Continua | P0 | Configuración CORS restrictiva acotada a hosts locales. |
| **RTE-P10** | `OP_LIMITER_LOCK` | Bloqueo por rate limiter a peticiones legítimas del Swarm distribuido. | Configuración de límites por IP demasiado agresiva. | HTTP Status 429 Too Many Requests en inter-comunicaciones. | Segundos | P1 | Whitelist de IPs locales y balanceo asíncrono. |
| **RTE-P11** | `OP_TLS_HANDSHAKE` | Falla al establecer túnel seguro entre agentes debido a certificados corruptos. | Expiración o desalineación de la CA raíz local del enjambre. | `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`. | MS | P0 | Auto-renovación de certificados CA locales en bootstrap. |
| **RTE-P12** | `OP_API_VERSION_GAP` | Ruptura de compatibilidad entre versiones del contrato de la API REST. | Despliegue asíncrono de nodos con diferentes versiones de ruta. | HTTP Status 404 Not Found en endpoints deprecados. | Continua | P1 | Versionado estricto en la URL `/api/v1/...`. |
| **RTE-P13** | `OP_STACK_LEAK` | Exposición de secretos y rutas físicas en respuestas de error de la API. | Error de ejecución no capturado retorna stack trace raw a la UI. | Stack trace legible en el cuerpo de la respuesta HTTP 500. | O(1) | P0 | Capturador global de excepciones (FastAPI exception handler). |
| **RTE-P14** | `OP_SILENT_DEATH` | Caída silenciosa del API Gateway sin disparar alarmas de sistema. | Hilo principal colapsa pero puerto de red sigue escuchando (zombie). | Peticiones cuelgan indefinidamente (hang). | Minutos | P0 | Liveness probe externa comprobando endpoint `/health`. |
| **RTE-P15** | `OP_CACHE_DESYNC` | Servir datos obsoletos de configuración del Gateway debido a caché L1 fría. | Mutación en base de datos no propaga señal de purga a FastAPI. | Configuración de ruteo errónea tras actualización. | Minutos | P1 | Invalidador síncrono de caché en hooks de base de datos. |
| **RTE-P16** | `OP_HOST_SPOOF` | Desvío de peticiones (hijack) debido a suplantación de cabecera Host. | Reverse proxy acepta cualquier cabecera Host en la cabecera HTTP. | Redirección de peticiones locales a hosts externos. | MS | P0 | Middleware de validación de cabecera Host de lista blanca. |
| **RTE-P17** | `OP_PROXY_EXHAUST` | Agotamiento de sockets de salida en el proxy local de inferencia. | Creación continua de nuevos clientes HTTP sin reutilizar conexiones. | `Cannot assign requested address` en peticiones salientes. | Lenta | P1 | Compartir cliente HTTP único mediante `httpx.AsyncClient`. |
| **RTE-P18** | `OP_UVICORN_TIMEOUT`| Desconexión forzada por el servidor ASGI antes del procesado final. | `timeout-keep-alive` inferior al tiempo de respuesta de inferencia. | Response vacía con status nulo de red. | Segundos | P1 | Sintonización de parámetros ASGI a un TTL coherente. |
| **RTE-P19** | `OP_MIME_MISMATCH` | Falla en procesamiento de petición por tipo de medio no soportado. | Cliente envía payload codificado en XML o texto plano sin cabecera JSON. | Status Code 415 Unsupported Media Type. | MS | P2 | Forzar cabecera `Content-Type: application/json`. |
| **RTE-P20** | `OP_TABLE_POISON` | Envenenamiento de la tabla de ruteo dinámico de subagentes. | Inserción de ruta falsa por nodo comprometido. | Envío de datos sensibles a worker no autorizado. | Segundos | P0 | Tabla de ruteo inmutable y firmada digitalmente (BFT). |

## MATRIZ 2: 20 INVARIANTES TERMODINÁMICAS (RTE-I01..20)
Leyes del transporte de red y ruteo de información inmutable en el ecosistema.

| ID | Invariante | Lógica / Principio | Implicación Operacional | Condición de Borde | Métrica Falsable |
|:---|:---|:---|:---|:---|:---|
| **RTE-I01** | `INV_ASYNC_ROUTES` | Toda declaración de endpoint de FastAPI debe usar definición asíncrona. | Evita bloqueo del loop de eventos del Gateway. | Declaración de ruta en python. | `is_coroutine_function(route) == True`. |
| **RTE-I02** | `INV_TENANT_CHECK` | Todo endpoint autenticado exige verificación estricta de tenant_id. | Garantía de aislamiento multi-tenant. | Procesado del token JWT en cabecera. | `tenant_id_extracted == True`. |
| **RTE-I03** | `INV_CORS_WHITELIST`| Las políticas CORS solo admiten hosts configurados explícitamente. | Protección contra orígenes hostiles web. | Respuesta a petición OPTIONS. | `Allow-Origin != "*"`. |
| **RTE-I04** | `INV_TLS_ONLY` | Toda comunicación inter-agente y con el Gateway es cifrada vía TLS 1.3. | Confidencialidad del canal de transporte. | Handshake de conexión tcp. | `SSL_Version == TLSv1.3`. |
| **RTE-I05** | `INV_API_LIMIT` | Los endpoints de API públicos tienen un rate limit estricto por cliente. | Protección contra ataques de denegación. | Petición HTTP procesada. | `RateLimit_Hits_Min <= 100`. |
| **RTE-I06** | `INV_STATIC_ROUTING`| La topología de ruteo es estática y validada mediante Merkle tree. | Previene secuestros de tráfico. | Mutación en tabla de ruteo. | `verify_topology_hash() == True`. |
| **INV_RTE_07** | `INV_NO_STACK_LEAK` | Las respuestas de error 5xx no contienen trazas ni rutas internas. | Evita revelación de información física. | Captura de excepción interna. | `contains("traceback") == False`. |
| **RTE-I08** | `INV_HEALTH_ENDPOINT`| El Gateway expone endpoint `/health` comprobando toda la pila local. | Monitorización de salud de servicios. | Probe de orquestador o cron. | `health_status == "OK"`. |
| **RTE-I09** | `INV_PAYLOAD_MAX` | El tamaño máximo permitido para payloads de peticiones HTTP es de 10MB. | Protección contra caídas de memoria. | Ingesta de cuerpo de petición. | `Content-Length <= 10MB`. |
| **RTE-I10** | `INV_STATIC_PORTS` | Los puertos de servicio están definidos estáticamente en archivos de configuración. | Evita puertos aleatorios conflictivos. | Inicialización de socket de red. | `Port_Defined == True`. |
| **RTE-I11** | `INV_CONNS_CAP` | El número máximo de conexiones abiertas concurrentes ASGI es de 1024. | Evita saturación de sockets en el SO. | Configuración de Uvicorn. | `max_connections <= 1024`. |
| **RTE-I12** | `INV_VERSION_HEADER`| Toda petición y respuesta del API incluye cabecera de versión del sistema. | Asegura alineación del contrato API. | Header parseado en middleware. | `contains("X-CORTEX-VERSION")`. |
| **RTE-I13** | `INV_REPLAY_SHIELD` | Las peticiones autenticadas requieren nonce y timestamp con margen de 5s. | Previene ataques de repetición. | Validación de firma de request. | `abs(Current_Time - Timestamp) < 5s`. |
| **RTE-I14** | `INV_IP_FINGERPRINT`| El token de autenticación se valida contra el hash de la IP origen de petición. | Evita robo y reutilización de tokens. | Verificación de claims en JWT. | `hash(Client_IP) == Token_IP_Hash`. |
| **RTE-I15** | `INV_SECURE_HEADERS`| La API incluye cabeceras HSTS, X-Content-Type y X-Frame-Options por defecto. | Prevención de exploits clásicos de navegador. | Inspección de headers de respuesta. | `Security_Headers_Present == True`. |
| **RTE-I16** | `INV_FASTAPI_TYPES` | Toda ruta de FastAPI utiliza tipos Pydantic para los modelos de respuesta. | Garantiza tipado estricto de contrato. | Firma de la función del endpoint. | `hasattr(route, "response_model")`. |
| **RTE-I17** | `INV_EDGE_AUTH` | Toda petición se autentica a nivel perimetral antes de ser enrutada al Swarm. | Aislamiento de red interna. | Entrada al Gateway. | `Authenticated == True`. |
| **RTE-I18** | `INV_CLIENT_BACKOFF`| Los clientes del Swarm usan reintentos con exponential backoff y jitter. | Evita el efecto thundering herd. | Excepción de red capturada. | `Retry_Delay_Exponent >= 2`. |
| **RTE-I19** | `INV_GRACEFUL_CLOSE`| Los sockets y conexiones asíncronas se cierran mediante hooks de shutdown. | Limpieza absoluta de descriptores. | Señal SIGTERM recibida. | `Graceful_Shutdown_Success == True`. |
| **RTE-I20** | `INV_LEDGER_ROUTE` | Todo evento de ruteo crítico de mensajes se loguea en el Master Ledger. | Auditoría forense inmutable. | Evento procesado en el bus. | `Ledger_Written == True`. |

## MATRIZ 3: 5 ANTIPATRONES ESTOCÁSTICOS (RTE-AP01..05)
Fragilidades arquitectónicas en la capa de API y comunicaciones inter-agente.

| ID | Antipatrón | Disfunción Causal | Señal de Presencia | Impacto en Robustez | Refactor (Alternativa) |
|:---|:---|:---|:---|:---|:---|
| **RTE-AP01** | **Sync-on-Async Router**| Declarar endpoints en FastAPI sin la palabra clave `async def` usando I/O síncrono. | `def endpoint(...)` en lugar de `async def`. | Congelamiento completo de la API. | Refactorizar a corrutinas asíncronas. |
| **RTE-AP02** | **Wildcard CORS Policy**| Configurar CORS usando `allow_origins=["*"]` en producción. | asterisk `*` visible en la configuración CORS. | Exfiltración de datos locales vía XSS. | Definir dominios específicos locales. |
| **RTE-AP03** | **Plain API Credentials**| Pasar claves de API o tokens como parámetros en texto plano en la URL (Query String). | Parámetros `?api_key=...` visibles en peticiones. | Filtrado de credenciales en logs e historial. | Pasar credenciales en la cabecera `Authorization: Bearer`. |
| **RTE-AP04** | **DB Dynamic Routing** | Leer tablas de configuración de ruteo dinámico sin validación criptográfica previa. | Queries SQL directas para enrutar eventos. | Ataques de suplantación de identidad de nodos. | Ruteo estático firmado digitalmente. |
| **RTE-AP05** | **Mixed Socket Context**| Compartir el mismo socket TCP para flujos de datos sin encriptar y flujos cifrados. | Ausencia de canal TLS forzado por puerto. | Ataques MitM en canales débiles. | Forzar puertos y certificados segregados. |

## MATRIZ 4: 3 REDUNDANCIAS ACTIVAS (RTE-RA01..03)
Estructuras redundantes para resiliencia en capa de transporte de red.

| ID | Redundancia C5 | Función Topológica | Riesgo Mitigado | Coste (Overhead) | Dependencias |
|:---|:---|:---|:---|:---|:---|
| **RTE-RA01** | **Dual Reverse Proxy** | Servidores Nginx + Uvicorn balanceados localmente. | Falla del proceso Uvicorn principal. | Consumo mínimo de memoria. | `nginx` / `uvicorn` |
| **RTE-RA02** | **Fallback DNS Lookup** | Resolución local estática de IPs en `/etc/hosts` como fallback a DNS externo. | Caída del servidor de nombres externo. | Ninguno. | Configuración local de red |
| **RTE-RA03** | **Backup Gateway Node**| Instancia Gateway secundaria escuchando en puerto alternativo. | Puerto principal bloqueado o proceso colapsado. | Carga en reposo duplicada. | `FastAPI` instance |

## MATRIZ 5: 5 VECTORES DE ATAQUE ADVERSARIAL (RTE-AV01..05)
Vectores de intrusión y denegación en la capa de red del Gateway.

| ID | Vector Adversarial | Superficie de Ataque | Mecanismo de Explotación | Impacto Termodinámico | Defensa (Mitigación) |
|:---|:---|:---|:---|:---|:---|
| **RTE-AV01** | **Slowloris Attack** | Sockets de conexión Uvicorn. | Mantener conexiones HTTP abiertas indefinidamente enviando cabeceras lentas. | Agotamiento de sockets de red (Anergía). | Timeout estricto de keep-alive en Uvicorn. |
| **RTE-AV02** | **Parameter Fuzzing** | Endpoints de FastAPI. | Enviar grandes volúmenes de datos deformados para romper el tipado. | Exposición de excepciones internas (500). | Tipado estricto Pydantic y try-catch. |
| **RTE-AV03** | **Origin Spoofing** | Cabecera Origin en HTTP. | Simular cabeceras Origin de confianza desde webs hostiles. | Ejecución de peticiones cruzadas (CSRF). | Whitelist estricta CORS sin comodines. |
| **RTE-AV04** | **Replay Token Exploit**| Endpoint de autenticación. | Captura de token firmado y reinyección rápida dentro de ventana horaria. | Ejecución de acciones no autorizadas. | Control estricto de nonces únicos. |
| **RTE-AV05** | **Topology Flood** | Endpoint de ruteo dinámico. | Enviar miles de cambios de ruta falsos para colapsar tablas. | Desplome de la red local por OOM. | Firmas BFT requeridas en topology checks. |
