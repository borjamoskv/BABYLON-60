use std::sync::OnceLock;
use std::convert::TryFrom;

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

    pub fn to_string(&self) -> String {
        format!("{}-{}-{}-{}", self.domain.as_str(), self.primitive.as_str(), self.modifier.as_str(), self.target.as_str())
    }
}

pub mod primitives_generated;

type Action = fn(&PrimitiveIdentity);

static KERNEL_TABLE: OnceLock<[Action; 10000]> = OnceLock::new();

fn default_dispatch_handler(identity: &PrimitiveIdentity) {
    println!(
        "⚡ [{:04}] {} executed via base transductor.",
        identity.code,
        identity.to_string()
    );
}

pub fn init_kernel() {
    let mut table = [default_dispatch_handler as Action; 10000];
    
    // Retroactively populate all 1000 actions from the generated taxonomy module
    for i in 0..10000 {
        if let Some(action) = primitives_generated::get_generated_action(i) {
            table[i] = action;
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
                return Ok(format!("Dispatched asynchronously: {}", identity.to_string()));
            }
            
            // Standard Sync Execution
            action(&identity);
            return Ok(format!("Dispatched: {}", identity.to_string()));
        }
    }
    
    Err("Kernel not initialized".to_string())
}

