# Catálogo de Triggers y Condiciones de Disparo de las 47 Primitivas de Agente Autónomo
**Por Borja Fernández Angulo**\
*Investigador en Sistemas Complejos*

---

## 1. Arquitectura de Disparo (Trigger Engine)

En la orquestación de agentes autónomos, un **trigger** es el vector de acoplamiento entre la intención en lenguaje natural (o evento de reloj/webhook) y el despacho de un playbook o herramienta en silicio. El catálogo clasifica sus 47 primitivas bajo tres dinámicas de activación:

1. **Disparo Reactivo por Cues Léxicos (Intención Directa):** Menciones explícitas de entidades («Uber», «AirBnB», «reserva mesa», «crea una rutina»).
2. **Disparo Causal por Evento Externo (Heartbeat / Cron / Webhook):** Disparos temporales desatendidos (`routines`, `scheduling`, alertas de seguimiento de paquetes).
3. **Disparo por Conmutación de Fallback (Degradación Asistida):** Fallo de API o ausencia de conector nativo que redirige el flujo al navegador en contenedor (`box-desktop`, `no-connector-fallback`).

A continuación se detalla la matriz cardinal completa de los 47 disparadores con sus **palabras clave exactas**, **condiciones de activación**, **anti-triggers** (límites de descarte) y **cargas útiles requeridas**.

---

## 2. Matriz Cardinal Isomórfica 1:1 de Triggers

---

### Estrato I: Día a Día (1–18)

#### 1. routines («Automatismos a piñón fijo»)
- **Triggers (Cues léxicos):** `"avísame cada [X]"`, `"recuérdame a las [hora]"`, `"revisa todos los días a las [hora]"`, `"crea una rutina"`, `"mira si hay novedades cada [intervalo]"`, `"schedule check"`, `"daily digest"`.
- **Condición de Disparo:** Peticiones explícitas de recurrencia temporal o supervisión continua en segundo plano.
- **Anti-Triggers:** Tareas puntuales inmediatas sin cadencia repetitiva («mira el disco ahora»).
- **Payload Requerido:** Frecuencia/hora (expresión cron o intervalo) + acción de comprobación + canal de aviso.

#### 2. scheduling («Mover la agenda sin mirar la pantalla»)
- **Triggers (Cues léxicos):** `"pon una reunión con [persona]"`, `"¿qué tengo hoy en el calendario?"`, `"mira cuándo estoy libre el jueves"`, `"agenda cita"`, `"mueve la reunión de las 4"`, `"cancel meeting"`, `"check calendar"`.
- **Condición de Disparo:** Gestión de eventos, detección de huecos de disponibilidad y colisiones en Google Calendar/Outlook.
- **Anti-Triggers:** Recordatorios informales sin bloqueo de bloque temporal (despachados a `routines`).
- **Payload Requerido:** Fecha/hora + participantes + duración + título del evento.

#### 3. skill-authoring («Fabricar una herramienta nueva»)
- **Triggers (Cues léxicos):** `"guarda este flujo como skill"`, `"crea una skill para [tarea]"`, `"haz una herramienta reutilizable que [X]"`, `"edita la skill [nombre]"`, `"borra la skill [nombre]"`, `"new custom skill"`.
- **Condición de Disparo:** Solicitud explícita de abstraer una secuencia de acciones en una función permanente e invocable.
- **Anti-Triggers:** Peticiones de ejecutar un comando una sola vez en el terminal.
- **Payload Requerido:** Nombre de la skill + instrucciones paso a paso + condiciones de entrada/salida.

#### 4. learn-from-demonstration («Copiar lo que hago en pantalla»)
- **Triggers (Cues léxicos):** `"mira lo que hago y hazlo tú luego"`, `"aprende de esta grabación"`, `"mira mi pantalla y crea una skill con esto"`, `"record demonstration"`, `"learn from this workflow"`.
- **Condición de Disparo:** Entrada de un archivo de vídeo de pantalla o sesión de captura de eventos de cursor/clics.
- **Anti-Triggers:** Instrucciones dictadas por texto donde el flujo ya está parametrizado.
- **Payload Requerido:** Flujo de eventos/vídeo grabado + objetivo declarado de la tarea.

#### 5. channels («Abrir la esclusa de mensajes»)
- **Triggers (Cues léxicos):** `"conecta Slack"`, `"desconecta el canal de Discord"`, `"vincula Telegram"`, `"avísame por WhatsApp cuando termine"`, `"link message channel"`.
- **Condición de Disparo:** Configuración, enlace o desacoplamiento de plataformas de mensajería externas como I/O del bot.
- **Anti-Triggers:** Redacción o envío de un mensaje individual (despachado a `send-on-behalf`).
- **Payload Requerido:** Tipo de canal + token de integración/autenticación + identificador de chat/sala.

#### 6. send-on-behalf («Firmar y despachar por cuenta ajena»)
- **Triggers (Cues léxicos):** `"mándale un correo a [persona]"`, `"escribe un email diciendo que [X]"`, `"deja un borrador en Slack para [nombre]"`, `"envía este mensaje por mí"`, `"draft email to"`.
- **Condición de Disparo:** Intención de emitir correspondencia formal desde las cuentas personales del usuario.
- **Anti-Triggers:** Veto absoluto a despacho autónomo sin validación previa del borrador por el usuario biológico.
- **Payload Requerido:** Destinatario + asunto/contexto + aprobación explícita del borrador renderizado.

#### 7. voice («Voz que no suena a lata»)
- **Triggers (Cues léxicos):** `"dímelo en voz"`, `"léeme esto en audio"`, `"mándame una nota de voz"`, `"cántame un poema"`, `"voice memo"`, `"read aloud"`.
- **Condición de Disparo:** Petición expresa de salida acústica, archivo de audio sintetizado o nota de voz.
- **Anti-Triggers:** Respuestas estándar de texto en el hilo de chat.
- **Payload Requerido:** Texto base + tono/acento o formato de audio solicitado.

#### 8. code-changes («Tocar código sin romper el tinglado»)
- **Triggers (Cues léxicos):** `"modifica la función [X]"`, `"refactoriza este archivo"`, `"arregla este bug en [repo]"`, `"aplica estos cambios en Cursor Origin"`, `"apply patch"`, `"edit code in repository"`.
- **Condición de Disparo:** Peticiones de edición de código fuente local o sincronización con espacios de desarrollo.
- **Anti-Triggers:** Consultas de lectura o explicación conceptual de un algoritmo (solo lectura).
- **Payload Requerido:** Ruta del archivo/función + descripción del cambio + pruebas de no-regresión.

#### 9. source-control («El libro mayor de los cambios»)
- **Triggers (Cues léxicos):** `"haz un commit y push"`, `"abre una pull request"`, `"revisa las issues abiertas"`, `"mira el estado de la CI en GitHub"`, `"create PR"`, `"merge branch"`.
- **Condición de Disparo:** Interacción con el grafo de versiones (Git/GitHub/Origin), ramas y pipelines de integración continua.
- **Anti-Triggers:** Edición de archivos locales sin intención de versionado.
- **Payload Requerido:** Mensaje de commit / título de PR + rama origen/destino + repositorio objetivo.

#### 10. add-connector («Enchufar un cable nuevo»)
- **Triggers (Cues léxicos):** `"conecta mi cuenta de [servicio]"`, `"instala el conector de Notion"`, `"autentica Linear"`, `"añade integración con [app]"`, `"install new connector"`.
- **Condición de Disparo:** Solicitud de vincular un nuevo servicio SaaS soportado al ecosistema de herramientas del bot.
- **Anti-Triggers:** Navegación en web abierta sin integración API (despachado a `box-desktop`).
- **Payload Requerido:** Nombre del servicio + flujo OAuth o API Key.

#### 11. purchases («Pasar la tarjeta sin que te desplumen»)
- **Triggers (Cues léxicos):** `"compra esto"`, `"reserva el billete y págalo"`, `"paga la suscripción de [servicio]"`, `"haz el checkout de este pedido"`, `"proceed to payment"`.
- **Condición de Disparo:** Intención transaccional que implique compromiso de fondos, pasarela de pago o datos bancarios.
- **Anti-Triggers:** Navegación previa y comparación de artículos sin intención de cobro (despachado a `shopping`). Requiere atestación Touch ID obligatoria.
- **Payload Requerido:** Artículo/servicio + importe máximo autorizado + confirmación biométrica del titular.

#### 12. shopping («Comparar precios sin tragarse anuncios»)
- **Triggers (Cues léxicos):** `"busca el mejor precio para [producto]"`, `"compara [artículo A] con [artículo B]"`, `"mira si hay stock de [X]"`, `"repite el pedido de café"`, `"price check"`.
- **Condición de Disparo:** Búsqueda comercial, auditoría de precios y preparación de carritos sin ejecutar el pago final.
- **Anti-Triggers:** Ejecución de cargo monetario (despachado a `purchases`).
- **Payload Requerido:** Nombre del producto + especificaciones clave + criterio de ordenación (precio/plazo).

#### 13. sign-in («Pasar el portero de la discoteca»)
- **Triggers (Cues léxicos):** `"inicia sesión en [sitio]"`, `"entra con mi cuenta a [URL]"`, `"resuelve el captcha de esta página"`, `"pon el código 2FA que llegó al móvil"`, `"login to"`.
- **Condición de Disparo:** Detección de muro de autenticación, pantalla de credenciales o desafío de verificación.
- **Anti-Triggers:** Acceso a sitios públicos que no exigen sesión autenticada.
- **Payload Requerido:** Dominio del servicio + inyección de credenciales seguras (vía 1Password local) + token MFA.

#### 14. in-chat-forms («Rellenar casillas desde el teclado»)
- **Triggers (Cues léxicos):** `"rellena este formulario con mis datos"`, `"completa los campos de envío"`, `"pon mi dirección y teléfono en la web"`, `"fill form"`.
- **Condición de Disparo:** Presencia de formularios web complejos (direcciones, encuestas, registros de contacto) que se resuelven conversacionalmente.
- **Anti-Triggers:** Formularios de pago o checkout bancario (derivados a `purchases`).
- **Payload Requerido:** Identificación de campos DOM + datos de perfil local del usuario.

#### 15. box-desktop («El ordenador fantasma de la nube»)
- **Triggers (Cues léxicos):** `"abre el navegador y haz [X]"`, `"entra en esta web que no tiene API"`, `"haz clic en el botón azul de la página"`, `"use desktop browser"`, `"open remote browser"`.
- **Condición de Disparo:** Tareas sobre sitios web interactivos que carecen de conector o API estructurada.
- **Anti-Triggers:** Servicios con conector nativo autenticado (`add-connector`).
- **Payload Requerido:** URL objetivo + secuencia de interacciones esperadas (clics, scroll, extracción).

#### 16. no-connector-fallback («Buscarse la vida cuando no hay enchufe»)
- **Triggers (Cues léxicos):** Activación interna: `[API_UNAVAILABLE]`, `[CONNECTOR_NOT_FOUND]`, `"el conector está fallando, hazlo por web"`, `"se atascó el login, prueba por navegador"`.
- **Condición de Disparo:** Fallo o ausencia de integración formal; conmutación automática al motor de navegación headless.
- **Anti-Triggers:** Cuando la API responde con código HTTP 200 y opera con normalidad.
- **Payload Requerido:** Tarea original en curso + estado de fallo del conector.

#### 17. export-bot-template («Empaquetar el clon para llevar»)
- **Triggers (Cues léxicos):** `"exporta la plantilla de este bot"`, `"dame una copia de esta configuración para compartir"`, `"export bot configuration"`, `"clone bot template"`.
- **Condición de Disparo:** Solicitud de serialización de prompts de sistema, lista de skills y ajustes del agente (purgando credenciales privadas).
- **Anti-Triggers:** Backup completo de datos de usuario con historial privado.
- **Payload Requerido:** Identificador del bot + formato de exportación (JSON/YAML/Markdown).

#### 18. group-chat-turns («Saber cuándo callar en el barullo»)
- **Triggers (Cues léxicos):** Mención directa `@bot`, respuesta a mensaje del bot en sala de grupo, o detección de pregunta dirigida en canales multi-usuario.
- **Condición de Disparo:** Mensajes recibidos dentro de hilos grupales o canales compartidos.
- **Anti-Triggers:** Charlas casuales entre miembros del grupo donde el bot no es interpelado (silencio operativo estricto).
- **Payload Requerido:** Identificador de emisor + contexto del hilo + mensaje directo.

---

### Estrato II: Viajes, Comida y Encargos (19–25)

#### 19. flight-booking («Cazar billetes sin pagar peajes»)
- **Triggers (Cues léxicos):** `"búscame un vuelo de [origen] a [destino]"`, `"mira billetes de avión para [fechas]"`, `"cambia mi vuelo a [hora]"`, `"saca la tarjeta de embarque"`, `"find flights"`.
- **Condición de Disparo:** Búsqueda, comparación de itinerarios o gestión de billetes aéreos.
- **Anti-Triggers:** Preguntas genéricas sobre clima en el destino sin mención a transporte.
- **Payload Requerido:** Origen (IATA) + Destino (IATA) + Fechas (ida/vuelta) + Preferencia de escalas.

#### 20. accommodation-booking («Buscar techo sin trampa de fotos»)
- **Triggers (Cues léxicos):** `"busca hotel en [ciudad]"`, `"necesito alojamiento para 3 noches en [lugar]"`, `"compara apartamentos cerca del centro"`, `"book hotel"`.
- **Condición de Disparo:** Solicitud de hospedaje, reserva o comparación hotelera.
- **Anti-Triggers:** Consultas específicas sobre estancias particulares de Airbnb (enrutadas a `site-playbooks-airbnb`).
- **Payload Requerido:** Ciudad/zona + fechas de check-in/out + número de huéspedes + presupuesto.

#### 21. rideshare («Pedir coche sin abrir la app del móvil»)
- **Triggers (Cues léxicos):** `"pídeme un Uber a [dirección]"`, `"cuánto tarda un Lyft en recogerme"`, `"pide un Bolt al aeropuerto"`, `"order ride"`, `"call a car"`.
- **Condición de Disparo:** Transporte urbano bajo demanda con geolocalización.
- **Anti-Triggers:** Consultas de rutas en transporte público (metro/tren).
- **Payload Requerido:** Punto de recogida + destino exacto + categoría de coche + confirmación de tarifa.

#### 22. restaurant-recommendations («Comer bien sin caer en trampas de turistas»)
- **Triggers (Cues léxicos):** `"dónde cenar bien en [zona]"`, `"recomiéndame un japonés para cena de trabajo"`, `"restaurantes con terraza cerca de mí"`, `"best restaurants for dinner"`.
- **Condición de Disparo:** Asesoramiento gastronómico por contexto, presupuesto y tipo de cocina.
- **Anti-Triggers:** Petición de reserva inmediata de mesa (despachada a `restaurant-booking`).
- **Payload Requerido:** Ubicación + tipo de cocina/ocasión + rango de precio.

#### 23. restaurant-booking («Poner la mesa sin hacer cola al teléfono»)
- **Triggers (Cues léxicos):** `"reserva mesa en [restaurante]"`, `"mira si hay hueco hoy a las 9 en [sitio]"`, `"cancela la reserva de mesa"`, `"reserve table"`.
- **Condición de Disparo:** Tramitación de reservas en locales de restauración.
- **Anti-Triggers:** Petición de comida a domicilio (despachada a `food-ordering`).
- **Payload Requerido:** Nombre del restaurante + comensales + fecha/hora deseada + teléfono de contacto.

#### 24. food-ordering («Pedir comida sin que te cobren triple comisión»)
- **Triggers (Cues léxicos):** `"pide unas pizzas a domicilio"`, `"pide comida tailandesa para llevar"`, `"quiero pedir cena a [restaurante]"`, `"order food delivery"`.
- **Condición de Disparo:** Pedidos de comida preparada para entrega en casa o recogida en local.
- **Anti-Triggers:** Compra de alimentos en supermercado crudos (despachada a `site-playbooks-instacart`).
- **Payload Requerido:** Restaurante/platos + dirección de entrega + límite de gasto.

#### 25. job-search («Buscar curro con bisturí»)
- **Triggers (Cues léxicos):** `"busca ofertas de [puesto] en [ciudad/remoto]"`, `"mira qué puestos de Rust hay abiertos"`, `"sigue el estado de mi candidatura en [empresa]"`, `"job openings for"`.
- **Condición de Disparo:** Rastreo de vacantes laborales, análisis de descripciones de puesto y tracking de procesos.
- **Anti-Triggers:** Redacción integral de currículum o preparación de entrevista (derivado al arnés `c5-career-and-interview-architect`).
- **Payload Requerido:** Rol técnico/profesional + ubicación/remoto + filtros salariales.

---

### Estrato III: Playbooks de Sitios Específicos (26–47)

#### 26. site-playbooks-airbnb («Inspección de estancias vacacionales»)
- **Triggers:** `"busca en Airbnb en [sitio]"`, `"lee este anuncio de Airbnb [enlace]"`, `"mira opiniones de este piso en Airbnb"`.
- **Anti-Triggers:** Prohibido disparar para herramientas de anfitrión (gestión de anuncios propios, precios de host).

#### 27. site-playbooks-bestbuy («Caza de gadgets en tienda americana»)
- **Triggers:** `"busca en Best Buy [producto]"`, `"precio y stock en Best Buy de [X]"`, `"mira si hay recogida en tienda en Best Buy"`.
- **Anti-Triggers:** Compras en territorio europeo sin presencia de tiendas físicas Best Buy.

#### 28. site-playbooks-costco («Auditoría a granel»)
- **Triggers:** `"mira precio en Costco de [artículo]"`, `"stock en Costco"`, `"arma carrito Same-Day en Costco"`.
- **Anti-Triggers:** Consultas que requieran número de membresía exclusivo si no está en almacén de claves local.

#### 29. site-playbooks-craigslist («Rastreo de tablón local»)
- **Triggers:** `"busca anuncios en Craigslist [ciudad]"`, `"mira clasificados de [producto] en Craigslist"`.
- **Anti-Triggers:** Veto explícito de la plataforma: **no publicar anuncios ni contactar a vendedores**. Solo lectura.

#### 30. site-playbooks-doordash («Comida y recados en DoorDash»)
- **Triggers:** `"mira la carta de [restaurante] en DoorDash"`, `"añade [plato] al carrito de DoorDash"`, `"resumen del checkout de DoorDash"`.
- **Anti-Triggers:** Ejecución ciega del pago final sin confirmación dactilar.

#### 31. site-playbooks-ebay («Pujas y compras de segunda mano»)
- **Triggers:** `"busca en eBay [artículo]"`, `"precio de venta en eBay"`, `"revisa este anuncio de eBay [URL]"`.
- **Anti-Triggers:** Emisión de pujas de último segundo (sniping) sin saldo verificado.

#### 32. site-playbooks-etsy («Artesanía y personalizaciones»)
- **Triggers:** `"busca en Etsy [artículo]"`, `"mira precio de [artesanía] en Etsy"`.
- **Anti-Triggers:** Herramientas de vendedor (gestión de tienda Etsy, pedidos de clientes).

#### 33. site-playbooks-expedia («Comparador general de viajes»)
- **Triggers:** `"compara en Expedia vuelos y hotel"`, `"paquetes de viaje en Expedia a [destino]"`.
- **Anti-Triggers:** Búsquedas específicas de una sola aerolínea (despachadas a United/Southwest).

#### 34. site-playbooks-facebook-marketplace («Segunda mano vecinal»)
- **Triggers:** `"busca en Facebook Marketplace coches cerca de mí"`, `"alquileres en Facebook Marketplace en [zona]"`.
- **Anti-Triggers:** Enviar mensajes directos al vendedor o publicar anuncios propios.

#### 35. site-playbooks-fedex («Rastreo logístico de FedEx»)
- **Triggers:** `"dónde está mi paquete de FedEx [tracking]"`, `"sigue envío FedEx"`, `"cuándo llega el FedEx"`.
- **Anti-Triggers:** Números de seguimiento de otras agencias (USPS/UPS).

#### 36. site-playbooks-google-flights («El radar global de tarifas aéreas»)
- **Triggers:** `"mira Google Flights de [origen] a [destino]"`, `"itinerarios más baratos en Google Flights"`.
- **Anti-Triggers:** Compra directa dentro del motor (Google Flights no procesa pagos, redirige a aerolíneas).

#### 37. site-playbooks-instacart («Cesta de la compra a domicilio»)
- **Triggers:** `"haz la compra en Instacart de [supermercado]"`, `"añade leche y fruta al carrito de Instacart"`.
- **Anti-Triggers:** Confirmación final de entrega sin verificación de propina/comisión.

#### 38. site-playbooks-linkedin («Radar de empleo corporativo»)
- **Triggers:** `"busca ofertas en LinkedIn de [puesto]"`, `"ofertas de trabajo en LinkedIn en [empresa]"`.
- **Anti-Triggers:** Veto explícito de la plataforma: **no postularse a candidaturas ni modificar el perfil público**.

#### 39. site-playbooks-luma («Eventos y comunidad tech»)
- **Triggers:** `"eventos de IA en Luma en [ciudad]"`, `"lee la ficha de este evento en Luma [URL]"`.
- **Anti-Triggers:** Cancelación de eventos organizados por el propio usuario.

#### 40. site-playbooks-opentable («Reserva directa en OpenTable»)
- **Triggers:** `"busca mesa en OpenTable en [sitio]"`, `"reserva en OpenTable para 2 hoy"`.
- **Anti-Triggers:** Restaurantes exclusivos de la red Resy.

#### 41. site-playbooks-realtor («Listados inmobiliarios en EE. UU.»)
- **Triggers:** `"busca casas en Realtor en [código postal]"`, `"mira las notas de colegios en Realtor para [zona]"`.
- **Anti-Triggers:** Búsquedas de vivienda en territorio europeo (requiere Idealista/Fotocasa).

#### 42. site-playbooks-resy («Mesa en locales gastronómicos exclusivos»)
- **Triggers:** `"mesas libres en Resy en [restaurante]"`, `"reserva por Resy para el viernes"`.
- **Anti-Triggers:** Locales sin integración en el protocolo Resy.

#### 43. site-playbooks-southwest («Tarifas de la aerolínea Southwest»)
- **Triggers:** `"tarifas de Southwest de [ciudad] a [ciudad]"`, `"vuelos baratos en Southwest"`.
- **Anti-Triggers:** Veto explícito: **no permite reservas, no check-in, no cambios de vuelo**.

#### 44. site-playbooks-target («Precios y recogida en Target»)
- **Triggers:** `"busca en Target [artículo]"`, `"mira si hay recogida en tienda en Target de [producto]"`.
- **Anti-Triggers:** Compras en tiendas fuera de Estados Unidos.

#### 45. site-playbooks-united («Vuelos de United Airlines con millas o efectivo»)
- **Triggers:** `"vuelos de United a [destino]"`, `"busca billetes con millas en United"`.
- **Anti-Triggers:** Gestión de un viaje ya reservado o cambios de asiento post-reserva.

#### 46. site-playbooks-ups («Rastreo logístico de UPS»)
- **Triggers:** `"seguimiento de paquete de UPS [número]"`, `"dónde está mi envío de UPS"`.
- **Anti-Triggers:** Paquetes de FedEx o Correos.

#### 47. site-playbooks-usps («Rastreo del servicio postal estadounidense»)
- **Triggers:** `"tracking de USPS [código]"`, `"dónde está mi paquete de correos USA"`.
- **Anti-Triggers:** Paquetes de mensajería privada internacional.

---

## 3. Síntesis Operativa y Falsación de Triggers

El catálogo revela que **el 46,8% de los triggers del catálogo comercial están geográficamente muertos para un operador en España o Europa** (USPS, Southwest, Target, Best Buy, Realtor, Craigslist local).

Bajo la arquitectura soberana C5-REAL:
1. **Poda de Anergía:** Los triggers de plataformas no operativas en la jurisdicción local deben permanecer desactivados para evitar desvío de atención y gasto entrópico en llamadas fallidas.
2. **Reemplazo Transductor:** Los triggers de retail y logística se reemplazan por adaptadores hacia las APIs/DOMs de la infraestructura real europea (Correos, SEUR, Wallapop, Idealista, Renfe).
3. **Mantenimiento del Cerrojo de Markov:** Ningún trigger de compra (`purchases`, `checkout`) tiene autorización para autoejecutarse sin la interrupción física del sensor Touch ID.

---

**Firmado:**\
**Borja Fernández Angulo**\
*Investigador en Sistemas Complejos*
