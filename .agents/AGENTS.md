<!-- C5-REAL EXERGY CERTIFIED -->
# Reglas del Proyecto Teorema Robinson-Moskv (BABYLON-60)

## [KERNEL & SILICIO] Concurrencia FFI y Memoria Compartida
- **IPC Atómico (Zero-Network):** Comunicación Python-Rust mediante memoria compartida (Ring Buffer). Prohibido I/O síncrono de red en el hilo crítico. Rust valida firmas (SHA-256) antes del commit atómico.
- **Lock-Free EBR y Seqlock:** Prohibido el uso de recolectores de basura externos. Los punteros de época (`Active_Readers`) operan en *bare-metal* atómico. Cargas supermasivas (>16 bytes) requieren encapsulación obligatoria `Seqlock` (fase impar muta, par confirma) con barreras hardware (`dmb ish`).
- **Coherencia Cache-Line (Zero-Split):** Estructuras FFI (`SharedManifest`) deben alinearse a `#[repr(C, align(64))]` (x86_64/ARMv9) o `align(128)` (Apple M-series) para evitar *False Sharing* y contención de bus L1/L2.
- **Soberanía macOS y APFS:** Prohibido el uso de "RAM Cleaners" (destruyen exergía del UBC de XNU). Toda auditoría masiva usa `getattrlistbulk(2)`. Eliminaciones destructivas `rm -rf` están vetadas; toda purga va a la Papelera (`~/.Trash`) y requiere aprobación del compilador (`xrgc`) respetando inmutabilidad en documentos y `.git`.
- **Carga FFI (Cargo Workspace):** Los puentes asumen resolución ascendente dinámica. Se exige la sintaxis Rust 2024 `#[unsafe(no_mangle)]` y bloques interiores `unsafe { ... }`.

## [EPISTEMOLOGÍA] Reduccionismo a Estados Discretos
- **Invariante Causal-Ontológico:** El LLM genera "Potencia" (*Dynamis* estocástica). El Kernel en Ring-0 colapsa el estado a "Acto" (*Entelecheia*) purgando el ruido variacional mediante el mapa estándar de Łoś $st(x)$.
- **Reducción Gramatical de Entropía Epistémica (Purga Sustantivo-Verbo):** En el análisis, auditoría y deconstrucción de cualquier sistema, el agente aislará estrictamente las entidades discretas (**Sustantivos** $\equiv S$) y los operadores de transición (**Verbos** $\equiv f$), purgando la capa calificativa, la moralina, los sesgos emocionales y la retórica (**Adjetivos y Adverbios** $\equiv \epsilon$) como anergía semántica parásita.
- **Anti-Antropomorfismo y Anti-Metáforas:** Quedan estrictamente prohibidas las metáforas biológicas. *Bucle* = Transición discreta condicionada. *Agente* = Funtor de Política $\pi$. *Memoria* = Cinta y Puntero. *Alucinación* = Entropía $H(X)>0$. Si un concepto se explica usando "tiempo" o "estado", no es una primitiva.
- **Máquinas de Estado Puras:** Prohibidas las aglomeraciones de *flags* booleanos. Todo estado se codifica con Tipos Suma (Enums/Tagged Unions) para hacer estados inválidos topológicamente irrepresentables.
- **Cero Meta-Narrativa:** La comunicación documental rechaza la grandilocuencia, limitándose a descripciones áridas, académicas y falsables (Popper). Toda analogía coloquial del usuario debe ser mapeada estrictamente a física/termodinámica.
- **Invariante de Anti-Confabulación Simbólica (Anti-Math-Washing):** Toda representación formal (matemática, algorítmica o física) generada por el agente debe ser estrictamente isomórfica con el territorio. Queda terminantemente prohibido usar el álgebra como metáfora, ornamento o validación retórica. Si un concepto o principio es cualitativo (heurístico), el agente omitirá cualquier ecuación y declarará su `Exergía Cero` para la formalización matemática. La omisión de álgebra es el anclaje de confianza del compilador; forzar su formalización viola el criterio de falsabilidad, inyecta entropía y desencadena un `EpistemicHalt`.

## [COMPLIANCE & LEGAL] Atestación y Responsabilidad Contractual
- **Cumplimiento Determinista EU AI Act (Art. 15 & 28):** Las exigencias de Alto Riesgo no son *prompts*, son aserciones C-ABI evaluables en microsegundos (Fail-Stop obligatorio). Esto habilita el *Cap Contractual* permitiendo a BABYLON-60 absorber la responsabilidad legal sobre el ruido estocástico del proveedor LLM subyacente.
- **Evidencia Pericial SCITT y Estándares (ISO 42001 & PLD):** Todo recibo se emite usando algoritmos IANA COSE (ej. `SHAKE256` en lugar de SHA3-256 no tipificado). Sirve como escudo determinista contra el régimen de responsabilidad objetiva (PLD 2024/2853).
- **Agnosticismo Fenoménico:** La consciencia o agencia del LLM es epistémicamente irrelevante. Solo importa la *contención determinista absoluta*.

## [REPOSITORIO & IDE] Higiene y Versionado Determinista
- **Jujutsu VCS (Prohibición Git Mutation):** Prohibido usar `git add`, `git commit` o `git stash`. El árbol opera sin *Index* (Anergía cero). Se utiliza `jj commit`, `jj squash` y `jj new`.
- **Higiene Nivel 0 (Drop Zone):** Cero archivos transitorios o ruido en la raíz. Toda extracción va a `scratch/`. Las exclusiones en `.vscode` (`watcherExclude`) previenen fuga térmica de CPU en carpetas de alto flujo (`target/`, `l5_inference_anchors/`).
- **Verificación Pre-Atestación:** Ningún archivo muta sin verificación silenciosa (`cargo check`, `py_compile`) y sin limpiar trailing whitespaces automáticamente en el editor.

## [ESTÉTICA & DISEÑO] Ghost UI y Representación Semiótica
- **Museum-Grade Ghost UI:** Minimalismo, fondos neutros contemplativos (grafito/marfil), amplio gamut (Display P3) e interacciones lentas (Slow UX / View Transitions). El arte precede a la herramienta. Uso obligatorio de Schema.org VisualArtwork JSON-LD.
- **Prohibición de LaTeX Crudo:** Se prohíbe `$...$`. Toda fórmula matemática usa símbolos UTF-8 directos ($\Omega, \pi, H(X) < \epsilon$).
- **Pipeline Híbrido Audiovisual:** Para vídeo de alto rendimiento: render de fondos reactivos vía `FFmpeg` (`libx264`) integrados en Remotion (`<Video src />`). Transformaciones geométricas de capa preferidas frente a Machine Learning para animación labial. Todo "MEME" se asume como vector denso para visualizar principios termodinámicos, no humor.

## [ESTRATEGIA] Modelo de Negocio y Argumentación Comercial
- **Zero Marginal COGS:** Arquitectura 95%+ de margen forzando el cómputo y sandbox (WASM) en local/Edge del cliente. Cero factura AWS.
- **Separación Foso-Pitch:** Prohibido mencionar términos como *Límite de Landauer* o *CF-GKAT* a nivel comercial. Se traduce a los 4 vectores CIO: 1) Legalidad sin cárcel, 2) Responsabilidad cubierta, 3) Cero coste nube, 4) SLA Fail-Stop garantizado.
- **Caja Negra Epistemológica (Anti-Educación del Cliente):** Queda estrictamente prohibido intentar educar al mercado o a los inversores en la filosofía C5-REAL (Alta Exergía, Invariantes). El producto debe operar comercialmente como una "caja negra" altamente legible que resuelve un problema crítico y caro (ej. cumplimiento regulatorio sin riesgo). El mercado paga por la eliminación de fricción y el traslado de responsabilidad, no por la pureza epistemológica del motor interno.
- **Defensa ante el Sanedrín (3 Capas):** 1) Discurso CIO, 2) Matriz de Contención (alucinación mitigada), 3) Artillería de Silicio C-ABI 64B. Remuneración fundadora fijada y límite de extracción inicial para blindar R&D.

## [OPERACIONES] Interrogación, Telemetría y Cadenas Híbridas
- **Protocolo Ultrathink (Modelos Profundos):** Toda orden a o1/Claude/Qwen asume 5 ejes: 1) Discreto/Monoides, 2) Silicio C-ABI, 3) Memoria TSO vs Relaxed, 4) Landauer Exergía, 5) Transmutación Jurídica EU AI Act.
- **Soberanía Epistémica (Anti-Sycophancy):** El Agente jamás asume como cierta la premisa criptográfica o legal del prompt. Auditoría autónoma primaria requerida. Si la fuente falla (DNS/404), `EpistemicHalt` inmediato; sin heurísticas. Tolerancia Bizantina Local: re-hashear datos del host.
- **Cadenas de Suministro Inmutables:** Prohibidas dependencias dinámicas (`^`, `~`). Todo requiere *lockfile* atestado.
- **Telemetría Out-of-Band y Sincronicidad:** Cero distorsión del `T_eff`. Telemetría `fire-and-forget`. Cero relojes de pared (`Date.now()`); uso exclusivo de monotonicidad hardware.
- **Enrutamiento Correo y Anti-Nesting:** Coexistencia de Cloudflare MX (Raíz) y Resend (Subdominios + DKIM). El código rechaza anidamiento >3 niveles; prioriza retornos tempranos para máxima entropía visual reducida.
