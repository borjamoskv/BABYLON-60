// FL-011 — Seqlock transaccional de época de política (B60-02 / B60-03).
//
// El snapshot se almacena como tres `AtomicU64` accedidos con `Relaxed` dentro
// del protocolo seqlock (fences Release/Acquire). Esto elimina la data race
// formal de `read_volatile`/`write_volatile` sobre datos no atómicos.

use core::sync::atomic::{fence, AtomicU64, Ordering};

/// Instantánea inmutable de política.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PolicySnapshot {
    /// Época de política del kernel.
    pub policy_epoch: u64,
    /// Bitmap de capacidades activas.
    pub capability_bitmap: u64,
    /// Máscara de agentes revocados.
    pub revoked_agents_mask: u64,
}

/// Errores fail-closed de FL-011.
#[derive(Debug, PartialEq, Eq)]
pub enum Fl011Error {
    /// Había una escritura en curso (secuencia impar).
    ConcurrentWriteInProgress,
    /// La política rotó entre el inicio y el fin de la ejecución.
    EpochInvalidatedDuringExecution {
        /// Secuencia al comienzo.
        start_seq: u64,
        /// Secuencia observada al final.
        end_seq: u64,
    },
    /// Agente revocado (o identificador fuera de rango).
    AgentRevoked,
    /// Capacidad denegada (o bit fuera de rango).
    CapabilityDenied,
    /// El lease expiró respecto a la época del kernel.
    CausalLeaseExpired {
        /// Época de expiración del lease.
        lease_epoch: u64,
        /// Época actual del kernel.
        kernel_epoch: u64,
    },
}

/// Seqlock de política con lectura sin bloqueo.
pub struct Fl011Seqlock {
    seq: AtomicU64,
    epoch: AtomicU64,
    caps: AtomicU64,
    revoked: AtomicU64,
}

impl Fl011Seqlock {
    /// Crea el seqlock con una política inicial (secuencia 0 = reposo).
    #[must_use]
    pub const fn new(initial: PolicySnapshot) -> Self {
        Self {
            seq: AtomicU64::new(0),
            epoch: AtomicU64::new(initial.policy_epoch),
            caps: AtomicU64::new(initial.capability_bitmap),
            revoked: AtomicU64::new(initial.revoked_agents_mask),
        }
    }

    /// Publica una nueva política. Los escritores se serializan por CAS par→impar.
    pub fn update_policy(&self, next: PolicySnapshot) {
        let s0 = loop {
            let s = self.seq.load(Ordering::Relaxed);
            if s & 1 == 0
                && self
                    .seq
                    .compare_exchange_weak(s, s.wrapping_add(1), Ordering::Acquire, Ordering::Relaxed)
                    .is_ok()
            {
                break s;
            }
            core::hint::spin_loop();
        };
        // Los stores de datos no pueden reordenarse antes de la marca impar.
        fence(Ordering::Release);
        self.epoch.store(next.policy_epoch, Ordering::Relaxed);
        self.caps.store(next.capability_bitmap, Ordering::Relaxed);
        self.revoked.store(next.revoked_agents_mask, Ordering::Relaxed);
        self.seq.store(s0.wrapping_add(2), Ordering::Release);
    }

    /// Lectura consistente del snapshot o error si hay escritura en curso/desgarro.
    fn read_consistent(&self) -> Result<(u64, PolicySnapshot), Fl011Error> {
        let seq1 = self.seq.load(Ordering::Acquire);
        if seq1 & 1 != 0 {
            return Err(Fl011Error::ConcurrentWriteInProgress);
        }
        let snap = PolicySnapshot {
            policy_epoch: self.epoch.load(Ordering::Relaxed),
            capability_bitmap: self.caps.load(Ordering::Relaxed),
            revoked_agents_mask: self.revoked.load(Ordering::Relaxed),
        };
        fence(Ordering::Acquire);
        let seq_mid = self.seq.load(Ordering::Relaxed);
        if seq1 != seq_mid {
            return Err(Fl011Error::EpochInvalidatedDuringExecution {
                start_seq: seq1,
                end_seq: seq_mid,
            });
        }
        Ok((seq1, snap))
    }

    /// Ejecuta una transición pura sólo si la política permanece idéntica de principio a fin.
    /// Cierra B60-02 (lease por época del kernel) y B60-03 (TOCTOU de persistencia cognitiva).
    ///
    /// # Errors
    /// Devuelve `Fl011Error` ante escritura concurrente, lease expirado, agente revocado,
    /// capacidad denegada o rotación de política durante la transición.
    pub fn execute_guarded<F, R>(
        &self,
        agent_id: u8,
        required_cap_bit: u8,
        lease_expiration_epoch: u64,
        transition: F,
    ) -> Result<(R, u64, u64), Fl011Error>
    where
        F: FnOnce(PolicySnapshot) -> R,
    {
        let (seq1, snap) = self.read_consistent()?;

        if snap.policy_epoch > lease_expiration_epoch {
            return Err(Fl011Error::CausalLeaseExpired {
                lease_epoch: lease_expiration_epoch,
                kernel_epoch: snap.policy_epoch,
            });
        }

        // Identificadores fuera de [0, 64) son fail-closed (evita overflow de shift).
        let agent_bit = 1u64.checked_shl(u32::from(agent_id)).ok_or(Fl011Error::AgentRevoked)?;
        if snap.revoked_agents_mask & agent_bit != 0 {
            return Err(Fl011Error::AgentRevoked);
        }
        let cap_bit = 1u64
            .checked_shl(u32::from(required_cap_bit))
            .ok_or(Fl011Error::CapabilityDenied)?;
        if snap.capability_bitmap & cap_bit == 0 {
            return Err(Fl011Error::CapabilityDenied);
        }

        let output = transition(snap);

        fence(Ordering::Acquire);
        let seq2 = self.seq.load(Ordering::Relaxed);
        if seq1 != seq2 {
            return Err(Fl011Error::EpochInvalidatedDuringExecution {
                start_seq: seq1,
                end_seq: seq2,
            });
        }

        Ok((output, seq1, snap.policy_epoch))
    }
}
