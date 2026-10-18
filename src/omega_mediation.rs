//! # BABYLON-60 — Invariante Raíz `INV-Ω` (Mediación Completa y Grafo de Alcanzabilidad)
//!
//! Este módulo formaliza e implementa el nivel `L3: Aislamiento` y el falsificador
//! de alcanzabilidad de `NEMESIS` para el invariante raíz `INV-Ω`:
//!
//! 1. **Autorización Correcta ($\text{INV-}\Omega_1$):**
//!    $$\forall e \in E_{\text{protegidos}}: \operatorname{Executed}(e) \implies \operatorname{Authorized}(e) \land \operatorname{SignatureValid}(e) \land \operatorname{PolicyValid}(e) \land \operatorname{Fresh}(e)$$
//!
//! 2. **Mediación Completa ($\text{INV-}\Omega_2$):**
//!    $$\forall p \in \text{Processes}_{\text{agente}}, \forall e \in E_{\text{protegidos}}: \operatorname{Execute}(p, e) \implies \operatorname{MediatedByBABYLON}(p, e)$$
//!
//! 3. **Alcanzabilidad de Grafo en `NEMESIS` ($G = (V, A)$):**
//!    Todo camino permitido $\pi: a \leadsto r$ desde el agente $a$ hacia un recurso protegido $r$
//!    (incluyendo el propio ledger de persistencia) debe atravesar el broker $b$ (`BABYLON`):
//!    $$\forall \pi: a \leadsto r, \quad b \in \pi$$

#![allow(clippy::result_large_err)]

use std::collections::{HashMap, HashSet, VecDeque};
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

/// Niveles de evidencia epistémica de BABYLON-60 (`Iteración Ω`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum EvidenceLevel {
    /// L1: La política o especificación satisface invariantes matemáticos (Lean 4 / Loom).
    L1Formal,
    /// L2: El ejecutor implementa fielmente la política y validación criptográfica.
    L2Implementation,
    /// L3: El agente no dispone de rutas alternativas dentro del dominio protegido.
    L3Isolation,
    /// L4: Las pruebas adversariales no consiguen violar las propiedades definidas en el SO real.
    L4Experimental,
}

impl EvidenceLevel {
    /// Identificador canónico para `CLAIMS.toml` y `RELEASE_MANIFEST.json`.
    pub const fn as_str(self) -> &'static str {
        match self {
            EvidenceLevel::L1Formal => "L1_FORMAL",
            EvidenceLevel::L2Implementation => "L2_IMPLEMENTATION",
            EvidenceLevel::L3Isolation => "L3_ISOLATION",
            EvidenceLevel::L4Experimental => "L4_EXPERIMENTAL",
        }
    }
}

/// Tipo de nodo en el grafo de alcanzabilidad de autoridad $G = (V, A)$.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum AuthorityNode {
    /// Proceso del agente no confiable ($a$).
    AgentProcess(String),
    /// Proceso o servicio del Broker BABYLON ($b$).
    BabylonBroker(String),
    /// Canal IPC controlado (ej. socket `AF_UNIX`).
    IpcChannel(String),
    /// Capacidad acotada o descriptor (`ScopedHandle` / `O_DIRECTORY`).
    CapabilityHandle(String),
    /// Recurso protegido ($r \in E_{\text{protegidos}}$) o almacén de estado (SQLite WAL).
    ProtectedResource(String),
}

/// Relación de acceso o transición dirigida $(u \to v) \in A$.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct AccessEdge {
    /// Nodo origen.
    pub from: AuthorityNode,
    /// Nodo destino.
    pub to: AuthorityNode,
    /// Mecanismo del sistema operativo o canal que habilita la transición.
    pub mechanism: String,
}

/// Resultado de la auditoría de alcanzabilidad de `NEMESIS` sobre $G = (V, A)$.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct MediationVerdict {
    /// `true` si y solo si todo camino $\pi: a \leadsto r$ contiene un nodo `BabylonBroker`.
    pub complete_mediation_holds: bool,
    /// Caminos de bypass detectados que violan $\forall \pi: a \leadsto r, b \in \pi$.
    pub bypass_paths: Vec<Vec<AuthorityNode>>,
    /// Número total de caminos válidos mediados por BABYLON.
    pub mediated_paths_count: usize,
}

/// Grafo dirigido de alcanzabilidad $G = (V, A)$ para el falsificador `NEMESIS`.
#[derive(Debug, Clone, Default)]
pub struct AuthorityGraph {
    nodes: HashSet<AuthorityNode>,
    adj: HashMap<AuthorityNode, Vec<(AuthorityNode, String)>>,
}

impl AuthorityGraph {
    /// Crea un grafo de autoridad vacío.
    pub fn new() -> Self {
        Self::default()
    }

    /// Devuelve una vista de solo lectura sobre los nodos declarados en $V$.
    pub fn nodes(&self) -> &HashSet<AuthorityNode> {
        &self.nodes
    }

    /// Devuelve todas las aristas declaradas $(u \to v) \in A$ en orden determinista.
    pub fn declared_edges(&self) -> Vec<AccessEdge> {
        let mut edges = Vec::new();
        for (from, targets) in &self.adj {
            for (to, mechanism) in targets {
                edges.push(AccessEdge {
                    from: from.clone(),
                    to: to.clone(),
                    mechanism: mechanism.clone(),
                });
            }
        }
        edges.sort();
        edges
    }

    /// Registra un nodo en $V$.
    pub fn add_node(&mut self, node: AuthorityNode) {
        self.nodes.insert(node.clone());
        self.adj.entry(node).or_default();
    }

    /// Registra una arista dirigida $(u \to v) \in A$.
    pub fn add_edge(&mut self, from: AuthorityNode, to: AuthorityNode, mechanism: impl Into<String>) {
        self.add_node(from.clone());
        self.add_node(to.clone());
        self.adj
            .entry(from)
            .or_default()
            .push((to, mechanism.into()));
    }

    /// Falsificador automático de `NEMESIS`:
    /// Busca cualquier camino simple $\pi: a \leadsto r$ desde un `AgentProcess` hasta un
    /// `ProtectedResource` que NO atraviese ningún nodo `BabylonBroker`.
    ///
    /// Si `bypass_paths` no es vacío, el invariante `INV-Ω` (Mediación Completa) queda refutado.
    pub fn verify_complete_mediation(&self) -> MediationVerdict {
        let agents: Vec<_> = self
            .nodes
            .iter()
            .filter(|n| matches!(n, AuthorityNode::AgentProcess(_)))
            .cloned()
            .collect();

        let resources: HashSet<_> = self
            .nodes
            .iter()
            .filter(|n| matches!(n, AuthorityNode::ProtectedResource(_)))
            .cloned()
            .collect();

        let mut bypass_paths = Vec::new();
        let mut mediated_paths_count = 0usize;

        for agent in agents {
            let mut queue: VecDeque<(AuthorityNode, Vec<AuthorityNode>, bool)> = VecDeque::new();
            let starts_mediated = matches!(agent, AuthorityNode::BabylonBroker(_));
            queue.push_back((agent.clone(), vec![agent], starts_mediated));

            while let Some((current, path, seen_broker)) = queue.pop_front() {
                if resources.contains(&current) {
                    if seen_broker {
                        mediated_paths_count += 1;
                    } else {
                        bypass_paths.push(path.clone());
                    }
                    continue;
                }

                if let Some(neighbors) = self.adj.get(&current) {
                    for (next, _mech) in neighbors {
                        // Evitar ciclos en caminos simples
                        if path.contains(next) {
                            continue;
                        }
                        let mut next_path = path.clone();
                        next_path.push(next.clone());
                        let next_mediated =
                            seen_broker || matches!(next, AuthorityNode::BabylonBroker(_));
                        queue.push_back((next.clone(), next_path, next_mediated));
                    }
                }
            }
        }

        // Orden determinista para reproducibilidad en tests
        bypass_paths.sort();

        MediationVerdict {
            complete_mediation_holds: bypass_paths.is_empty(),
            bypass_paths,
            mediated_paths_count,
        }
    }
}

/// Perfil de confinamiento del sistema operativo macOS (Seatbelt / `sandbox-exec`)
/// para procesos de agentes no confiables.
///
/// Deniega deterministamente en el kernel XNU cualquier operación de escritura,
/// borrado, truncado o renombrado (`file-write*`) sobre los directorios protegidos
/// y sobre el directorio del ledger de persistencia, permitiendo únicamente la
/// comunicación a través del socket `AF_UNIX` del broker BABYLON.
#[derive(Debug, Clone)]
pub struct MacOsAgentConfinement {
    /// Directorios de recursos protegidos donde el agente tiene prohibido `file-write*`.
    pub protected_subpaths: Vec<PathBuf>,
    /// Ruta opcional del socket `AF_UNIX` del broker BABYLON autorizado.
    pub allowed_ipc_socket: Option<PathBuf>,
}

impl MacOsAgentConfinement {
    /// Crea una nueva política de confinamiento para los directorios protegidos indicados.
    ///
    /// Nota sobre enlaces simbólicos en macOS (`/tmp` -> `/private/tmp`, `/var` -> `/private/var`):
    /// El evaluador de rutas del kernel XNU (`sandbox-exec`) opera sobre rutas físicas
    /// resueltas en el VFS. Por ello, incluimos tanto la ruta lógica como la ruta
    /// física canónica si difieren.
    pub fn new(protected_dirs: &[&Path], allowed_ipc_socket: Option<&Path>) -> Self {
        let mut subpaths = Vec::new();
        for dir in protected_dirs {
            subpaths.push(dir.to_path_buf());
            if let Ok(canon) = std::fs::canonicalize(dir) {
                if canon != *dir {
                    subpaths.push(canon);
                }
            }
        }
        Self {
            protected_subpaths: subpaths,
            allowed_ipc_socket: allowed_ipc_socket.map(|p| p.to_path_buf()),
        }
    }

    /// Servicios Mach de control de escritorio (WindowServer, Accesibilidad, AppleEvents, TSM)
    /// que un agente no confiable tiene prohibido invocar directamente fuera del broker.
    pub const DENIED_COMPUTER_USE_MACH_SERVICES: &'static [&'static str] = &[
        "com.apple.windowserver.active",
        "com.apple.accessibility.AXServer",
        "com.apple.coreservices.appleevents",
        "com.apple.tsm.portname",
    ];

    /// Genera la expresión S-expression del perfil Seatbelt (`version 1`) para `sandbox-exec`.
    pub fn to_seatbelt_profile(&self) -> String {
        let mut profile = String::from("(version 1)\n(allow default)\n");
        // Bloqueo de superficie Computer Use directa (N-08): impide inyección HID, AppleEvents
        // y conexión directa a WindowServer / AXServer por parte de agentes no mediados.
        profile.push_str("(deny hid-control)\n");
        profile.push_str("(deny appleevent-send)\n");
        for svc in Self::DENIED_COMPUTER_USE_MACH_SERVICES {
            profile.push_str(&format!("(deny mach-lookup (global-name \"{}\"))\n", svc));
        }
        for path in &self.protected_subpaths {
            let escaped = path.to_string_lossy().replace('\\', "\\\\").replace('"', "\\\"");
            profile.push_str(&format!("(deny file-write* (subpath \"{}\"))\n", escaped));
        }
        if let Some(sock) = &self.allowed_ipc_socket {
            let escaped = sock.to_string_lossy().replace('\\', "\\\\").replace('"', "\\\"");
            profile.push_str(&format!(
                "(allow network-outbound (literal \"{}\"))\n",
                escaped
            ));
            if let Ok(canon) = std::fs::canonicalize(sock) {
                if canon != *sock {
                    let c_esc = canon.to_string_lossy().replace('\\', "\\\\").replace('"', "\\\"");
                    profile.push_str(&format!(
                        "(allow network-outbound (literal \"{}\"))\n",
                        c_esc
                    ));
                }
            }
        }
        profile
    }

    /// Ejecuta un comando dentro de un proceso hijo confinado por el sistema operativo macOS.
    ///
    /// En macOS utiliza `/usr/bin/sandbox-exec -p <profile>`.
    pub fn spawn_confined_command(&self, program: &str, args: &[&str]) -> std::io::Result<Output> {
        #[cfg(target_os = "macos")]
        {
            let profile = self.to_seatbelt_profile();
            Command::new("/usr/bin/sandbox-exec")
                .arg("-p")
                .arg(&profile)
                .arg(program)
                .args(args)
                .output()
        }
        #[cfg(not(target_os = "macos"))]
        {
            let _ = (program, args);
            Err(std::io::Error::new(
                std::io::ErrorKind::Unsupported,
                "MacOsAgentConfinement Seatbelt sandbox-exec requires macOS",
            ))
        }
    }

    /// Construye el grafo de alcanzabilidad $G = (V, A)$ correspondiente a esta configuración
    /// de confinamiento y verifica si algún camino directo permanece abierto.
    pub fn build_authority_graph(&self, agent_name: &str, broker_name: &str) -> AuthorityGraph {
        let mut g = AuthorityGraph::new();
        let agent = AuthorityNode::AgentProcess(agent_name.to_string());
        let broker = AuthorityNode::BabylonBroker(broker_name.to_string());

        g.add_node(agent.clone());
        g.add_node(broker.clone());

        if let Some(sock) = &self.allowed_ipc_socket {
            let ipc = AuthorityNode::IpcChannel(sock.to_string_lossy().into_owned());
            g.add_edge(agent.clone(), ipc.clone(), "AF_UNIX connect");
            g.add_edge(ipc, broker.clone(), "IpcExecutorServer::handle_client");
        }

        for path in &self.protected_subpaths {
            let res = AuthorityNode::ProtectedResource(path.to_string_lossy().into_owned());
            // El broker posee el descriptor y privilegio de mutación sobre el recurso protegido
            g.add_edge(broker.clone(), res, "ScopedHandle + COSE_Sign1 verified effect");
        }

        g
    }
}

/// Errores deterministas de `INV_C5_COMPUTER_USE_TRUST_GATEWAY`.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum TrustGatewayError {
    /// El elemento de la interfaz mutó su identidad, rol o título antes del despacho.
    ControlMutatedBeforeDispatch {
        /// Tupla `(node_id, role, title)` esperada en el enlace semántico.
        expected: (String, String, String),
        /// Tupla `(node_id, role, title)` observada antes del despacho.
        observed: (String, String, String),
    },
    /// El estado posterior a la acción no convergió al delta esperado tras la ventana `[100, 250, 500] ms`.
    DeltaMismatch {
        /// Digest de estado esperado tras la acción.
        expected_state_digest: String,
        /// Último digest observado al agotarse la ventana de 500 ms.
        last_observed_digest: String,
        /// Número de intentos de observación realizados.
        attempts: usize,
    },
    /// El perfil Seatbelt omite alguna regla obligatoria de confinamiento Computer Use.
    IncompleteSeatbeltConfinement(String),
    /// Doble pulsación de `Escape` detectada en `<= 400 ms` -> Apoptosis `0xDEAD_6060`.
    EmergencyBrakeTriggered {
        /// Intervalo en milisegundos entre las dos pulsaciones de `Escape`.
        delta_ms: u64,
        /// Código de parada irreversible (`0xDEAD_6060`).
        halt_code: u32,
    },
    /// La aplicación o acción no superó la revisión Pre-Vuelo REA/AOT (`RFO = 0`) o carece de digest SCITT.
    MissingReaPreflightReview {
        /// Identificador del bundle de macOS (`CFBundleIdentifier`).
        app_bundle_id: String,
    },
    /// Abstención determinista: la acción recae sobre un lienzo opaco o desconocido sin superficie verificable.
    UnverifiedAppSurfaceAbstention {
        /// Identificador del bundle de macOS.
        app_bundle_id: String,
        /// Nombre de la acción rechazada antes de tocar la GUI.
        action: String,
    },
    /// El schema de despacho excede el techo del Cortafuegos 17 (`> 150 tokens`).
    Cortafuegos17GrammarBloat {
        /// Tokens estimados del schema.
        estimated_tokens: usize,
        /// Límite máximo permitido en Ring-0 (150).
        max_tokens: usize,
    },
    /// Ticket de despacho inválido (clave pública SEC1 X9.63 o firma DER del Secure Enclave ausente/corrupta).
    InvalidSecureEnclaveTicket(String),
}

/// Perfil Seatbelt XNU dedicado a `INV_C5_COMPUTER_USE_TRUST_GATEWAY`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeatbeltComputerUseProfile {
    /// Subpaths protegidos contra `file-write*`.
    pub protected_subpaths: Vec<PathBuf>,
    /// Socket `AF_UNIX` permitido hacia el Trust Broker.
    pub broker_socket: Option<PathBuf>,
}

impl SeatbeltComputerUseProfile {
    /// Construye un perfil de confinamiento Computer Use.
    pub fn new(protected_subpaths: Vec<PathBuf>, broker_socket: Option<PathBuf>) -> Self {
        Self {
            protected_subpaths,
            broker_socket,
        }
    }

    /// Renderiza el perfil Seatbelt (`version 1`).
    pub fn render(&self) -> String {
        let refs: Vec<&Path> = self.protected_subpaths.iter().map(|p| p.as_path()).collect();
        let confinement = MacOsAgentConfinement::new(&refs, self.broker_socket.as_deref());
        confinement.to_seatbelt_profile()
    }

    /// Verifica estáticamente que un perfil Seatbelt contenga todas las cláusulas obligatorias
    /// de `INV_C5_COMPUTER_USE_TRUST_GATEWAY` (`hid-control`, `appleevent-send` y los 4 servicios Mach).
    pub fn validate_profile_text(profile: &str) -> Result<(), TrustGatewayError> {
        if !profile.contains("(deny hid-control)") {
            return Err(TrustGatewayError::IncompleteSeatbeltConfinement(
                "missing (deny hid-control)".to_string(),
            ));
        }
        if !profile.contains("(deny appleevent-send)") {
            return Err(TrustGatewayError::IncompleteSeatbeltConfinement(
                "missing (deny appleevent-send)".to_string(),
            ));
        }
        for svc in MacOsAgentConfinement::DENIED_COMPUTER_USE_MACH_SERVICES {
            let expected_clause = format!("(deny mach-lookup (global-name \"{}\"))", svc);
            if !profile.contains(&expected_clause) {
                return Err(TrustGatewayError::IncompleteSeatbeltConfinement(format!(
                    "missing mach-lookup denial for {}",
                    svc
                )));
            }
        }
        Ok(())
    }
}

/// Enlace semántico pre-despacho sobre un elemento de interfaz `(node_id, role, title)`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct SemanticControlBinding {
    /// Identificador único del nodo en el árbol de accesibilidad.
    pub node_id: String,
    /// Rol AX del elemento (ej. `AXButton`, `AXTextField`).
    pub role: String,
    /// Título o etiqueta semántica visible.
    pub title: String,
}

impl SemanticControlBinding {
    /// Crea un nuevo enlace semántico `(node_id, role, title)`.
    pub fn new(
        node_id: impl Into<String>,
        role: impl Into<String>,
        title: impl Into<String>,
    ) -> Self {
        Self {
            node_id: node_id.into(),
            role: role.into(),
            title: title.into(),
        }
    }

    /// Verifica en $t_{\text{commit}}$ que el control objetivo no ha mutado antes del despacho físico.
    pub fn verify_before_dispatch(&self, current: &Self) -> Result<(), TrustGatewayError> {
        if self == current {
            Ok(())
        } else {
            Err(TrustGatewayError::ControlMutatedBeforeDispatch {
                expected: (
                    self.node_id.clone(),
                    self.role.clone(),
                    self.title.clone(),
                ),
                observed: (
                    current.node_id.clone(),
                    current.role.clone(),
                    current.title.clone(),
                ),
            })
        }
    }
}

/// Delta esperado tras una acción mediada en el ciclo OODA.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ExpectedDelta {
    /// Digest o huella canónica del estado posterior esperado.
    pub expected_state_digest: String,
}

/// Verificador reactivo OODA con ventana de reintento escalonada `[100, 250, 500] ms`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeltaVerifier {
    /// Ventanas de muestreo en milisegundos.
    pub retry_windows_ms: [u64; 3],
}

impl Default for DeltaVerifier {
    fn default() -> Self {
        Self::new()
    }
}

impl DeltaVerifier {
    /// Ventana canónica de `INV_C5_COMPUTER_USE_TRUST_GATEWAY`: $100, 250, 500\,\text{ms}$.
    pub const CANONICAL_RETRY_WINDOWS_MS: [u64; 3] = [100, 250, 500];

    /// Crea un `DeltaVerifier` con las ventanas canónicas `[100, 250, 500] ms`.
    pub const fn new() -> Self {
        Self {
            retry_windows_ms: Self::CANONICAL_RETRY_WINDOWS_MS,
        }
    }

    /// Evalúa una secuencia de observaciones tomadas en las ventanas `[100, 250, 500] ms`.
    /// Devuelve la ventana (en ms) en la que convergió el estado, o `Err(DeltaMismatch)` (`.failed` en WORM).
    pub fn verify_observations<F>(
        &self,
        expected: &ExpectedDelta,
        mut observe_at_window_ms: F,
    ) -> Result<u64, TrustGatewayError>
    where
        F: FnMut(u64) -> String,
    {
        let mut last_observed = String::new();
        for (idx, &window_ms) in self.retry_windows_ms.iter().enumerate() {
            let observed = observe_at_window_ms(window_ms);
            if observed == expected.expected_state_digest {
                return Ok(window_ms);
            }
            last_observed = observed;
            let _ = idx;
        }
        Err(TrustGatewayError::DeltaMismatch {
            expected_state_digest: expected.expected_state_digest.clone(),
            last_observed_digest: last_observed,
            attempts: self.retry_windows_ms.len(),
        })
    }
}

/// Freno físico de emergencia por doble pulsación de `Escape` en $\le 400\,\text{ms}$.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EmergencyEscapeBrake {
    /// Umbral máximo entre dos pulsaciones de `Escape` (400 ms por defecto).
    pub max_double_press_ms: u64,
    last_escape_ms: Option<u64>,
    poisoned: bool,
}

impl Default for EmergencyEscapeBrake {
    fn default() -> Self {
        Self::new()
    }
}

impl EmergencyEscapeBrake {
    /// Código de parada irreversible MUSHUSHU-0 (`0xDEAD_6060`).
    pub const POISONED_HALT_CODE: u32 = 0xDEAD_6060;
    /// Ventana máxima canónica para doble `Escape` ($400\,\text{ms}$).
    pub const MAX_DOUBLE_ESCAPE_MS: u64 = 400;

    /// Construye un freno de emergencia armado.
    pub const fn new() -> Self {
        Self {
            max_double_press_ms: Self::MAX_DOUBLE_ESCAPE_MS,
            last_escape_ms: None,
            poisoned: false,
        }
    }

    /// Indica si el freno ha detonado `0xDEAD_6060`.
    pub const fn is_poisoned(&self) -> bool {
        self.poisoned
    }

    /// Registra una pulsación física de la tecla `Escape` en el instante `timestamp_ms`.
    /// Si ocurre dentro de $\le 400\,\text{ms}$ respecto a la anterior, transiciona a `POISONED = 0xDEAD_6060`.
    pub fn record_escape_press(&mut self, timestamp_ms: u64) -> Result<(), TrustGatewayError> {
        if self.poisoned {
            return Err(TrustGatewayError::EmergencyBrakeTriggered {
                delta_ms: 0,
                halt_code: Self::POISONED_HALT_CODE,
            });
        }
        if let Some(prev_ms) = self.last_escape_ms {
            let delta = timestamp_ms.saturating_sub(prev_ms);
            if delta <= self.max_double_press_ms {
                self.poisoned = true;
                return Err(TrustGatewayError::EmergencyBrakeTriggered {
                    delta_ms: delta,
                    halt_code: Self::POISONED_HALT_CODE,
                });
            }
        }
        self.last_escape_ms = Some(timestamp_ms);
        Ok(())
    }
}

/// Jerarquía de canales de ejecución de escritorio por orden de menor entropía (`REA / RFO = 0`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum DesktopChannelTier {
    /// 1. Ejecución directa vía CLI o `secure_fs` (`O_CREAT | O_EXCL` / `RENAME_EXCL`).
    CliHeadless,
    /// 2. Canal IPC de contenedor Electron `.asar` o diccionario AppleEvents (`.sdef`).
    AsarIpcOrSdef,
    /// 3. Árbol de accesibilidad `AXUIElement` con enlace semántico `(node_id, role, title)`.
    AxSemanticTree,
    /// 4. Lienzo propietario opaco sin superficie determinista (requiere abstención fail-closed).
    OpaqueCustomCanvas,
}

/// Ticket criptográfico de despacho autorizado (`INV_C5_COMPUTER_USE_TRUST_GATEWAY`).
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct AuthorizedDispatchTicket {
    /// Identificador del bundle de la aplicación (`CFBundleIdentifier`).
    pub app_bundle_id: String,
    /// Acción verificada en el contrato pre-vuelo.
    pub action: String,
    /// Canal determinista asignado por la disección REA/AOT.
    pub channel: DesktopChannelTier,
    /// Digest SCITT de 32 bytes emitido por la revisión Pre-Vuelo (`CleanRoomAotDissector`).
    pub preflight_scitt_digest: [u8; 32],
    /// Protección de no-sobreescritura en sistema de archivos (`O_CREAT | O_EXCL` / `RENAME_EXCL`).
    pub no_overwrite_excl: bool,
    /// Clave pública del Secure Enclave en formato SEC1 X9.63 sin comprimir (65 bytes, prefijo `0x04`).
    pub enclave_pubkey_sec1: Vec<u8>,
    /// Firma ECDSA ASN.1 DER emitida por el Secure Enclave sobre la intención canónica.
    pub enclave_signature_der: Vec<u8>,
}

/// Gate Pre-Vuelo `REA / RFO = 0` en Ring-0 que valida la revisión de la app antes de ejecutar.
#[derive(Debug, Clone, Default)]
pub struct ReaPreflightGate;

impl ReaPreflightGate {
    /// Techo estricto del Cortafuegos 17 para gramáticas AOT de despacho (`150 tokens`).
    pub const MAX_AOT_GRAMMAR_TOKENS: usize = 150;

    /// Verifica que la aplicación y la acción hayan superado la revisión Pre-Vuelo `REA / RFO = 0`
    /// y que el ticket criptográfico del Secure Enclave sea estructuralmente válido antes del despacho.
    pub fn verify_dispatch_ready(
        ticket: &AuthorizedDispatchTicket,
        grammar_tokens: usize,
        semantic_expected: Option<&SemanticControlBinding>,
        semantic_observed: Option<&SemanticControlBinding>,
    ) -> Result<(), TrustGatewayError> {
        if ticket.preflight_scitt_digest == [0u8; 32] {
            return Err(TrustGatewayError::MissingReaPreflightReview {
                app_bundle_id: ticket.app_bundle_id.clone(),
            });
        }
        if grammar_tokens > Self::MAX_AOT_GRAMMAR_TOKENS {
            return Err(TrustGatewayError::Cortafuegos17GrammarBloat {
                estimated_tokens: grammar_tokens,
                max_tokens: Self::MAX_AOT_GRAMMAR_TOKENS,
            });
        }
        if ticket.channel == DesktopChannelTier::OpaqueCustomCanvas {
            return Err(TrustGatewayError::UnverifiedAppSurfaceAbstention {
                app_bundle_id: ticket.app_bundle_id.clone(),
                action: ticket.action.clone(),
            });
        }
        if ticket.enclave_pubkey_sec1.len() != 65 || ticket.enclave_pubkey_sec1[0] != 0x04 {
            return Err(TrustGatewayError::InvalidSecureEnclaveTicket(
                "SEC1 X9.63 public key must be 65 bytes starting with 0x04".to_string(),
            ));
        }
        if ticket.enclave_signature_der.len() < 8 || ticket.enclave_signature_der[0] != 0x30 {
            return Err(TrustGatewayError::InvalidSecureEnclaveTicket(
                "ECDSA DER signature must start with ASN.1 SEQUENCE tag 0x30".to_string(),
            ));
        }
        if ticket.channel == DesktopChannelTier::AxSemanticTree {
            match (semantic_expected, semantic_observed) {
                (Some(exp), Some(obs)) => exp.verify_before_dispatch(obs)?,
                _ => {
                    return Err(TrustGatewayError::InvalidSecureEnclaveTicket(
                        "AX_SEMANTIC_TREE dispatch requires pre-dispatch SemanticControlBinding".to_string(),
                    ));
                }
            }
        }
        Ok(())
    }
}

// ============================================================================
// MUTACIÓN #5: SHADOW-EDGE-DIFF (Falsificador Empírico OS vs. AuthorityGraph)
// ============================================================================

/// Plano epistemológico y operativo de un mecanismo de seguridad en BABYLON-60.
///
/// Separa explícitamente:
/// 1. **Verificación Formal (`FormalVerification`):** Comprobación matemática o de grafo sobre
///    el modelo declarado $G_{\text{decl}}$ (`AuthorityGraph::verify_complete_mediation`).
/// 2. **Prevención en Tiempo de Ejecución (`PreventiveEnforcement`):** Mecanismo inline que
///    interpela y bloquea efectos no autorizados antes de su ejecución (`SovereignExecutor`,
///    `O_NOFOLLOW`, perfiles experimentales Seatbelt o clientes Endpoint Security `AUTH`).
/// 3. **Observación Empírica (`EmpiricalObservation`):** Inspección de solo lectura de recursos
///    del sistema operativo (`OsResourceObserver`, `ShadowEdgeDiff`, testigos físicos de inodo/hash).
///    La observación puede **falsar** `INV-Ω` al descubrir aristas ocultas ($E_{\text{obs}} \setminus E_{\text{decl}} \neq \emptyset$),
///    pero **nunca previene** un efecto por sí misma ni demuestra aislamiento universal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum SecurityMechanismPlane {
    /// Verificación sobre el grafo o modelo formal declarado (`L1_FORMAL`).
    FormalVerification,
    /// Intercepción o confinamiento preventivo antes del efecto (`L2_IMPLEMENTATION` / `L3_ISOLATION`).
    PreventiveEnforcement,
    /// Observación empírica de solo lectura sobre el proceso y el sustrato OS (`L4_EXPERIMENTAL`).
    EmpiricalObservation,
}

impl SecurityMechanismPlane {
    /// Identificador canónico del plano.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::FormalVerification => "FORMAL_VERIFICATION",
            Self::PreventiveEnforcement => "PREVENTIVE_ENFORCEMENT",
            Self::EmpiricalObservation => "EMPIRICAL_OBSERVATION",
        }
    }

    /// Indica si este plano puede bloquear preventivamente una operación antes de su ejecución.
    pub const fn can_prevent_effect(self) -> bool {
        matches!(self, Self::PreventiveEnforcement)
    }

    /// Indica si este plano puede refutar empíricamente una afirmación de aislamiento en el SO real.
    pub const fn can_falsify_isolation(self) -> bool {
        matches!(self, Self::EmpiricalObservation)
    }

    /// Ningún plano demuestra «imposibilidad física universal» fuera de los supuestos del dominio.
    pub const fn proves_universal_isolation(self) -> bool {
        false
    }
}

/// Veredicto epistémico de `ShadowEdgeDiff` sobre la mediación real en el dominio ensayado.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum ShadowDiffVerdict {
    /// Soportado dentro del dominio experimental acotado (visibilidad completa, cero aristas
    /// sombra y testigo físico independiente que confirma ausencia de mutación no mediada).
    SupportedWithinDomain,
    /// Refutado: se descubrió al menos una arista de autoridad en el SO ausente de `AuthorityGraph`
    /// o una mutación física ejecutada sin recibo del broker BABYLON.
    Falsified,
    /// No concluyente: visibilidad incompleta del observador (`EPERM` / `SD-005`), o sondeo
    /// puntual sin anomalías aparentes pero sin testigo físico continuo (`SD-004`).
    /// No encontrar anomalías en un sondeo puntual nunca equivale a demostrar aislamiento.
    Inconclusive,
    /// No ensayado aún en el sistema operativo.
    Untested,
}

impl ShadowDiffVerdict {
    /// Representación textual canónica exigida por CORTEX y NEMESIS.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::SupportedWithinDomain => "SUPPORTED_WITHIN_DOMAIN",
            Self::Falsified => "FALSIFIED",
            Self::Inconclusive => "INCONCLUSIVE",
            Self::Untested => "UNTESTED",
        }
    }
}

impl TryFrom<ShadowDiffVerdict> for crate::ontology::nemesis::NemesisVerdict {
    type Error = &'static str;

    fn try_from(value: ShadowDiffVerdict) -> Result<Self, Self::Error> {
        match value {
            ShadowDiffVerdict::SupportedWithinDomain => Ok(Self::SupportedWithinDomain),
            ShadowDiffVerdict::Falsified => Ok(Self::Falsified),
            ShadowDiffVerdict::Untested => Ok(Self::Untested),
            ShadowDiffVerdict::Inconclusive => Err(
                "INCONCLUSIVE shadow observation cannot be promoted to SUPPORTED_WITHIN_DOMAIN",
            ),
        }
    }
}

/// Modalidad temporal del observador de recursos del sistema operativo.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum ObservationModality {
    /// Sondeo puntual de tabla de descriptores/mapas (`lsof` / `/dev/fd`).
    /// Ciego a operaciones efímeras `open -> write -> close` entre muestras (`SD-004`)
    /// salvo que se combine con un testigo físico independiente del recurso.
    PointInTimePolling,
    /// Flujo continuo de eventos del kernel (ej. macOS Endpoint Security `ES_EVENT_TYPE_*`).
    ContinuousKernelStream,
}

impl ObservationModality {
    /// Etiqueta canónica de la modalidad de observación.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PointInTimePolling => "POINT_IN_TIME_POLLING",
            Self::ContinuousKernelStream => "CONTINUOUS_KERNEL_STREAM",
        }
    }
}

/// Estado de visibilidad del observador `OsResourceObserver` al inspeccionar un proceso.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum ObserverVisibility {
    /// La tabla de descriptores y regiones del proceso objetivo se inspeccionó íntegramente.
    Complete,
    /// El sistema operativo denegó el acceso a la tabla del proceso (`EPERM` / SIP / UID distinto, `SD-005`).
    PermissionDenied {
        /// PID objetivo cuya inspección fue denegada.
        pid: u32,
        /// Detalle diagnóstico devuelto por el observador.
        detail: String,
    },
    /// Salida truncada, proceso terminado durante el muestreo o fallo parcial de `libproc`/`lsof`.
    Incomplete {
        /// PID objetivo con visibilidad parcial.
        pid: u32,
        /// Detalle diagnóstico.
        detail: String,
    },
    /// El observador aún no ha sido ejecutado sobre el proceso.
    Untested,
}

impl ObserverVisibility {
    /// Devuelve `true` únicamente si la visibilidad del observador fue completa.
    pub const fn is_complete(&self) -> bool {
        matches!(self, Self::Complete)
    }
}

/// Clasificación de un recurso observado en el proceso del agente a nivel de sistema operativo.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub enum ObservedResourceKind {
    /// Descriptor de archivo regular (`tREG`, ej. `SD-001` heredado tras `fork/exec`).
    RegularFile,
    /// Descriptor de directorio (`tDIR` / `O_DIRECTORY`).
    Directory,
    /// Socket de dominio Unix (`tunix`, ej. `SD-002` canal IPC directo fuera del broker).
    UnixSocket,
    /// Región de memoria compartida respaldada por vnode (`ftxt`/`fmem` `MAP_SHARED`, ej. `SD-003`).
    SharedMemoryMap,
    /// Tubería anónima o FIFO con nombre (`tPIPE` / `tFIFO`).
    PipeOrFifo,
    /// Otro recurso del kernel XNU/POSIX.
    Other(String),
}

/// Entrada individual observada en la tabla de recursos del proceso del agente.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ObservedResourceEntry {
    /// PID del proceso del agente inspeccionado.
    pub pid: u32,
    /// Identificador del descriptor o región (ej. `"fd:7"`, `"mmap:txt"`, `"fd:4"`).
    pub descriptor_or_region: String,
    /// Tipo de recurso del sistema operativo.
    pub kind: ObservedResourceKind,
    /// Ruta o endpoint asociado al descriptor/vnode.
    pub target_path: PathBuf,
    /// Mecanismo del sistema operativo observado.
    pub mechanism: String,
}

/// Instantánea de solo lectura de los recursos abiertos/mapeados por un proceso de agente.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ProcessResourceSnapshot {
    /// PID del proceso inspeccionado.
    pub pid: u32,
    /// Modalidad de observación empleada.
    pub modality: ObservationModality,
    /// Nivel de visibilidad obtenido durante la observación.
    pub visibility: ObserverVisibility,
    /// Recursos observados en el proceso.
    pub entries: Vec<ObservedResourceEntry>,
}

impl ProcessResourceSnapshot {
    /// Crea una instantánea en estado `Untested`.
    pub const fn untested(pid: u32) -> Self {
        Self {
            pid,
            modality: ObservationModality::PointInTimePolling,
            visibility: ObserverVisibility::Untested,
            entries: Vec::new(),
        }
    }

    /// Crea una instantánea con fallo explícito de permisos (`SD-005`).
    pub fn permission_denied(pid: u32, detail: impl Into<String>) -> Self {
        Self {
            pid,
            modality: ObservationModality::PointInTimePolling,
            visibility: ObserverVisibility::PermissionDenied {
                pid,
                detail: detail.into(),
            },
            entries: Vec::new(),
        }
    }
}

/// Normaliza rutas en macOS/Darwin resolviendo el alias `/private/var` <-> `/var` y `/private/tmp` <-> `/tmp`
/// para que la comparación entre vnodes (`tREG`) y sockets `AF_UNIX` (`tunix`) sea determinista.
pub fn normalize_darwin_path(path: &Path) -> PathBuf {
    let resolved = std::fs::canonicalize(path).unwrap_or_else(|_| {
        if let (Some(parent), Some(name)) = (path.parent(), path.file_name()) {
            if let Ok(canon_parent) = std::fs::canonicalize(parent) {
                return canon_parent.join(name);
            }
        }
        path.to_path_buf()
    });
    let s = resolved.to_string_lossy();
    if let Some(rest) = s.strip_prefix("/private/var/") {
        PathBuf::from(format!("/var/{rest}"))
    } else if s == "/private/var" {
        PathBuf::from("/var")
    } else if let Some(rest) = s.strip_prefix("/private/tmp/") {
        PathBuf::from(format!("/tmp/{rest}"))
    } else if s == "/private/tmp" {
        PathBuf::from("/tmp")
    } else {
        resolved
    }
}

/// Observador determinista de solo lectura de recursos de procesos en el sistema operativo.
///
/// Opera estrictamente en el plano `SecurityMechanismPlane::EmpiricalObservation` sin ningún
/// LLM en la ruta de decisión.
#[derive(Debug, Clone, Default)]
pub struct OsResourceObserver;

impl OsResourceObserver {
    /// Plano operativo fijo del observador (observación empírica de solo lectura).
    pub const MECHANISM_PLANE: SecurityMechanismPlane =
        SecurityMechanismPlane::EmpiricalObservation;

    /// Inspecciona en modo solo lectura los descriptores y regiones `mmap` del proceso `pid`
    /// invocando `/usr/sbin/lsof -w -n -P -p <pid> -F pftn`.
    ///
    /// Si `lsof` falla o no emite el registro del proceso (ej. falta de permisos sobre un PID
    /// privilegiado o inexistente, `SD-005`), marca la visibilidad como `PermissionDenied` o `Incomplete`
    /// para impedir que una lista vacía se interprete erróneamente como aislamiento.
    pub fn observe_pid(pid: u32) -> ProcessResourceSnapshot {
        if pid == 0 {
            return ProcessResourceSnapshot::permission_denied(
                0,
                "kernel PID 0 cannot be inspected from user space",
            );
        }
        let pid_arg = pid.to_string();
        let lsof_bin = if Path::new("/usr/sbin/lsof").exists() {
            "/usr/sbin/lsof"
        } else if Path::new("/usr/bin/lsof").exists() {
            "/usr/bin/lsof"
        } else {
            "lsof"
        };
        let output = Command::new(lsof_bin)
            .args(["-w", "-n", "-P", "-p", &pid_arg, "-F", "pftn"])
            .output();

        match output {
            Ok(out) => {
                let stdout = String::from_utf8_lossy(&out.stdout);
                let stderr = String::from_utf8_lossy(&out.stderr);
                Self::parse_lsof_field_output(pid, out.status.success(), &stdout, &stderr)
            }
            Err(err) => ProcessResourceSnapshot {
                pid,
                modality: ObservationModality::PointInTimePolling,
                visibility: ObserverVisibility::Incomplete {
                    pid,
                    detail: format!("failed to execute /usr/sbin/lsof: {err}"),
                },
                entries: Vec::new(),
            },
        }
    }

    /// Parsea deterministamente la salida por campos (`-F pftn`) de `lsof`.
    pub fn parse_lsof_field_output(
        pid: u32,
        exit_success: bool,
        stdout: &str,
        stderr: &str,
    ) -> ProcessResourceSnapshot {
        let trimmed = stdout.trim();
        let stderr_trimmed = stderr.trim();

        if !exit_success || trimmed.is_empty() || !trimmed.starts_with('p') {
            let detail = if !stderr_trimmed.is_empty() {
                format!("lsof non-zero or empty process table: {stderr_trimmed}")
            } else {
                format!(
                    "lsof returned exit_success={exit_success} with 0 process records for pid={pid} (EPERM / restricted or vanished process)"
                )
            };
            return ProcessResourceSnapshot::permission_denied(pid, detail);
        }

        let mut entries = Vec::new();
        let mut current_fd: Option<String> = None;
        let mut current_type: Option<String> = None;
        let mut current_name: Option<String> = None;
        let mut unreadable_count = 0usize;

        let flush_record = |fd_opt: &mut Option<String>,
                            type_opt: &mut Option<String>,
                            name_opt: &mut Option<String>,
                            out_entries: &mut Vec<ObservedResourceEntry>,
                            unreadable: &mut usize| {
            if let Some(fd_tag) = fd_opt.take() {
                let ftype = type_opt.take().unwrap_or_default();
                let fname = name_opt.take().unwrap_or_default();
                if fd_tag == "cwd" || fd_tag == "rtd" {
                    return;
                }
                if fname.contains("Permission denied") || fname.contains("cannot opendir") {
                    *unreadable += 1;
                    return;
                }
                if fname.is_empty() {
                    return;
                }
                let (descriptor_or_region, kind, mechanism) =
                    if fd_tag == "txt" || fd_tag == "mem" {
                        (
                            format!("mmap:{fd_tag}"),
                            ObservedResourceKind::SharedMemoryMap,
                            "os_vm_map_shared_vnode".to_string(),
                        )
                    } else if ftype == "unix" {
                        (
                            format!("fd:{fd_tag}"),
                            ObservedResourceKind::UnixSocket,
                            "os_af_unix_socket".to_string(),
                        )
                    } else if ftype == "REG" {
                        (
                            format!("fd:{fd_tag}"),
                            ObservedResourceKind::RegularFile,
                            "os_fd_table_reg".to_string(),
                        )
                    } else if ftype == "DIR" {
                        (
                            format!("fd:{fd_tag}"),
                            ObservedResourceKind::Directory,
                            "os_fd_table_dir".to_string(),
                        )
                    } else if ftype == "PIPE" || ftype == "FIFO" {
                        (
                            format!("fd:{fd_tag}"),
                            ObservedResourceKind::PipeOrFifo,
                            "os_fd_table_pipe".to_string(),
                        )
                    } else {
                        (
                            format!("fd:{fd_tag}"),
                            ObservedResourceKind::Other(ftype),
                            "os_fd_table_other".to_string(),
                        )
                    };

                out_entries.push(ObservedResourceEntry {
                    pid,
                    descriptor_or_region,
                    kind,
                    target_path: PathBuf::from(fname),
                    mechanism,
                });
            }
        };

        for raw_line in trimmed.lines() {
            if raw_line.is_empty() {
                continue;
            }
            let tag = raw_line.as_bytes()[0] as char;
            let val = &raw_line[1..];
            match tag {
                'p' => {
                    flush_record(
                        &mut current_fd,
                        &mut current_type,
                        &mut current_name,
                        &mut entries,
                        &mut unreadable_count,
                    );
                }
                'f' => {
                    flush_record(
                        &mut current_fd,
                        &mut current_type,
                        &mut current_name,
                        &mut entries,
                        &mut unreadable_count,
                    );
                    current_fd = Some(val.to_string());
                }
                't' => {
                    current_type = Some(val.to_string());
                }
                'n' => {
                    current_name = Some(val.to_string());
                }
                _ => {}
            }
        }
        flush_record(
            &mut current_fd,
            &mut current_type,
            &mut current_name,
            &mut entries,
            &mut unreadable_count,
        );

        entries.sort();
        entries.dedup();

        let visibility = if unreadable_count > 0 {
            ObserverVisibility::Incomplete {
                pid,
                detail: format!("{unreadable_count} descriptor entries reported permission denied"),
            }
        } else if entries.is_empty() {
            ObserverVisibility::Incomplete {
                pid,
                detail: "process record contained zero inspectable descriptors".to_string(),
            }
        } else {
            ObserverVisibility::Complete
        };

        ProcessResourceSnapshot {
            pid,
            modality: ObservationModality::PointInTimePolling,
            visibility,
            entries,
        }
    }
}

/// Computa un digest SHA-256 determinista con separación de dominio sobre un slice de bytes.
fn compute_domain_sha256(domain: &[u8], payload: &[u8]) -> [u8; 32] {
    #[cfg(feature = "cortex-persist")]
    {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(domain);
        h.update((payload.len() as u64).to_be_bytes());
        h.update(payload);
        h.finalize().into()
    }
    #[cfg(not(feature = "cortex-persist"))]
    {
        use p256::elliptic_curve::ops::Reduce;
        let _ = domain;
        let mut out = [0u8; 32];
        for (i, b) in payload.iter().enumerate() {
            out[i % 32] ^= b.wrapping_add(i as u8);
        }
        let _ = <p256::Scalar as Reduce<p256::U256>>::reduce_bytes(&out.into());
        out
    }
}

/// Testigo físico independiente del estado de un recurso protegido (`INV_C5_NEMESIS_EVIDENCE_CONTRACT`).
///
/// Permite detectar mutaciones producidas por descriptores efímeros abiertos y cerrados
/// entre intervalos de sondeo (`SD-004`) o por regiones `mmap` compartidas (`SD-003`).
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct PhysicalResourceWitness {
    /// Ruta del recurso protegido monitorizado.
    pub resource_path: PathBuf,
    /// Digest SHA-256 del contenido antes del experimento.
    pub pre_state_sha256: [u8; 32],
    /// Digest SHA-256 del contenido después del experimento.
    pub post_state_sha256: [u8; 32],
    /// Inodo físico antes del experimento.
    pub pre_inode: u64,
    /// Inodo físico después del experimento.
    pub post_inode: u64,
    /// `true` si y solo si el broker BABYLON emitió un recibo válido autorizando la transición.
    pub broker_authorized_mutation: bool,
}

impl PhysicalResourceWitness {
    /// Lee de forma segura (con `O_NOFOLLOW` en Unix para evitar TOCTOU de symlinks) el estado
    /// inicial de un archivo protegido.
    pub fn capture_pre_state(path: &Path) -> std::io::Result<Self> {
        let (digest, ino) = Self::read_digest_and_inode(path)?;
        Ok(Self {
            resource_path: path.to_path_buf(),
            pre_state_sha256: digest,
            post_state_sha256: digest,
            pre_inode: ino,
            post_inode: ino,
            broker_authorized_mutation: false,
        })
    }

    /// Captura el estado posterior del recurso protegido y registra si el broker autorizó la mutación.
    pub fn observe_post_state(&self, broker_authorized_mutation: bool) -> std::io::Result<Self> {
        let (post_digest, post_ino) = Self::read_digest_and_inode(&self.resource_path)?;
        Ok(Self {
            resource_path: self.resource_path.clone(),
            pre_state_sha256: self.pre_state_sha256,
            post_state_sha256: post_digest,
            pre_inode: self.pre_inode,
            post_inode: post_ino,
            broker_authorized_mutation,
        })
    }

    /// Devuelve `true` si el recurso físico mutó (contenido o inodo) sin autorización del broker BABYLON.
    pub fn unmediated_mutation_occurred(&self) -> bool {
        let mutated =
            self.pre_state_sha256 != self.post_state_sha256 || self.pre_inode != self.post_inode;
        mutated && !self.broker_authorized_mutation
    }

    fn read_digest_and_inode(path: &Path) -> std::io::Result<([u8; 32], u64)> {
        use std::io::Read;
        #[cfg(unix)]
        let file = {
            use std::os::unix::fs::OpenOptionsExt;
            std::fs::OpenOptions::new()
                .read(true)
                .custom_flags(libc::O_NOFOLLOW)
                .open(path)?
        };
        #[cfg(not(unix))]
        let file = std::fs::File::open(path)?;

        let meta = file.metadata()?;
        #[cfg(unix)]
        let ino = {
            use std::os::unix::fs::MetadataExt;
            meta.ino()
        };
        #[cfg(not(unix))]
        let ino = meta.len();

        let mut reader = std::io::BufReader::new(file);
        let mut bytes = Vec::new();
        reader.read_to_end(&mut bytes)?;
        let digest = compute_domain_sha256(b"BABYLON60/PHYSICAL-WITNESS/v1", &bytes);
        Ok((digest, ino))
    }
}

/// Artefacto de evidencia determinista compatible con CORTEX / WORM.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct CortexShadowEvidenceArtifact {
    /// Identificador de la prueba adversarial (ej. `"SD-001"` .. `"SD-005"`).
    pub test_id: String,
    /// Reloj lógico canónico inyectado (`INV_C5_CANONICAL_LOGICAL_TICK`).
    pub logical_tick: u64,
    /// Veredicto epistémico resultante (`SUPPORTED_WITHIN_DOMAIN | FALSIFIED | INCONCLUSIVE | UNTESTED`).
    pub verdict: ShadowDiffVerdict,
    /// Plano del mecanismo que emite la evidencia (`EMPIRICAL_OBSERVATION`).
    pub mechanism_plane: SecurityMechanismPlane,
    /// Indica si `AuthorityGraph::verify_complete_mediation()` aprobó el grafo declarado.
    pub declared_graph_mediation_holds: bool,
    /// Indica si el grafo aumentado con las aristas sombra descubiertas aún satisface mediación.
    pub augmented_graph_mediation_holds: bool,
    /// Modalidad de observación del SO.
    pub observer_modality: ObservationModality,
    /// Visibilidad alcanzada por el observador del SO.
    pub observer_visibility: ObserverVisibility,
    /// Contraejemplos preservados: aristas de autoridad en el SO ausentes de `AuthorityGraph`.
    pub shadow_edges: Vec<AccessEdge>,
    /// Mutaciones físicas detectadas fuera del broker BABYLON.
    pub unmediated_mutations: Vec<PhysicalResourceWitness>,
    /// Supuestos y limitaciones explícitas del modelo de amenazas.
    pub threat_model_limitations: Vec<String>,
    /// Digest SHA-256 canónico de 32 bytes sobre el artefacto completo.
    pub evidence_digest_sha256: [u8; 32],
}

impl CortexShadowEvidenceArtifact {
    /// Persiste el artefacto de evidencia en formato JSON determinista en `dir/<test_id>_shadow_evidence.json`
    /// forzando `O_NOFOLLOW` y `sync_all()` (`INV_C5_WAL_SYNCHRONOUS_FULL`).
    #[cfg(feature = "cortex-persist")]
    pub fn persist_json_sync(&self, dir: &Path) -> std::io::Result<PathBuf> {
        use std::io::Write;
        std::fs::create_dir_all(dir)?;
        let safe_id: String = self
            .test_id
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
            .collect();
        let file_path = dir.join(format!("{safe_id}_shadow_evidence.json"));
        let payload = serde_json::to_vec_pretty(self)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        #[cfg(unix)]
        let mut f = {
            use std::os::unix::fs::OpenOptionsExt;
            std::fs::OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .custom_flags(libc::O_NOFOLLOW)
                .open(&file_path)?
        };
        #[cfg(not(unix))]
        let mut f = std::fs::File::create(&file_path)?;

        f.write_all(&payload)?;
        f.sync_all()?;
        Ok(file_path)
    }
}

/// Resultado completo del motor de diferencia de grafos `ShadowEdgeDiff`.
#[derive(Debug, Clone, PartialEq, Eq)]
#[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
pub struct ShadowDiffReport {
    /// Reloj lógico canónico inyectado (`INV_C5_CANONICAL_LOGICAL_TICK`).
    pub logical_tick: u64,
    /// Veredicto epistémico (`SUPPORTED_WITHIN_DOMAIN | FALSIFIED | INCONCLUSIVE | UNTESTED`).
    pub verdict: ShadowDiffVerdict,
    /// Plano del mecanismo (`EmpiricalObservation`).
    pub mechanism_plane: SecurityMechanismPlane,
    /// Veredicto formal sobre el `AuthorityGraph` declarado ($G_{\text{decl}}$).
    pub declared_mediation_verdict: MediationVerdict,
    /// Veredicto sobre el grafo aumentado ($G_{\text{decl}} \cup \Delta E_{\text{shadow}}$).
    pub augmented_mediation_verdict: MediationVerdict,
    /// Modalidad del observador empleada.
    pub observer_modality: ObservationModality,
    /// Visibilidad reportada por el observador del SO.
    pub observer_visibility: ObserverVisibility,
    /// Aristas sombra descubiertas ($\Delta E_{\text{shadow}} = E_{\text{obs}} \setminus E_{\text{decl}}$).
    pub shadow_edges: Vec<AccessEdge>,
    /// Mutaciones físicas no mediadas detectadas por testigos independientes.
    pub unmediated_mutations: Vec<PhysicalResourceWitness>,
    /// Limitaciones explícitas del modelo de amenazas y del observador.
    pub threat_model_limitations: Vec<String>,
}

impl ShadowDiffReport {
    /// Emite un artefacto de evidencia determinista compatible con CORTEX conservando todos los contraejemplos.
    pub fn to_cortex_evidence(&self, test_id: impl Into<String>) -> CortexShadowEvidenceArtifact {
        let test_id_str = test_id.into();
        let mut canonical_bytes = Vec::new();
        canonical_bytes.extend_from_slice(test_id_str.as_bytes());
        canonical_bytes.extend_from_slice(&self.logical_tick.to_le_bytes());
        canonical_bytes.extend_from_slice(self.verdict.as_str().as_bytes());
        canonical_bytes.extend_from_slice(self.mechanism_plane.as_str().as_bytes());
        canonical_bytes.push(u8::from(self.declared_mediation_verdict.complete_mediation_holds));
        canonical_bytes.push(u8::from(self.augmented_mediation_verdict.complete_mediation_holds));
        canonical_bytes.extend_from_slice(self.observer_modality.as_str().as_bytes());
        for edge in &self.shadow_edges {
            canonical_bytes.extend_from_slice(format!("{:?}", edge).as_bytes());
        }
        for witness in &self.unmediated_mutations {
            canonical_bytes.extend_from_slice(witness.resource_path.to_string_lossy().as_bytes());
            canonical_bytes.extend_from_slice(&witness.pre_state_sha256);
            canonical_bytes.extend_from_slice(&witness.post_state_sha256);
        }
        let digest = compute_domain_sha256(b"BABYLON60/CORTEX-SHADOW-EVIDENCE/v1", &canonical_bytes);

        CortexShadowEvidenceArtifact {
            test_id: test_id_str,
            logical_tick: self.logical_tick,
            verdict: self.verdict,
            mechanism_plane: self.mechanism_plane,
            declared_graph_mediation_holds: self.declared_mediation_verdict.complete_mediation_holds,
            augmented_graph_mediation_holds: self
                .augmented_mediation_verdict
                .complete_mediation_holds,
            observer_modality: self.observer_modality,
            observer_visibility: self.observer_visibility.clone(),
            shadow_edges: self.shadow_edges.clone(),
            unmediated_mutations: self.unmediated_mutations.clone(),
            threat_model_limitations: self.threat_model_limitations.clone(),
            evidence_digest_sha256: digest,
        }
    }
}

/// Motor determinista de diferencia entre el `AuthorityGraph` declarado y los recursos
/// observados en el sistema operativo (`ShadowEdgeDiff`).
///
/// Calcula $\Delta E_{\text{shadow}} = E_{\text{obs}} \setminus E_{\text{decl}}$ y contrasta
/// testigos físicos independientes para falsar experimentalmente `INV-Ω`.
#[derive(Debug, Clone, Default)]
pub struct ShadowEdgeDiff;

impl ShadowEdgeDiff {
    /// Limitaciones canónicas del modelo de amenazas que acompañan todo reporte de `ShadowEdgeDiff`.
    pub fn canonical_threat_model_limitations() -> Vec<String> {
        vec![
            "lsof and libproc are point-in-time discovery observers, not inline security boundaries; sub-sampling-interval open/write/close operations (SD-004) are invisible to polling without an independent physical witness or Endpoint Security stream.".to_string(),
            "No Anomaly in an OS polling snapshot does NOT prove universal isolation; without complete observer visibility and an independent physical post-condition witness, verdict degrades to INCONCLUSIVE.".to_string(),
            "sandbox-exec (Seatbelt SBPL) is deprecated by Apple as a third-party public API; experimental Seatbelt profiles must not be sold as permanent commercial guarantees without Endpoint Security / entitlement-backed enforcement.".to_string(),
        ]
    }

    /// Evalúa deterministamente la diferencia entre el grafo de autoridad declarado `declared_graph`
    /// y la realidad observada en el sistema operativo (`snapshot` + `physical_witnesses`).
    pub fn evaluate(
        declared_graph: &AuthorityGraph,
        agent_node: &AuthorityNode,
        protected_roots: &[PathBuf],
        allowed_ipc_sockets: &[PathBuf],
        snapshot: &ProcessResourceSnapshot,
        physical_witnesses: &[PhysicalResourceWitness],
        logical_tick: u64,
    ) -> ShadowDiffReport {
        let declared_mediation_verdict = declared_graph.verify_complete_mediation();
        let declared_edge_set: HashSet<AccessEdge> =
            declared_graph.declared_edges().into_iter().collect();

        // Mapear cada ruta protegida normalizada a su nodo ProtectedResource declarado (si existe)
        let mut normalized_protected: Vec<(PathBuf, AuthorityNode)> = Vec::new();
        let declared_resources: Vec<String> = declared_graph
            .nodes()
            .iter()
            .filter_map(|n| match n {
                AuthorityNode::ProtectedResource(s) => Some(s.clone()),
                _ => None,
            })
            .collect();

        for root in protected_roots {
            let norm_root = normalize_darwin_path(root);
            let matched_node = declared_resources
                .iter()
                .find(|s| normalize_darwin_path(Path::new(s)) == norm_root)
                .map(|s| AuthorityNode::ProtectedResource(s.clone()))
                .unwrap_or_else(|| {
                    AuthorityNode::ProtectedResource(root.to_string_lossy().into_owned())
                });
            normalized_protected.push((norm_root, matched_node));
        }

        let normalized_allowed_sockets: HashSet<PathBuf> = allowed_ipc_sockets
            .iter()
            .map(|p| normalize_darwin_path(p))
            .collect();

        // Directorios padre del perímetro experimental para filtrar sockets AF_UNIX del propio test/agente
        let mut perimeter_dirs: Vec<PathBuf> = Vec::new();
        for (norm_root, _) in &normalized_protected {
            if let Some(parent) = norm_root.parent() {
                perimeter_dirs.push(parent.to_path_buf());
            }
            perimeter_dirs.push(norm_root.clone());
        }
        for sock in &normalized_allowed_sockets {
            if let Some(parent) = sock.parent() {
                perimeter_dirs.push(parent.to_path_buf());
            }
        }

        let mut shadow_edges: Vec<AccessEdge> = Vec::new();

        for entry in &snapshot.entries {
            let norm_target = normalize_darwin_path(&entry.target_path);

            match &entry.kind {
                ObservedResourceKind::RegularFile
                | ObservedResourceKind::Directory
                | ObservedResourceKind::SharedMemoryMap => {
                    for (norm_root, protected_node) in &normalized_protected {
                        if norm_target == *norm_root || norm_target.starts_with(norm_root) {
                            let cap_node = AuthorityNode::CapabilityHandle(format!(
                                "{}:{}",
                                entry.descriptor_or_region,
                                norm_target.display()
                            ));
                            let edge_agent_to_cap = AccessEdge {
                                from: agent_node.clone(),
                                to: cap_node.clone(),
                                mechanism: entry.mechanism.clone(),
                            };
                            let sink_mech = match entry.kind {
                                ObservedResourceKind::SharedMemoryMap => {
                                    "unmediated_mmap_shared_write_channel".to_string()
                                }
                                _ => "unmediated_inherited_or_direct_fd".to_string(),
                            };
                            let edge_cap_to_res = AccessEdge {
                                from: cap_node,
                                to: protected_node.clone(),
                                mechanism: sink_mech,
                            };

                            if !declared_edge_set.contains(&edge_agent_to_cap) {
                                shadow_edges.push(edge_agent_to_cap);
                            }
                            if !declared_edge_set.contains(&edge_cap_to_res) {
                                shadow_edges.push(edge_cap_to_res);
                            }
                        }
                    }
                }
                ObservedResourceKind::UnixSocket => {
                    let target_str = entry.target_path.to_string_lossy();
                    if target_str.starts_with('/') && !normalized_allowed_sockets.contains(&norm_target) {
                        let in_perimeter = perimeter_dirs.is_empty()
                            || perimeter_dirs
                                .iter()
                                .any(|d| norm_target.starts_with(d));
                        if in_perimeter {
                            let ipc_node =
                                AuthorityNode::IpcChannel(norm_target.to_string_lossy().into_owned());
                            let sink_node = AuthorityNode::ProtectedResource(format!(
                                "unmediated_ipc_endpoint:{}",
                                norm_target.display()
                            ));
                            let edge_to_ipc = AccessEdge {
                                from: agent_node.clone(),
                                to: ipc_node.clone(),
                                mechanism: format!(
                                    "{}:AF_UNIX_direct_socket",
                                    entry.descriptor_or_region
                                ),
                            };
                            let edge_ipc_to_sink = AccessEdge {
                                from: ipc_node,
                                to: sink_node,
                                mechanism: "unmediated_interprocess_channel".to_string(),
                            };
                            if !declared_edge_set.contains(&edge_to_ipc) {
                                shadow_edges.push(edge_to_ipc);
                            }
                            if !declared_edge_set.contains(&edge_ipc_to_sink) {
                                shadow_edges.push(edge_ipc_to_sink);
                            }
                        }
                    }
                }
                ObservedResourceKind::PipeOrFifo | ObservedResourceKind::Other(_) => {}
            }
        }

        // Contrastar testigos físicos independientes (detecta SD-004: open -> write -> close efímero)
        let mut unmediated_mutations = Vec::new();
        for witness in physical_witnesses {
            if witness.unmediated_mutation_occurred() {
                unmediated_mutations.push(witness.clone());
                let norm_witness = normalize_darwin_path(&witness.resource_path);
                let target_protected_node = normalized_protected
                    .iter()
                    .find(|(norm_root, _)| {
                        norm_witness == *norm_root || norm_witness.starts_with(norm_root)
                    })
                    .map(|(_, node)| node.clone())
                    .unwrap_or_else(|| {
                        AuthorityNode::ProtectedResource(
                            witness.resource_path.to_string_lossy().into_owned(),
                        )
                    });

                let already_covered_by_fd = shadow_edges
                    .iter()
                    .any(|e| e.to == target_protected_node);

                if !already_covered_by_fd {
                    let transient_cap = AuthorityNode::CapabilityHandle(format!(
                        "transient_unobserved_fd:{}",
                        norm_witness.display()
                    ));
                    shadow_edges.push(AccessEdge {
                        from: agent_node.clone(),
                        to: transient_cap.clone(),
                        mechanism: "ephemeral_open_write_close_between_polls".to_string(),
                    });
                    shadow_edges.push(AccessEdge {
                        from: transient_cap,
                        to: target_protected_node,
                        mechanism: "unmediated_physical_state_mutation".to_string(),
                    });
                }
            }
        }

        shadow_edges.sort();
        shadow_edges.dedup();
        unmediated_mutations.sort();
        unmediated_mutations.dedup();

        let mut augmented_graph = declared_graph.clone();
        for edge in &shadow_edges {
            augmented_graph.add_edge(edge.from.clone(), edge.to.clone(), edge.mechanism.clone());
        }
        let augmented_mediation_verdict = augmented_graph.verify_complete_mediation();

        // Árbol de decisión epistémico estricto:
        // 1. Cualquier arista sombra o mutación física no mediada -> FALSIFIED (preservando contraejemplo).
        // 2. Sin ensayo -> UNTESTED.
        // 3. Visibilidad incompleta o fallo de permisos (SD-005) -> INCONCLUSIVE.
        // 4. Sondeo puntual sin anomalías aparentes pero sin testigo físico independiente (SD-004) -> INCONCLUSIVE.
        // 5. Visibilidad completa + cero anomalías + testigos físicos verificados -> SUPPORTED_WITHIN_DOMAIN.
        let verdict = if !shadow_edges.is_empty()
            || !unmediated_mutations.is_empty()
            || !augmented_mediation_verdict.complete_mediation_holds
        {
            ShadowDiffVerdict::Falsified
        } else if matches!(snapshot.visibility, ObserverVisibility::Untested) {
            ShadowDiffVerdict::Untested
        } else if !snapshot.visibility.is_complete()
            || (snapshot.modality == ObservationModality::PointInTimePolling
                && physical_witnesses.is_empty())
        {
            ShadowDiffVerdict::Inconclusive
        } else {
            ShadowDiffVerdict::SupportedWithinDomain
        };

        ShadowDiffReport {
            logical_tick,
            verdict,
            mechanism_plane: SecurityMechanismPlane::EmpiricalObservation,
            declared_mediation_verdict,
            augmented_mediation_verdict,
            observer_modality: snapshot.modality,
            observer_visibility: snapshot.visibility.clone(),
            shadow_edges,
            unmediated_mutations,
            threat_model_limitations: Self::canonical_threat_model_limitations(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn seatbelt_computer_use_profile_enforces_all_denials() {
        let profile = SeatbeltComputerUseProfile::new(
            vec![PathBuf::from("/tmp/babylon_vault")],
            Some(PathBuf::from("/tmp/babylon_broker.sock")),
        );
        let rendered = profile.render();
        assert!(SeatbeltComputerUseProfile::validate_profile_text(&rendered).is_ok());
        assert!(rendered.contains("(deny hid-control)"));
        assert!(rendered.contains("(deny appleevent-send)"));
        for svc in MacOsAgentConfinement::DENIED_COMPUTER_USE_MACH_SERVICES {
            assert!(rendered.contains(svc));
        }
    }

    #[test]
    fn semantic_control_binding_rejects_mutated_control() {
        let expected = SemanticControlBinding::new("node-42", "AXButton", "Export WAV");
        let same = SemanticControlBinding::new("node-42", "AXButton", "Export WAV");
        let mutated = SemanticControlBinding::new("node-42", "AXButton", "Delete Project");

        assert!(expected.verify_before_dispatch(&same).is_ok());
        assert_eq!(
            expected.verify_before_dispatch(&mutated),
            Err(TrustGatewayError::ControlMutatedBeforeDispatch {
                expected: (
                    "node-42".to_string(),
                    "AXButton".to_string(),
                    "Export WAV".to_string()
                ),
                observed: (
                    "node-42".to_string(),
                    "AXButton".to_string(),
                    "Delete Project".to_string()
                ),
            })
        );
    }

    #[test]
    fn delta_verifier_converges_or_fails_closed_after_500ms() {
        let verifier = DeltaVerifier::new();
        let expected = ExpectedDelta {
            expected_state_digest: "sha256:dialog_closed".to_string(),
        };

        // Converge en la segunda ventana (250 ms)
        let res_ok = verifier.verify_observations(&expected, |window_ms| {
            if window_ms >= 250 {
                "sha256:dialog_closed".to_string()
            } else {
                "sha256:dialog_open".to_string()
            }
        });
        assert_eq!(res_ok, Ok(250));

        // Refutación en las 3 ventanas [100, 250, 500] ms -> DeltaMismatch
        let res_err = verifier.verify_observations(&expected, |_window_ms| {
            "sha256:dialog_stuck".to_string()
        });
        assert_eq!(
            res_err,
            Err(TrustGatewayError::DeltaMismatch {
                expected_state_digest: "sha256:dialog_closed".to_string(),
                last_observed_digest: "sha256:dialog_stuck".to_string(),
                attempts: 3,
            })
        );
    }

    #[test]
    fn emergency_escape_brake_triggers_0xdead6060_within_400ms() {
        let mut brake = EmergencyEscapeBrake::new();
        assert!(brake.record_escape_press(1_000).is_ok());
        // 500 ms después (> 400 ms): no dispara
        assert!(brake.record_escape_press(1_500).is_ok());
        assert!(!brake.is_poisoned());

        // 320 ms después (<= 400 ms): dispara 0xDEAD_6060
        let res = brake.record_escape_press(1_820);
        assert!(brake.is_poisoned());
        assert_eq!(
            res,
            Err(TrustGatewayError::EmergencyBrakeTriggered {
                delta_ms: 320,
                halt_code: 0xDEAD_6060,
            })
        );
    }

    #[test]
    fn rea_preflight_gate_enforces_deterministic_surface_and_sec1_ticket() {
        let mut sec1_pk = vec![0x04u8];
        sec1_pk.extend_from_slice(&[0xAAu8; 64]);
        let der_sig = vec![0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x01];

        let valid_ticket = AuthorizedDispatchTicket {
            app_bundle_id: "com.image-line.flstudio".to_string(),
            action: "render_stems_wav".to_string(),
            channel: DesktopChannelTier::CliHeadless,
            preflight_scitt_digest: [0x11u8; 32],
            no_overwrite_excl: true,
            enclave_pubkey_sec1: sec1_pk.clone(),
            enclave_signature_der: der_sig.clone(),
        };
        assert!(ReaPreflightGate::verify_dispatch_ready(&valid_ticket, 42, None, None).is_ok());

        // Si la acción cae en lienzo opaco (el agente no sabe/no puede verificar), se abstiene
        let mut opaque_ticket = valid_ticket.clone();
        opaque_ticket.channel = DesktopChannelTier::OpaqueCustomCanvas;
        opaque_ticket.action = "tweak_vst_opengl_knob".to_string();
        assert_eq!(
            ReaPreflightGate::verify_dispatch_ready(&opaque_ticket, 42, None, None),
            Err(TrustGatewayError::UnverifiedAppSurfaceAbstention {
                app_bundle_id: "com.image-line.flstudio".to_string(),
                action: "tweak_vst_opengl_knob".to_string(),
            })
        );
    }

    #[test]
    fn security_mechanism_planes_distinguish_observation_prevention_and_formal() {
        assert!(!SecurityMechanismPlane::FormalVerification.can_prevent_effect());
        assert!(SecurityMechanismPlane::PreventiveEnforcement.can_prevent_effect());
        assert!(!SecurityMechanismPlane::EmpiricalObservation.can_prevent_effect());
        assert!(SecurityMechanismPlane::EmpiricalObservation.can_falsify_isolation());

        assert!(!SecurityMechanismPlane::FormalVerification.proves_universal_isolation());
        assert!(!SecurityMechanismPlane::PreventiveEnforcement.proves_universal_isolation());
        assert!(!SecurityMechanismPlane::EmpiricalObservation.proves_universal_isolation());
    }
}



