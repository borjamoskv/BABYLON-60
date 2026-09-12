// ============================================================================
// B60 CANONICAL 60-OPCODE SEXAGESIMAL INSTRUCTION SET ARCHITECTURE (B60-ISA)
// ============================================================================

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SexaOpCode {
    // 00..09: Control de Flujo & Estados de Máquina
    Halt = 0,               // 0x00: Detención ordenada
    FailClosed = 1,         // 0x01: Parada atómica irrevocable (EU AI Act Art. 14)
    NoOp = 2,               // 0x02: No-operación exérgica
    Jump = 3,               // 0x03: Salto incondicional
    JumpIfZero = 4,         // 0x04: Salto condicional
    JumpIfNotZero = 5,      // 0x05: Salto si residuo sexagesimal > 0
    Call = 6,               // 0x06: Invocación de subrutina
    Return = 7,             // 0x07: Retorno de subrutina
    ForkSwarm = 8,          // 0x08: Bifurcación agéntica de enjambre (Legión)
    YieldTick = 9,          // 0x09: Ceder ciclo al planificador RTOS

    // 10..19: Aritmética Sexagesimal Racional Exacta (Q60)
    SexaAdd = 10,           // 0x0A: Suma sexagesimal con acarreo 60^k
    SexaSub = 11,           // 0x0B: Resta sexagesimal con préstamo
    SexaMulRational = 12,   // 0x0C: Multiplicación por factor entero sexa
    SexaDivRational = 13,   // 0x0D: División euclídea exacta en Q60
    SexaMod60 = 14,         // 0x0E: Residuo sexagesimal módulo 60
    SexaPack = 15,          // 0x0F: Empaquetar segundos y fracción
    SexaUnpack = 16,        // 0x10: Desempaquetar componentes
    SexaFloor = 17,         // 0x11: Truncar a entero de segundos
    SexaCeil = 18,          // 0x12: Redondeo superior al tick sexagesimal
    SexaAbs = 19,           // 0x13: Valor absoluto sexagesimal

    // 20..29: Operaciones de Manta de Markov y Teoría de la Información
    MarkovEnter = 20,       // 0x14: Aislar contexto en Manta de Markov
    MarkovExit = 21,        // 0x15: Transducir hacia estados activos
    FisherMetricProj = 22,  // 0x16: Proyección de Chentsov sobre geodésica
    KolmogorovAudit = 23,   // 0x17: Calcular ratio complejidad/diff
    LandauerRecord = 24,    // 0x18: Registrar borrado de bits (kB T ln 2)
    EntropyAssert = 25,     // 0x19: Falla si entropía > umbral
    MutualInfoCheck = 26,   // 0x1A: Verificar separación causal condicional
    PopperFalsify = 27,     // 0x1B: Ejecutar oráculo falsador de hipótesis
    CompressMDL = 28,       // 0x1C: Mínima longitud de descripción
    NoisePurge = 29,        // 0x1D: Purgar anergía residual fuera de la Manta

    // 30..39: Registro y Memoria Soberana de Silicio (Zero-Copy)
    LoadReg = 30,           // 0x1E: Cargar a registro R0..R7
    StoreReg = 31,          // 0x1F: Guardar de registro a manifest
    ManifestSync = 32,      // 0x20: Flush atómico de 64 bytes (Seqlock)
    ManifestAcquire = 33,   // 0x21: Lectura lock-free de 64 bytes
    PushStack = 34,         // 0x22: Push en pila lineal
    PopStack = 35,          // 0x23: Pop en pila lineal
    SwapStack = 36,         // 0x24: Intercambio en tope de pila
    AffinityPin = 37,       // 0x25: Pinning a Performance Core (P-Core)
    DirectAPFSIO = 38,      // 0x26: Escritura WORM sin pasar por cache FS
    ZeroCopyBorrow = 39,    // 0x27: Préstamo lineal de memoria compartida

    // 40..49: Criptografía de Silicio y Atestación de Hardware
    Sha3Block = 40,         // 0x28: Hash atómico SHA3-256 en acelerador ARM
    Ed25519Verify = 41,     // 0x29: Verificación de firma en hardware
    SepTouchIdSign = 42,    // 0x2A: Petición de firma al Secure Enclave
    ScittChainAppend = 43,  // 0x2B: Encadenar hash al ledger WORM
    CoseSignReceipt = 44,   // 0x2C: Emitir recibo COSE Sign1 (EU AI Act)
    KeyDeriveHKDF = 45,     // 0x2D: Derivación determinista de clave
    MerkleRootVerify = 46,  // 0x2E: Verificar árbol de Merkle en O(log n)
    TimestampAttest = 47,   // 0x2F: Sellado temporal con reloj sexagesimal
    NonceGenerate = 48,     // 0x30: Nonce cuántico/hardware sin repetición
    QuarantineIsolate = 49, // 0x31: Bloqueo forense de agente adulterado

    // 50..59: Gobernanza LegalTech y Cumplimiento EU AI Act
    EuAiActCheckRisk = 50,  // 0x32: Comprobación de categoría de alto riesgo
    HumanOversightPing = 51,// 0x33: Verificación de presencia humana activa
    AuditTrailSnapshot = 52,// 0x34: Exportar expediente forense firmado
    VprmStepScore = 53,     // 0x35: Verifiable Process Reward Model step
    BiasVarianceGate = 54,  // 0x36: Rechazar deriva discriminatoria/sesgo
    GoodhartDetector = 55,  // 0x37: Detectar optimización perversa del proxy
    WormIntegrityProbe = 56,// 0x38: Escaneo de integridad del ledger SQLite
    C5RealExergyScore = 57, // 0x39: Evaluación de exergía del sistema (1..21000)
    SovereignBftVote = 58,  // 0x3A: Voto BFT en consenso causal local
    OmegaFixedPoint = 59,   // 0x3B: Convergencia total de estado (Punto Fijo Omega)
}

impl SexaOpCode {
    pub fn from_u8(v: u8) -> Option<Self> {
        if v < 60 {
            Some(unsafe { std::mem::transmute(v) })
        } else {
            None
        }
    }

    pub fn mnemonic(&self) -> &'static str {
        match self {
            SexaOpCode::Halt => "HALT",
            SexaOpCode::FailClosed => "FAIL_CLOSED",
            SexaOpCode::NoOp => "NOOP",
            SexaOpCode::Jump => "JUMP",
            SexaOpCode::JumpIfZero => "JZ",
            SexaOpCode::JumpIfNotZero => "JNZ",
            SexaOpCode::Call => "CALL",
            SexaOpCode::Return => "RET",
            SexaOpCode::ForkSwarm => "FORK_SWARM",
            SexaOpCode::YieldTick => "YIELD_TICK",
            SexaOpCode::SexaAdd => "SEXA_ADD",
            SexaOpCode::SexaSub => "SEXA_SUB",
            SexaOpCode::SexaMulRational => "SEXA_MUL",
            SexaOpCode::SexaDivRational => "SEXA_DIV",
            SexaOpCode::SexaMod60 => "SEXA_MOD60",
            SexaOpCode::SexaPack => "SEXA_PACK",
            SexaOpCode::SexaUnpack => "SEXA_UNPACK",
            SexaOpCode::SexaFloor => "SEXA_FLOOR",
            SexaOpCode::SexaCeil => "SEXA_CEIL",
            SexaOpCode::SexaAbs => "SEXA_ABS",
            SexaOpCode::MarkovEnter => "MARKOV_ENTER",
            SexaOpCode::MarkovExit => "MARKOV_EXIT",
            SexaOpCode::FisherMetricProj => "FISHER_PROJ",
            SexaOpCode::KolmogorovAudit => "KOLMOGOROV_AUDIT",
            SexaOpCode::LandauerRecord => "LANDAUER_RECORD",
            SexaOpCode::EntropyAssert => "ENTROPY_ASSERT",
            SexaOpCode::MutualInfoCheck => "MUTUAL_INFO_CHECK",
            SexaOpCode::PopperFalsify => "POPPER_FALSIFY",
            SexaOpCode::CompressMDL => "COMPRESS_MDL",
            SexaOpCode::NoisePurge => "NOISE_PURGE",
            SexaOpCode::LoadReg => "LOAD_REG",
            SexaOpCode::StoreReg => "STORE_REG",
            SexaOpCode::ManifestSync => "MANIFEST_SYNC",
            SexaOpCode::ManifestAcquire => "MANIFEST_ACQUIRE",
            SexaOpCode::PushStack => "PUSH",
            SexaOpCode::PopStack => "POP",
            SexaOpCode::SwapStack => "SWAP",
            SexaOpCode::AffinityPin => "AFFINITY_PIN",
            SexaOpCode::DirectAPFSIO => "DIRECT_APFS_IO",
            SexaOpCode::ZeroCopyBorrow => "ZERO_COPY_BORROW",
            SexaOpCode::Sha3Block => "SHA3_BLOCK",
            SexaOpCode::Ed25519Verify => "ED25519_VERIFY",
            SexaOpCode::SepTouchIdSign => "TOUCHID_SIGN",
            SexaOpCode::ScittChainAppend => "WORM_COMMIT",
            SexaOpCode::CoseSignReceipt => "COSE_RECEIPT",
            SexaOpCode::KeyDeriveHKDF => "KEY_DERIVE",
            SexaOpCode::MerkleRootVerify => "MERKLE_VERIFY",
            SexaOpCode::TimestampAttest => "TIMESTAMP_ATTEST",
            SexaOpCode::NonceGenerate => "NONCE_GEN",
            SexaOpCode::QuarantineIsolate => "QUARANTINE_ISOLATE",
            SexaOpCode::EuAiActCheckRisk => "EU_AI_CHECK_RISK",
            SexaOpCode::HumanOversightPing => "HUMAN_OVERSIGHT_PING",
            SexaOpCode::AuditTrailSnapshot => "AUDIT_TRAIL_SNAP",
            SexaOpCode::VprmStepScore => "VPRM_STEP_SCORE",
            SexaOpCode::BiasVarianceGate => "BIAS_VARIANCE_GATE",
            SexaOpCode::GoodhartDetector => "GOODHART_DETECTOR",
            SexaOpCode::WormIntegrityProbe => "WORM_PROBE",
            SexaOpCode::C5RealExergyScore => "C5_EXERGY_SCORE",
            SexaOpCode::SovereignBftVote => "BFT_VOTE",
            SexaOpCode::OmegaFixedPoint => "OMEGA_FIXED_POINT",
        }
    }
}
