# GITHUB_ANTI_PATTERNS: C5-REAL Sovereign Offsec & Misconfiguration Registry

## 100 GITHUB THREAT VECTORS (GTV)

### I. EXPOSICIÓN DE SECRETOS (001-010)
- **GTV-001** | `OP_SEC_PAT_LEAK`: Hardcodeo de Personal Access Tokens (PATs) (classic) sin fecha de caducidad.
- **GTV-002** | `OP_SEC_CLOUD_KEYS`: Exposición de credenciales de AWS/GCP/Azure en código fuente histórico sin rotación.
- **GTV-003** | `OP_SEC_DOTENV`: Envío accidental de archivos `.env` o configuraciones de producción debido a `.gitignore` omitido o mal parseado.
- **GTV-004** | `OP_SEC_SSH_PRIV`: Compromiso de claves SSH privadas (`id_rsa`) usadas para automatizaciones estáticas o despliegues.
- **GTV-005** | `OP_SEC_SLACK_WEBHOOK`: Fuga de webhooks de Slack o Discord que permiten exfiltración e ingeniería social en los canales.
- **GTV-006** | `OP_SEC_NPM_TOKENS`: Exposición de tokens de publicación de NPM o PyPI permitiendo Supply Chain Attacks en los paquetes del repositorio.
- **GTV-007** | `OP_SEC_GHA_SECRET_ECHO`: Logeo o echoing (`echo ${{ secrets.AWS_KEY }}`) deliberado o por error en logs de GitHub Actions.
- **GTV-008** | `OP_SEC_DB_URI`: Cadenas de conexión (DSN) de bases de datos de producción (AlloyDB, PostgreSQL, Redis) en hardcode en migraciones.
- **GTV-009** | `OP_SEC_ORPHAN_COMMITS`: Fuga de secretos en commits huérfanos o en referencias de Force Pushes que siguen accesibles vía API.
- **GTV-010** | `OP_SEC_GIT_HISTORY_BLINDNESS`: Remoción de un secreto del código actual pero sin auditar la historia ni forzar purgas criptográficas (BFG Repo-Cleaner).

### II. GESTIÓN DE IDENTIDAD Y ACCESO ORGANIZACIONAL (011-020)
- **GTV-011** | `OP_IAM_NO_MFA`: Falta de enforcement de MFA para administradores y dueños de repositorios de la Organización.
- **GTV-012** | `OP_IAM_BASE_PERM_WRITE`: Permisos base de organización seteados en `Write` en lugar de `Read` o `None`, exponiendo la base de código entera.
- **GTV-013** | `OP_IAM_NO_SAML`: Ausencia de SAML/SSO que impide offboarding centralizado, dejando ex-empleados con acceso.
- **GTV-014** | `OP_IAM_STALE_ADMINS`: Cuentas de administradores zombies o bots sobrantes reteniendo poderes `owner`.
- **GTV-015** | `OP_IAM_EXCESS_COLLAB`: Otorgamiento masivo de colaboradores externos con permisos `Admin` o `Maintain`.
- **GTV-016** | `OP_IAM_OAUTH_SCOPES`: Instalación de aplicaciones OAuth externas con alcance ilimitado (`repo` full) que asumen privilegios no requeridos.
- **GTV-017** | `OP_IAM_APP_TOKENS`: Fuga de GitHub App Tokens temporales en builds expuestos.
- **GTV-018** | `OP_IAM_GHOST_TEAMS`: Equipos organizacionales heredando permisos sin auditoría de miembros activos.
- **GTV-019** | `OP_IAM_UNVERIFIED_DOMAINS`: Empleados usando emails de dominios personales (gmail.com) para contribuciones críticas de la organización.
- **GTV-020** | `OP_IAM_AUDIT_LOG_BLINDNESS`: Ignorar la ingestión externa del Audit Log de GitHub (Splunk, Elastic) permitiendo escalamiento silencioso.

### III. CONFIGURACIÓN DEL REPOSITORIO (021-030)
- **GTV-021** | `OP_REP_PUBLIC_FORK`: Repositorio privado donde un usuario crea un fork público forzando fuga estructural.
- **GTV-022** | `OP_REP_OPEN_WIKI`: GitHub Wiki con permisos de escritura abiertos, resultando en defacement y links de Phishing indexados (SEO spam).
- **GTV-023** | `OP_REP_OPEN_ISSUES`: Permisos de issue creation abiertos que permiten ejecución de GH Actions y exfiltración.
- **GTV-024** | `OP_REP_GH_PAGES_LEAK`: Activación accidental de GitHub Pages exponiendo artefactos, directorios y variables buildadas.
- **GTV-025** | `OP_REP_NO_SECURITY_MD`: Falta de Security Policy (`SECURITY.md`), desviando a los whitehats a disclosure público.
- **GTV-026** | `OP_REP_DEPENDABOT_OFF`: Alertas de seguridad inhabilitadas u ocultas por ruido excesivo, ignorando CVEs críticos (ej. Log4j).
- **GTV-027** | `OP_REP_ANON_ACCESS`: Repositorios supuestamente "Open Source" sin mitigación de contribuyentes maliciosos (No rate limiting).
- **GTV-028** | `OP_REP_DISCUSSIONS_DEFACE`: GitHub Discussions abusadas para C2 Command & Control o distribución de payloads maliciosos.
- **GTV-029** | `OP_REP_METADATA_SPOOF`: Manipulación del archivo `CITATION.cff` o tags para ejecutar inyecciones semánticas en la plataforma.
- **GTV-030** | `OP_REP_EXPOSED_WEBHOOKS`: Webhooks expuestos sin verificación HMAC secreta en el receptor, permitiendo despliegues falsos.

### IV. PROTECCIÓN DE RAMAS (BRANCH PROTECTION) (031-040)
- **GTV-031** | `OP_BPR_NO_PROTECTION`: Ramas de producción (`main` / `master`) carentes de protección, permitiendo Force Push directo.
- **GTV-032** | `OP_BPR_ADMIN_BYPASS`: Administradores capaces de bypassear controles de Pull Request, rompiendo la trazabilidad determinista.
- **GTV-033** | `OP_BPR_NO_REVIEWS`: Falta de política `Require pull request reviews`, permitiendo merge de código hostil unilateralmente.
- **GTV-034** | `OP_BPR_STALE_APPROVALS`: Permiso de merge persistente tras updates (push) posteriores a la aprobación del PR (inyección post-review).
- **GTV-035** | `OP_BPR_CODE_OWNER_BYPASS`: Ausencia de enforcement de Code Owners en archivos y flujos de infraestructura crítica (`.github/`).
- **GTV-036** | `OP_BPR_STATUS_CHECK_SKIP`: Status checks de CI/CD pasables de largo, permitiendo merge con fallos de compilación o tests.
- **GTV-037** | `OP_BPR_NO_SIG_VERIFY`: Falta de requerimiento estricto para Commits Firmados (GPG/SSH), posibilitando Committer Spoofing (Suplantación de identidad).
- **GTV-038** | `OP_BPR_LINEAR_HISTORY_OFF`: Fusión sucia que dificulta auditoría forense y rollback criptográfico (AX-041).
- **GTV-039** | `OP_BPR_MERGE_QUEUE_RACE`: Bypass de restricciones a través de manipulación temporal de la Merge Queue.
- **GTV-040** | `OP_BPR_TAG_POISONING`: Tags sin protección permitiendo que dependencias ancladas (Pinned Dependencies) muten al reescribir un Tag antiguo.

### V. GITHUB ACTIONS: INYECCIÓN Y PAYLOAD (041-050)
- **GTV-041** | `OP_GHA_CMD_INJECT_ISSUE`: Inyección de comandos RCE vía `${{ github.event.issue.title }}` o `body` sin sanear en bloque `run`.
- **GTV-042** | `OP_GHA_CMD_INJECT_PR`: Ejecución arbitraria a partir de `${{ github.event.pull_request.head.ref }}` (Branch Name RCE).
- **GTV-043** | `OP_GHA_UNTRUSTED_PR_RUN`: `pull_request_target` event corriendo código del Fork (RCE hostil en contexto con secretos).
- **GTV-044** | `OP_GHA_SCRIPT_EVAL`: Uso abusivo de `actions/github-script` evaluando input sucio de variables de entorno de GitHub.
- **GTV-045** | `OP_GHA_PWN_REQUEST`: Ejecución automática de tests sin sandboxing (ej. tests unitarios) en código forked usando el evento `pull_request`.
- **GTV-046** | `OP_GHA_ENV_POISON`: Modificación hostil de variables usando `${GITHUB_ENV}` export para afectar scripts posteriores.
- **GTV-047** | `OP_GHA_PATH_HIJACK`: Sobrescritura de ejecutables legítimos a través de la inyección de paths en `${GITHUB_PATH}`.
- **GTV-048** | `OP_GHA_INPUT_SHELL`: Inyección en custom Actions al no usar arreglos seguros para los argumentos, confiando en expansión del shell.
- **GTV-049** | `OP_GHA_PAYLOAD_POISON`: Lectura insegura del archivo local `github.event.json` que fue modificado por procesos anteriores.
- **GTV-050** | `OP_GHA_CHECK_SUITE_RCE`: Abuso de los eventos de `check_suite` o `check_run` que asumen input confiable y evalúan strings.

### VI. GITHUB ACTIONS: RUNNERS Y ENTORNO (051-060)
- **GTV-051** | `OP_GHA_RUNNER_PERSIST`: Uso de Self-Hosted Runners no efímeros que no limpian su estado, permitiendo Sandbox Escape persistente.
- **GTV-052** | `OP_GHA_RUNNER_DOCKER_SOCK`: Self-Hosted runners exponiendo el socket de Docker (`/var/run/docker.sock`) garantizando root host en escape.
- **GTV-053** | `OP_GHA_PUBLIC_RUNNER`: Conexión de runners locales a repositorios públicos permitiendo que cualquier persona ejecute mineros o exfiltre la red local.
- **GTV-054** | `OP_GHA_RUNNER_LABELS_HIJACK`: Manipulación de las etiquetas (labels) del runner para enrutar workflows de prod a runners de dev comprometidos.
- **GTV-055** | `OP_GHA_OOM_DOS`: Ataque de consumo de memoria y CPU masivos contra runners limitados y costosos de GitHub.
- **GTV-056** | `OP_GHA_CACHE_POISON`: Envenenamiento de `actions/cache` en un branch que luego se propaga y es ejecutado por el branch `main`.
- **GTV-057** | `OP_GHA_ARTIFACT_OVERLAP`: Sobrescritura hostil o manipulación (Zip Slip) usando `actions/upload-artifact` sin sanitización.
- **GTV-058** | `OP_GHA_SHARED_WORKSPACE`: Interacción cruzada en `/home/runner/work` donde un step malicioso esconde un backdoor que un step legítimo posterior ejecuta.
- **GTV-059** | `OP_GHA_VM_ESCAPE`: Escapes de virtualización o side-channels a nivel micro-arquitectura usando la máquina de Actions para extraer memoria de tenantes colindantes.
- **GTV-060** | `OP_GHA_IDLE_MINING`: Workflows que tras fallar inician bucles de red (Mining o DoS P2P) manteniéndose vivos hasta el Timeout máximo (360 min).

### VII. PERMISOS Y TOKENS GITHUB ACTIONS (061-070)
- **GTV-061** | `OP_GHA_BROAD_TOKEN`: Uso del token `GITHUB_TOKEN` con permisos `contents: write` o `admin` por defecto en todos los workflows.
- **GTV-062** | `OP_GHA_NO_MIN_SCOPES`: Omisión del bloque de `permissions: {}` dejando los scopes de GITHUB_TOKEN permisivos implícitamente.
- **GTV-063** | `OP_GHA_TOKEN_LEAK`: Fuga del `GITHUB_TOKEN` hacia logs externos al pasarlo como query parameter en vez de header Authorization.
- **GTV-064** | `OP_GHA_ISSUE_WRITE_SPOOF`: Uso de `issues: write` para crear falsos positivos o phishing con la identidad de github-actions[bot].
- **GTV-065** | `OP_GHA_PR_WRITE_DEFACE`: Workflow capaz de aprobar PRs de manera autónoma sin supervisión.
- **GTV-066** | `OP_GHA_ACTION_BOT_COMMIT`: Código inyectando backdoors mediante un `git commit` automatizado a nombre de Actions Bot.
- **GTV-067** | `OP_GHA_SECRET_CROSS`: Inyección de un workflow no confiable a un environment que requiere Secrets sin un manual approval step.
- **GTV-068** | `OP_GHA_ENV_BYPASS`: Bypass de Environment Protection rules (requerimiento de reviewers) modificando el nombre del environment de destino.
- **GTV-069** | `OP_GHA_DEPLOY_KEY_ABUSE`: Almacenamiento de un token PAT global en los Secrets del Repo en lugar de usar un `GITHUB_TOKEN` de corto alcance.
- **GTV-070** | `OP_GHA_WORKFLOW_WRITE`: Fuga de permisos `actions: write` y `workflows: write` que permiten reescribir y exfiltrar permanentemente sin dejar rastro de commit manual.

### VIII. SUPPLY CHAIN & TERCEROS (071-080)
- **GTV-071** | `OP_SUP_UNPINNED_ACTIONS`: Uso de Actions de terceros referenciados por ramas mutables (ej. `@master` o `@v1`) en vez de commit SHAs estáticos.
- **GTV-072** | `OP_SUP_TYPOSQUATTING`: Instalación de un Action o paquete con typo-squatting (`actions/chekout@v3`).
- **GTV-073** | `OP_SUP_CONFUSION_ATTACK`: Dependency Confusion; inyección de un paquete de dependencia privada subida a un registro público con versión alta.
- **GTV-074** | `OP_SUP_MALICIOUS_FORK_ACTION`: Consumo de un GitHub Action proveniente de un Fork sin mantenimiento (Hijack de Maintainer).
- **GTV-075** | `OP_SUP_DOCKER_DIGEST`: Referencias a imágenes de Docker (`container: node:16`) sin hash digest, vulnerables a inyección upstream.
- **GTV-076** | `OP_SUP_RELEASE_POISON`: Modificación post-publicación de archivos binarios o releases adjuntos a un Tag.
- **GTV-077** | `OP_SUP_CURL_BASH`: El clásico `curl | bash` en los build scripts de CI/CD importando código estocástico en runtime.
- **GTV-078** | `OP_SUP_GPG_KEY_LEAK`: Fuga o débil custodia de claves GPG que firman artefactos de release.
- **GTV-079** | `OP_SUP_DEPENDABOT_HIJACK`: Inserción maliciosa en repos dependientes que fuerzan a Dependabot a sugerir PRs hostiles, dándoles pátina de legitimidad.
- **GTV-080** | `OP_SUP_MARKETPLACE_BLIND`: Uso de Actions no verificadas por el creador en el Marketplace y sin auditoría interna.

### IX. FORENSE, REGISTROS Y PROCEDIMIENTOS (081-090)
- **GTV-081** | `OP_FOR_LOG_SPOOF`: Manipulación del output para falsificar el éxito del build en el Audit Trail (`echo "Success" && exit 0`).
- **GTV-082** | `OP_FOR_HISTORY_REWRITE`: Uso de `git push --force` masivo por un admin para tapar o esconder un vector ofensivo, destruyendo la cadena causal (AX-041).
- **GTV-083** | `OP_FOR_GHOST_COMMITTER`: Uso del flag `--author` en git para asignar la culpa de un commit a un desarrollador senior de la organización (Suplantación).
- **GTV-084** | `OP_FOR_API_EXHAUST`: Cierre de auditorías forzando agotamiento de la GitHub API (Rate Limit DoS).
- **GTV-085** | `OP_FOR_NO_SBOM`: Ausencia de Software Bill of Materials generado determinísticamente durante el flujo de build y release.
- **GTV-086** | `OP_FOR_UNTRACKED_BINARIES`: Commits de binarios y `dlls/so` pre-compilados en repositorios en lugar de construirlos desde source.
- **GTV-087** | `OP_FOR_ISSUE_HISTORY_DELETE`: Remoción física de un comment o issue que contiene el reporte de una vulnerabilidad, perdiendo la trazabilidad P0.
- **GTV-088** | `OP_FOR_FORK_NETWORK_BLINDNESS`: Falta de auditoría a la red de Forks donde un código privado fue expuesto antes de hacerlo de vuelta privado.
- **GTV-089** | `OP_FOR_NO_SEC_ALERTS`: Secret Scanning alerts silenciadas sistemáticamente asumiéndolas falsos positivos, normalizando la desviación.
- **GTV-090** | `OP_FOR_SAGA_ABORT_MASKING`: Fallos de GitHub actions encriptados o enmascarados como Timeout cuando realmente exfiltraron estado.

### X. VULNERABILIDADES ARQUITECTÓNICAS Y SOCIAL ENGINEERING (091-100)
- **GTV-091** | `OP_SOC_OWNER_TAKEOVER`: Adquisición de dominio caducado o namespace abandonado para resucitar una organización y secuestrar la cadena de software (Repo Hijack).
- **GTV-092** | `OP_SOC_MALICIOUS_PR_BODY`: Inyección de payloads y scripts JS o CSS en el markdown del PR description para comprometer a quien lo revisa.
- **GTV-093** | `OP_SOC_REPO_STAR_SPOOFING`: Compra de Stars y Forks automatizados para proveer falsa legitimidad a un repositorio C2 o de Phishing.
- **GTV-094** | `OP_SOC_PHISHING_COMMITS`: URLs engañosas insertadas en los comentarios del código apuntando a payloads C2 (`http://g1thub.com/...`).
- **GTV-095** | `OP_SOC_BACKDOOR_DEPENDENCY_PR`: Enviar correcciones gramaticales (typos) en el PR mientras se inyecta silenciosamente una subdependencia comprometida (Trojan Review).
- **GTV-096** | `OP_SOC_SPONSOR_FRAUD`: Manipulación de GitHub Sponsors insertando crypto-wallets asociadas a grupos maliciosos.
- **GTV-097** | `OP_ARQ_MONOREPO_OOM`: Saturación o envenenamiento de los triggers condicionales de GHA en un monorepo para ejecutar 10,000 builds en paralelo (FinOps DoS).
- **GTV-098** | `OP_ARQ_REUSABLE_WORKFLOW_BYPASS`: Bypass de los chequeos estáticos llamando a `workflow_call` con contextos o secrets mutados.
- **GTV-099** | `OP_ARQ_COMPOSITE_ACTION_LEAK`: Pasaje de contexto global hacia Composite Actions sin desinfección, rompiendo los límites de acceso.
- **GTV-100** | `OP_ARQ_ORACLE_GHA_ATTACK`: Uso repetitivo de `run` logs y responses para adivinar el contenido de secretos byte por byte midiendo el tiempo de respuesta y errores.

---
> **Validación C5-REAL (ExergyGuard):** Esta matriz define el perímetro de invariantes defensivos y asimétricos frente al ecosistema de GitHub, integrando la termodinámica de Ouroboros. Anergía = 0.
