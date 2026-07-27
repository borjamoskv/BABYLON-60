# ADR-011: Domain Topology, Routing, and Epistemic Hygiene (C5-REAL)

## 1. Contexto y Problema
El diseño previo sugería la instanciación simultánea de 5 dominios (`cortexpersist.org`, `.dev`, `.com`, `babylon60.com`, `agents.archi`) bajo la asunción de que una topología fragmentada imitaba los ecosistemas empresariales (Sigstore, K8s).
Sin embargo, bajo la termodinámica estricta C5-REAL, esto generaba **Anergía**:
1. Dominios vacíos erosionan la credibilidad técnica (Green Theater).
2. Fragmentación prematura del SEO ("Context Rot").
3. Separar el billing en `babylon60.com` introduce fricción en procurement y activa filtros anti-fraude.
4. El `.org` no confiere neutralidad per se; la neutralidad es criptográfica y gobernada, no un TLD.

## 2. Decisión (MILLENNIUM Execution Plan)

### 2.1. Unificación de Superficie Principal
- **Dominio Canónico:** `cortexpersist.dev` asume el rol de vértice central. Todo el tráfico, documentación y portal de desarrolladores colapsa aquí.
- **Redirección Causal (301):** Todos los demás dominios (`cortexpersist.org`, `babylon60.com`, `agents.archi`) ejecutarán un redirect 301 incondicional hacia `cortexpersist.dev` hasta que la densidad de información requiera una ramificación física justificada.

### 2.2. Aislamiento del Vector Comercial (Billing)
- El entorno Enterprise y de facturación colapsa obligatoriamente en `cortexpersist.com`. Queda terminantemente prohibido utilizar `babylon60.com` o cualquier dominio alternativo para pasarelas de pago (Stripe/Paddle).

### 2.3. Higiene Criptográfica (DNS & Anti-Spoofing)
- **Bloqueo DNSSEC** forzado en los 5 dominios.
- **Registros Nulos de Autenticidad:** Configuración estricta de SPF (`v=spf1 -all`), DKIM, y DMARC (`p=reject`) en los dominios inactivos/aparcados para aniquilar el vector de ataque por spoofing.

### 2.4. Erradicación del Green Theater
- Se purgan inmediatamente todos los términos estocásticos ("grado militar", "impenetrable") de los manifiestos. La seguridad no se adjetiva; se demuestra mediante pruebas formales y hashes criptográficos en el Ledger.

## 3. Consecuencias
- Minimización térmica: Cero esfuerzo en mantenimiento de 5 portales.
- Aumento directo de la fiabilidad Enterprise.
- Enrutamiento simplificado y consolidación de la autoridad de marca.

## 4. Orquestación (SLA)
- Invocar Swarm MILLENNIUM (1000-Agent Simulation) para el refactor distribuido en todo el corpus documental y de código, apuntando todas las referencias estáticas a `cortexpersist.dev`.
