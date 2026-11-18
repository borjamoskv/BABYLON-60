---
name: c5_enterprise_compliance_offer_invariant
description: Invariante de deslinde ontológico en oferta comercial Enterprise, comparativas SOTA y cumplimiento del Reglamento (UE) 2024/1689 (EU AI Act).
trigger: "model_decision"
---

# Invariante de Deslinde Ontológico en Oferta Comercial Enterprise (INV_C5_ENTERPRISE_OFFER)

Aplicar solo a una oferta o evaluación enterprise solicitada. Las referencias jurídicas de este documento requieren comprobar vigencia y aplicabilidad con fuentes oficiales en esa tarea; esta regla no certifica conformidad ni autoriza publicar una oferta.

## 1. Prohibición de Falsa Equivalencia Regulatoria (Silicio ≠ Conformidad Legal)
Queda estrictamente prohibido afirmar en landings comerciales, teasers, presentaciones de producto o documentación enterprise que BABYLON-60 otorga "conformidad total", "cumplimiento automático" o "certificación llave en mano" con el Reglamento (UE) 2024/1689 (EU Artificial Intelligence Act):
* **Vector Técnico (TCB):** Describir los controles de trazabilidad, autorización y parada indicando su implementación, versión, configuración, pruebas y límites. Solo se presentarán como verificados los resultados respaldados por evidencia accesible. Touch ID es una opción técnica de autorización; el Art. 14 no exige ese dispositivo ni convierte la autenticación en supervisión humana suficiente por sí sola.
* **Vector Organizativo (Operador):** La conformidad formal de un sistema de IA de alto riesgo exige que el operador defina políticas de retención, capacitación cognitiva del supervisor, explicabilidad en UI, procedimientos de mitigación y evaluación de sesgos/exactitud estadística del LLM.

## 2. Requisitos Mandatorios de la Oferta Enterprise
Para una oferta solicitada, separar controles técnicos de responsabilidades organizativas. Los parámetros comerciales siguientes son una plantilla revisable; acordar alcance y aceptación antes de comprometerlos:
1. **Ficha Técnica del Piloto (PoC):** Propuesta inicial de 30 a 45 días y hasta 5 nodos, sujeta a capacidad y acuerdo. Fijar criterios medibles de aceptación Pass/Fail:
   - *Intercepción Fail-Closed:* Veto de todas las operaciones no autorizadas incluidas en los casos de prueba acordados (`AUTH_002`, `AUTH_007`), con exclusiones y configuración documentadas.
   - *Trazabilidad Criptográfica:* Recibos verificables para todos los efectos válidos del conjunto de prueba acordado, identificando formato, algoritmo y almacenamiento utilizados.
   - *Idempotencia ante Caídas:* Recuperación de estado consistente sin corrupción tras parada abrupta `SIGKILL` (`AUTH_003`, `AUTH_006`).
2. **SLA y capacidad acreditados:** Ninguna oferta comprometerá atención 24/7, tiempos de respuesta, RTO/RPO o capacidad de nodos sin un Anexo de Capacidad Acreditada vigente: topología y quórum real cuando aplique, carga y capacidad medidas, cobertura de guardias y pruebas de recuperación/failover pertinentes. Una automatización de failover no demuestra cobertura humana. Identificar exclusiones, fecha y responsables. En instalaciones de operador único sin redundancia acreditada, declarar best-effort o ventanas operativas definidas; no presentar objetivos como garantías.
3. **Evidencia Pre-Contacto:** Acceso directo a reportes de muestra JSON (`eu_ai_act_compliance_pack.json`) y enlace clicable entre claims técnicas y tests del monorepo (`CLAIMS.toml`).
4. **Desacoplamiento de Embudo:** Adaptar contenido y llamadas a la acción al público acordado; CISO, Platform Engineering y DPO son perfiles de referencia, no una audiencia obligatoria.

## 3. Obligaciones, plazos, sanciones y alcance de la evidencia (EU AI Act Arts. 12, 14, 16, 26, 99 y AI Omnibus)

Toda afirmación jurídica debe identificar el uso previsto, el papel del operador, la disposición aplicable y su fuente:
* **Registro y trazabilidad (Art. 12):** El Art. 12 exige capacidades de registro automático de eventos (*logging*) para sistemas de alto riesgo. No prescribe cadenas hash, SHA3-256, blockchain ni anclaje en Bitcoin; la verificabilidad criptográfica puede aportar evidencia técnica, pero no equivale por sí sola a cumplir el reglamento.
* **Calendario de aplicación (AI Omnibus, en vigor desde 27-07-2026):** No utilizar el 2 de agosto de 2026 como fecha de exigibilidad de los requisitos de alto riesgo. Los plazos revisados aplicables son **2 de diciembre de 2027** (sistemas del Art. 6.2 / Anexo III) y **2 de agosto de 2028** (sistemas del Art. 6.1 / Anexo I).
* **Obligaciones propias:** Los Arts. 16 y 26 establecen obligaciones de proveedores y responsables del despliegue de sistemas de IA de alto riesgo, respectivamente. El Art. 26 no atribuye al desplegador toda responsabilidad ni exonera al proveedor. Deben evaluarse los papeles efectivos, las conductas y las normas aplicables; los proveedores de modelos de uso general tienen además su régimen específico.
* **Supervisión humana:** El Art. 14 exige supervisión efectiva y proporcionada, con medios para comprender las capacidades y límites, evitar el sesgo de automatización, interpretar resultados e intervenir o detener el sistema. La biometría puede apoyar una autorización, pero no sustituye estas condiciones ni acredita por sí sola conformidad.
* **Sanciones:** El Art. 99.3 prevé hasta 35 M€ o el 7% por infracciones de las prohibiciones del Art. 5. El Art. 99.4 prevé hasta 15 M€ o el 3% por las obligaciones que enumera, incluidas las de los Arts. 16 y 26. Los porcentajes se refieren al volumen de negocios mundial del ejercicio anterior; para empresas rige el límite mayor, con las excepciones del Art. 99.6 (pymes: menor) y 99.6 bis (pequeñas empresas de mediana capitalización: menor para los apartados 4 y 5). La sanción concreta depende de las circunstancias. El Art. 71 regula la base de datos de la UE, no las multas.
* **Modelos de riesgo:** En un escenario hipotético, $\epsilon=P(\text{error})$ y $\delta=P(\text{omisión del control}\mid\text{error})$ permiten calcular $N\epsilon\delta$ fallos conjuntos esperados si esas tasas aplican a cada operación. No son automáticamente catástrofes o brechas, ni un número garantizado de incidentes. Si se usan tasas marginales en lugar de condicionales, su producto necesita una hipótesis de independencia justificada.
* **Límites de las pruebas:** Ningún simulador, hash, recibo o sensor certifica por sí solo diligencia debida, inmunidad frente a sanciones o probabilidad cero de fallo. Toda garantía técnica debe limitarse al modelo de amenazas, casos, entorno y versión efectivamente verificados.

Fuentes oficiales: [Reglamento consolidado a 27-07-2026](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng); Comisión Europea: [Art. 14](https://ai-act-service-desk.ec.europa.eu/es/ai-act/article-14), [Art. 16](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-16), [Art. 26](https://ai-act-service-desk.ec.europa.eu/es/ai-act/article-26), [Art. 71](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-71) y [Art. 99](https://ai-act-service-desk.ec.europa.eu/es/ai-act/article-99).

## 4. Comparaciones contractuales y de Estado del Arte (SOTA) respaldadas por fuentes

Toda comparación con otro proveedor debe identificar el contrato, versión, fecha y cláusulas examinadas. Revisar garantías, límites de responsabilidad, indemnizaciones y tratamiento de datos sin atribuir condiciones a un proveedor sin fuente. La ubicación de una nube o el uso de telemetría no permiten concluir automáticamente incumplimiento de RGPD o NIS2; la evaluación requiere los hechos del tratamiento y las obligaciones aplicables. Una preferencia arquitectónica local debe presentarse como tal.

En análisis competitivos y revisiones SOTA de memoria, persistencia o seguridad:
* **Veto a exclusividad por apilamiento ad-hoc (*Anti-Feature-Stacking*):** No declarar «intersección vacía», «hueco confirmado» ni ausencia absoluta de competidores acumulando una lista específica de componentes (`SQLite + SHA3-256 + Lamport + UUIDv5 + OTS + pip`). Evaluar la diferenciación mediante preguntas operativas: qué manipulaciones detecta cada sistema, contra qué atacante y referencia de confianza, qué necesita desplegar el usuario, si un tercero puede verificar la evidencia y el coste de integración/mantenimiento.
* **Separación ortogonal de propiedades:**
  1. *Integridad de mensaje vs. secuencia:* El cifrado autenticado por mensaje (p. ej. AEAD / Fernet) aporta integridad de contenido aunque carezca de cadena hash de secuencia. «Sin hash-chain» $\neq$ «sin integridad criptográfica».
  2. *Inmutabilidad de log vs. deserialización:* Encadenar hashes no previene vulnerabilidades de deserialización (RCE) o inyección (SQLi) al consumir los datos.
  3. *Registro vs. proyección de memoria:* La evolución de representaciones contextuales ($\text{Estado}_t = \operatorname{Proyecci\acute{o}n}(\text{eventos}_{\le t})$) no equivale a reescritura fraudulenta del historial.
  4. *Anclaje temporal:* Separar OTS del código (commits Git) de OTS de raíces operativas del ledger; ninguno acredita por sí solo ejecución efectiva ni veracidad semántica.
