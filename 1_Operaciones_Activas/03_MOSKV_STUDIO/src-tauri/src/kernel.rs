// C5-REAL EXERGY CERTIFIED
use std::convert::TryFrom;
use std::sync::OnceLock;

// 1000-Primitive Action Space Enums
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Domain {
    Source = 0,
    Matrix = 1,
    Pulse = 2,
    Kinetic = 3,
    Logic = 4,
    Vector = 5,
    Storage = 6,
    Osint = 7,
    Clock = 8,
    Compiler = 9,
}

impl TryFrom<u8> for Domain {
    type Error = &'static str;
    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Domain::Source),
            1 => Ok(Domain::Matrix),
            2 => Ok(Domain::Pulse),
            3 => Ok(Domain::Kinetic),
            4 => Ok(Domain::Logic),
            5 => Ok(Domain::Vector),
            6 => Ok(Domain::Storage),
            7 => Ok(Domain::Osint),
            8 => Ok(Domain::Clock),
            9 => Ok(Domain::Compiler),
            _ => Err("Invalid Domain index"),
        }
    }
}

impl Domain {
    pub fn as_str(&self) -> &'static str {
        match self {
            Domain::Source => "SOURCE",
            Domain::Matrix => "MATRIX",
            Domain::Pulse => "PULSE",
            Domain::Kinetic => "KINETIC",
            Domain::Logic => "LOGIC",
            Domain::Vector => "VECTOR",
            Domain::Storage => "STORAGE",
            Domain::Osint => "OSINT",
            Domain::Clock => "CLOCK",
            Domain::Compiler => "COMPILER",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Primitive {
    Init = 0,
    Mutate = 1,
    Bind = 2,
    Query = 3,
    Stream = 4,
    Commit = 5,
    Sync = 6,
    Halt = 7,
    Fork = 8,
    Join = 9,
}

impl TryFrom<u8> for Primitive {
    type Error = &'static str;
    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Primitive::Init),
            1 => Ok(Primitive::Mutate),
            2 => Ok(Primitive::Bind),
            3 => Ok(Primitive::Query),
            4 => Ok(Primitive::Stream),
            5 => Ok(Primitive::Commit),
            6 => Ok(Primitive::Sync),
            7 => Ok(Primitive::Halt),
            8 => Ok(Primitive::Fork),
            9 => Ok(Primitive::Join),
            _ => Err("Invalid Primitive index"),
        }
    }
}

impl Primitive {
    pub fn as_str(&self) -> &'static str {
        match self {
            Primitive::Init => "INIT",
            Primitive::Mutate => "MUTATE",
            Primitive::Bind => "BIND",
            Primitive::Query => "QUERY",
            Primitive::Stream => "STREAM",
            Primitive::Commit => "COMMIT",
            Primitive::Sync => "SYNC",
            Primitive::Halt => "HALT",
            Primitive::Fork => "FORK",
            Primitive::Join => "JOIN",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Modifier {
    Raw = 0,
    Atomic = 1,
    Persist = 2,
    Ephemeral = 3,
    Async = 4,
    Sync = 5,
    Quantized = 6,
    Mapped = 7,
    Wrapped = 8,
    Locked = 9,
}

impl TryFrom<u8> for Modifier {
    type Error = &'static str;
    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Modifier::Raw),
            1 => Ok(Modifier::Atomic),
            2 => Ok(Modifier::Persist),
            3 => Ok(Modifier::Ephemeral),
            4 => Ok(Modifier::Async),
            5 => Ok(Modifier::Sync),
            6 => Ok(Modifier::Quantized),
            7 => Ok(Modifier::Mapped),
            8 => Ok(Modifier::Wrapped),
            9 => Ok(Modifier::Locked),
            _ => Err("Invalid Modifier index"),
        }
    }
}

impl Modifier {
    pub fn as_str(&self) -> &'static str {
        match self {
            Modifier::Raw => "RAW",
            Modifier::Atomic => "ATOMIC",
            Modifier::Persist => "PERSIST",
            Modifier::Ephemeral => "EPHEMERAL",
            Modifier::Async => "ASYNC",
            Modifier::Sync => "SYNC",
            Modifier::Quantized => "QUANTIZED",
            Modifier::Mapped => "MAPPED",
            Modifier::Wrapped => "WRAPPED",
            Modifier::Locked => "LOCKED",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Target {
    Local = 0,
    Network = 1,
    Swarm = 2,
    Ledger = 3,
    Memory = 4,
    Dispatch = 5,
    Ui = 6,
    System = 7,
    Bft = 8,
    Core = 9,
}

impl TryFrom<u8> for Target {
    type Error = &'static str;
    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Target::Local),
            1 => Ok(Target::Network),
            2 => Ok(Target::Swarm),
            3 => Ok(Target::Ledger),
            4 => Ok(Target::Memory),
            5 => Ok(Target::Dispatch),
            6 => Ok(Target::Ui),
            7 => Ok(Target::System),
            8 => Ok(Target::Bft),
            9 => Ok(Target::Core),
            _ => Err("Invalid Target index"),
        }
    }
}

impl Target {
    pub fn as_str(&self) -> &'static str {
        match self {
            Target::Local => "LOCAL",
            Target::Network => "NETWORK",
            Target::Swarm => "SWARM",
            Target::Ledger => "LEDGER",
            Target::Memory => "MEMORY",
            Target::Dispatch => "DISPATCH",
            Target::Ui => "UI",
            Target::System => "SYSTEM",
            Target::Bft => "BFT",
            Target::Core => "CORE",
        }
    }
}

#[derive(Debug, Clone)]
pub struct PrimitiveIdentity {
    pub domain: Domain,
    pub primitive: Primitive,
    pub modifier: Modifier,
    pub target: Target,
    pub code: u16,
}

impl PrimitiveIdentity {
    pub fn new(d: u8, p: u8, m: u8, t: u8) -> Result<Self, &'static str> {
        let domain = Domain::try_from(d)?;
        let primitive = Primitive::try_from(p)?;
        let modifier = Modifier::try_from(m)?;
        let target = Target::try_from(t)?;
        let code = (d as u16 * 1000) + (p as u16 * 100) + (m as u16 * 10) + t as u16;
        Ok(Self {
            domain,
            primitive,
            modifier,
            target,
            code,
        })
    }
}

impl std::fmt::Display for PrimitiveIdentity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}-{}-{}-{}",
            self.domain.as_str(),
            self.primitive.as_str(),
            self.modifier.as_str(),
            self.target.as_str()
        )
    }
}

use crate::primitives_generated;

type Action = fn(&PrimitiveIdentity);

static KERNEL_TABLE: OnceLock<[Action; 10000]> = OnceLock::new();

fn default_dispatch_handler(identity: &PrimitiveIdentity) {
    println!(
        "⚡ [{:04}] {} executed via base transductor.",
        identity.code, identity
    );
}

pub fn init_kernel() {
    let mut table = [default_dispatch_handler as Action; 10000];

    // Retroactively populate all 1000 actions from the generated taxonomy module
    for (i, slot) in table.iter_mut().enumerate() {
        if let Some(action) = primitives_generated::get_generated_action(i) {
            *slot = action;
        }
    }

    KERNEL_TABLE.set(table).ok();
}

#[tauri::command]
pub fn dispatch(d: u8, p: u8, m: u8, t: u8) -> Result<String, String> {
    let identity = PrimitiveIdentity::new(d, p, m, t).map_err(|e| e.to_string())?;

    if let Some(table) = KERNEL_TABLE.get() {
        let index = identity.code as usize;
        if index < 10000 {
            let action = table[index];

            // Async modifier handling:
            if identity.modifier == Modifier::Async {
                let id_clone = identity.clone();
                std::thread::spawn(move || {
                    action(&id_clone);
                });
                return Ok(format!("Dispatched asynchronously: {}", identity));
            }

            // Standard Sync Execution
            action(&identity);
            return Ok(format!("Dispatched: {}", identity));
        }
    }

    Err("Kernel not initialized".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::convert::TryFrom;

    // ── Domain ────────────────────────────────────────────────────────────────

    #[test]
    fn domain_try_from_all_valid_indices() {
        let cases: &[(u8, Domain, &str)] = &[
            (0, Domain::Source, "SOURCE"),
            (1, Domain::Matrix, "MATRIX"),
            (2, Domain::Pulse, "PULSE"),
            (3, Domain::Kinetic, "KINETIC"),
            (4, Domain::Logic, "LOGIC"),
            (5, Domain::Vector, "VECTOR"),
            (6, Domain::Storage, "STORAGE"),
            (7, Domain::Osint, "OSINT"),
            (8, Domain::Clock, "CLOCK"),
            (9, Domain::Compiler, "COMPILER"),
        ];
        for &(idx, ref variant, label) in cases {
            let d = Domain::try_from(idx).expect("valid index must succeed");
            assert_eq!(d, *variant);
            assert_eq!(d.as_str(), label);
        }
    }

    #[test]
    fn domain_try_from_oob_returns_err() {
        assert!(Domain::try_from(10).is_err());
        assert!(Domain::try_from(255).is_err());
    }

    // ── Primitive ─────────────────────────────────────────────────────────────

    #[test]
    fn primitive_try_from_all_valid_indices() {
        let cases: &[(u8, Primitive, &str)] = &[
            (0, Primitive::Init, "INIT"),
            (1, Primitive::Mutate, "MUTATE"),
            (2, Primitive::Bind, "BIND"),
            (3, Primitive::Query, "QUERY"),
            (4, Primitive::Stream, "STREAM"),
            (5, Primitive::Commit, "COMMIT"),
            (6, Primitive::Sync, "SYNC"),
            (7, Primitive::Halt, "HALT"),
            (8, Primitive::Fork, "FORK"),
            (9, Primitive::Join, "JOIN"),
        ];
        for &(idx, ref variant, label) in cases {
            let p = Primitive::try_from(idx).expect("valid index must succeed");
            assert_eq!(p, *variant);
            assert_eq!(p.as_str(), label);
        }
    }

    #[test]
    fn primitive_try_from_oob_returns_err() {
        assert!(Primitive::try_from(10).is_err());
        assert!(Primitive::try_from(200).is_err());
    }

    // ── Modifier ──────────────────────────────────────────────────────────────

    #[test]
    fn modifier_try_from_all_valid_indices() {
        let cases: &[(u8, Modifier, &str)] = &[
            (0, Modifier::Raw, "RAW"),
            (1, Modifier::Atomic, "ATOMIC"),
            (2, Modifier::Persist, "PERSIST"),
            (3, Modifier::Ephemeral, "EPHEMERAL"),
            (4, Modifier::Async, "ASYNC"),
            (5, Modifier::Sync, "SYNC"),
            (6, Modifier::Quantized, "QUANTIZED"),
            (7, Modifier::Mapped, "MAPPED"),
            (8, Modifier::Wrapped, "WRAPPED"),
            (9, Modifier::Locked, "LOCKED"),
        ];
        for &(idx, ref variant, label) in cases {
            let m = Modifier::try_from(idx).expect("valid index must succeed");
            assert_eq!(m, *variant);
            assert_eq!(m.as_str(), label);
        }
    }

    #[test]
    fn modifier_try_from_oob_returns_err() {
        assert!(Modifier::try_from(10).is_err());
    }

    // ── Target ────────────────────────────────────────────────────────────────

    #[test]
    fn target_try_from_all_valid_indices() {
        let cases: &[(u8, Target, &str)] = &[
            (0, Target::Local, "LOCAL"),
            (1, Target::Network, "NETWORK"),
            (2, Target::Swarm, "SWARM"),
            (3, Target::Ledger, "LEDGER"),
            (4, Target::Memory, "MEMORY"),
            (5, Target::Dispatch, "DISPATCH"),
            (6, Target::Ui, "UI"),
            (7, Target::System, "SYSTEM"),
            (8, Target::Bft, "BFT"),
            (9, Target::Core, "CORE"),
        ];
        for &(idx, ref variant, label) in cases {
            let t = Target::try_from(idx).expect("valid index must succeed");
            assert_eq!(t, *variant);
            assert_eq!(t.as_str(), label);
        }
    }

    #[test]
    fn target_try_from_oob_returns_err() {
        assert!(Target::try_from(10).is_err());
    }

    // ── PrimitiveIdentity ─────────────────────────────────────────────────────

    #[test]
    fn primitive_identity_code_arithmetic() {
        // code = d*1000 + p*100 + m*10 + t
        let id = PrimitiveIdentity::new(3, 7, 2, 5).unwrap();
        assert_eq!(id.code, 3725u16);
    }

    #[test]
    fn primitive_identity_zero_produces_code_0() {
        let id = PrimitiveIdentity::new(0, 0, 0, 0).unwrap();
        assert_eq!(id.code, 0);
    }

    #[test]
    fn primitive_identity_max_produces_code_9999() {
        let id = PrimitiveIdentity::new(9, 9, 9, 9).unwrap();
        assert_eq!(id.code, 9999);
    }

    #[test]
    fn primitive_identity_oob_domain_returns_err() {
        assert!(PrimitiveIdentity::new(10, 0, 0, 0).is_err());
    }

    #[test]
    fn primitive_identity_oob_primitive_returns_err() {
        assert!(PrimitiveIdentity::new(0, 10, 0, 0).is_err());
    }

    #[test]
    fn primitive_identity_oob_modifier_returns_err() {
        assert!(PrimitiveIdentity::new(0, 0, 10, 0).is_err());
    }

    #[test]
    fn primitive_identity_oob_target_returns_err() {
        assert!(PrimitiveIdentity::new(0, 0, 0, 10).is_err());
    }

    #[test]
    fn primitive_identity_to_string_source_init_raw_local() {
        let id = PrimitiveIdentity::new(0, 0, 0, 0).unwrap();
        assert_eq!(id.to_string(), "SOURCE-INIT-RAW-LOCAL");
    }

    #[test]
    fn primitive_identity_to_string_logic_query_atomic_core() {
        let id = PrimitiveIdentity::new(4, 3, 1, 9).unwrap();
        assert_eq!(id.to_string(), "LOGIC-QUERY-ATOMIC-CORE");
    }

    // ── Kernel init & dispatch ────────────────────────────────────────────────

    #[test]
    fn init_kernel_is_idempotent() {
        init_kernel();
        init_kernel(); // second call must not panic
        assert!(KERNEL_TABLE.get().is_some());
    }

    #[test]
    fn dispatch_sync_returns_ok_with_identity_label() {
        init_kernel();
        let result = dispatch(0, 0, 0, 0);
        assert!(result.is_ok());
        let msg = result.unwrap();
        assert!(msg.contains("SOURCE-INIT-RAW-LOCAL"), "got: {msg}");
    }

    #[test]
    fn dispatch_async_modifier_returns_dispatched_asynchronously() {
        init_kernel();
        // Modifier index 4 = Async
        let result = dispatch(0, 0, 4, 0);
        assert!(result.is_ok());
        let msg = result.unwrap();
        assert!(msg.contains("asynchronously"), "got: {msg}");
    }

    #[test]
    fn dispatch_oob_d_returns_err() {
        init_kernel();
        assert!(dispatch(10, 0, 0, 0).is_err());
    }

    #[test]
    fn dispatch_oob_p_returns_err() {
        init_kernel();
        assert!(dispatch(0, 10, 0, 0).is_err());
    }

    #[test]
    fn dispatch_oob_m_returns_err() {
        init_kernel();
        assert!(dispatch(0, 0, 10, 0).is_err());
    }

    #[test]
    fn dispatch_oob_t_returns_err() {
        init_kernel();
        assert!(dispatch(0, 0, 0, 10).is_err());
    }

    #[test]
    fn dispatch_all_domains_resolve() {
        init_kernel();
        for d in 0u8..10 {
            assert!(dispatch(d, 0, 0, 0).is_ok(), "domain {d} failed");
        }
    }

    #[test]
    fn dispatch_all_primitives_resolve() {
        init_kernel();
        for p in 0u8..10 {
            assert!(dispatch(0, p, 0, 0).is_ok(), "primitive {p} failed");
        }
    }

    #[test]
    fn dispatch_compiler_join_sync_core_label() {
        init_kernel();
        let r = dispatch(9, 9, 5, 9).unwrap();
        assert!(r.contains("COMPILER-JOIN-SYNC-CORE"), "got: {r}");
    }
}
