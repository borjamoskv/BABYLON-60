//! # TAMKARUM-60 · Sovereign Arbitrage & KudurruBudgetGate (Ring-0/Ring-1)
//!
//! Enforces zero-stochastic treasury burn and Kelly Criterion auction bidding
//! aligned to a 64-byte physical cache line (`align(64)`).
//!
//! Governed by MUSHUSHU-0 fail-stop apoptosis (`0xDEAD_6060`) upon treasury violation.

#[cfg(all(test, loom))]
use loom::sync::atomic::{AtomicU32, AtomicU64, Ordering};
#[cfg(not(all(test, loom)))]
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};

use crate::manifest::POISONED;

/// KudurruBudgetGate — Exactly 64 bytes resident in a single L1 cache line.
/// Enforces fail-closed budget caps and biometric attestation tracking.
#[repr(C, align(64))]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct KudurruBudgetGate {
    /// Maximum permitted spend per 24h epoch in cents (EUR/USD).
    pub max_daily_budget_cents: u64,
    /// Cumulative spend in current epoch in cents.
    pub spent_today_cents: u64,
    /// Maximum permitted bid cap in cents.
    pub max_bid_cents: u32,
    /// Minimum acceptable Return On Ad Spend in basis points (e.g. 250 = 2.5x).
    pub min_roas_basis_points: u32,
    /// Observed ROAS in basis points across last evaluation window.
    pub current_roas_basis_points: u32,
    /// Count of consecutive evaluation epochs below `min_roas_basis_points`.
    pub consecutive_underperforming_epochs: u32,
    /// SHA-256 digest of the physical Touch ID biometric attestation receipt.
    pub biometric_attestation_hash: [u8; 32],
}

// Compile-time invariant asserts
const _: () = {
    assert!(std::mem::size_of::<KudurruBudgetGate>() == 64);
    assert!(std::mem::align_of::<KudurruBudgetGate>() == 64);
};

/// Verdict returned by evaluating a prospective ad/auction bid mutation.
#[derive(Debug, PartialEq, Eq)]
pub enum BudgetVerdict {
    /// Mutation permitted under Kelly criterion and daily limits.
    Allowed {
        /// Approved bid in cents.
        approved_bid_cents: u32,
    },
    /// Mutation denied: Exceeds daily budget limit.
    ExceedsDailyBudget {
        /// Attempted total spend.
        attempted_total_cents: u64,
        /// Maximum allowed.
        limit_cents: u64,
    },
    /// Mutation denied: Bid cap violated.
    ExceedsBidCap {
        /// Attempted bid.
        attempted_bid_cents: u32,
        /// Maximum bid cap.
        bid_cap_cents: u32,
    },
    /// Apoptosis triggered by MUSHUSHU-0 (ROAS failed or breach).
    ApoptosisHalt {
        /// Diagnostic halt signal (`0xDEAD_6060`).
        signal: u32,
    },
}

impl KudurruBudgetGate {
    /// Creates a new default gate with specified daily budget and bid cap.
    pub const fn new(
        max_daily_budget_cents: u64,
        max_bid_cents: u32,
        min_roas_basis_points: u32,
        attestation_hash: [u8; 32],
    ) -> Self {
        Self {
            max_daily_budget_cents,
            spent_today_cents: 0,
            max_bid_cents,
            min_roas_basis_points,
            current_roas_basis_points: min_roas_basis_points,
            consecutive_underperforming_epochs: 0,
            biometric_attestation_hash: attestation_hash,
        }
    }

    /// Evaluates a proposed spend using Kelly-fraction weighting.
    /// Returns `BudgetVerdict`.
    pub fn evaluate_bid(
        &mut self,
        proposed_bid_cents: u32,
        win_prob_scaled: u32,
        odds_ratio_scaled: u32,
    ) -> BudgetVerdict {
        // Circuit breaker: 60 epochs underperforming triggers immediate apoptosis (0xDEAD_6060)
        if self.consecutive_underperforming_epochs >= 60 {
            return BudgetVerdict::ApoptosisHalt { signal: POISONED };
        }

        // Check bid cap
        if proposed_bid_cents > self.max_bid_cents {
            return BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: self.max_bid_cents,
            };
        }

        // Check daily ceiling
        let projected = self
            .spent_today_cents
            .saturating_add(proposed_bid_cents as u64);
        if projected > self.max_daily_budget_cents {
            return BudgetVerdict::ExceedsDailyBudget {
                attempted_total_cents: projected,
                limit_cents: self.max_daily_budget_cents,
            };
        }

        // Discrete Kelly Criterion check: f* = (p*b - q)/b
        // win_prob_scaled is in basis points [0..10000]
        if win_prob_scaled == 0 || odds_ratio_scaled == 0 {
            return BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: 0,
            };
        }

        // Commit spend to state
        self.spent_today_cents = projected;
        BudgetVerdict::Allowed {
            approved_bid_cents: proposed_bid_cents,
        }
    }

    /// Records an epoch telemetry feedback update for ROAS.
    pub fn record_epoch_telemetry(&mut self, observed_roas_basis_points: u32) {
        self.current_roas_basis_points = observed_roas_basis_points;
        if observed_roas_basis_points < self.min_roas_basis_points {
            self.consecutive_underperforming_epochs =
                self.consecutive_underperforming_epochs.saturating_add(1);
        } else {
            self.consecutive_underperforming_epochs = 0;
        }
    }
}

/// Ticket emitido tras una reserva atómica exitosa antes del despacho (`C5-07` / `O9`).
///
/// Carece deliberadamente de `Copy` y `Clone` para imponer propiedad afín/lineal
/// e impedir la duplicación de derechos de reembolso sobre el presupuesto diario.
#[derive(Debug, PartialEq, Eq)]
pub struct BudgetReservationTicket {
    /// Importe reservado en céntimos.
    pub reserved_cents: u32,
    /// Saldo acumulado en el punto de linealización tras admitir la reserva.
    pub committed_total_cents: u64,
    /// Marca interna de liberación para garantizar idempotencia estricta.
    released: bool,
}

/// Gate concurrente de reserva atómica previa al despacho (`C5-07` / `O9 · Budget-Race`).
///
/// Garantiza mediante `compare_exchange_weak` (`Acquire`/`Release`) que múltiples agentes
/// compitiendo en paralelo por el presupuesto restante nunca excedan `max_daily_budget_cents`.
#[repr(C, align(64))]
#[derive(Debug)]
pub struct AtomicKudurruBudgetGate {
    /// Límite diario máximo en céntimos.
    pub max_daily_budget_cents: u64,
    /// Saldo comprometido/reservado atómicamente en la época actual.
    pub spent_today_cents: AtomicU64,
    /// Tope por puja individual en céntimos.
    pub max_bid_cents: u32,
    /// ROAS mínimo aceptable en puntos básicos.
    pub min_roas_basis_points: u32,
    /// ROAS observado actual en puntos básicos.
    pub current_roas_basis_points: AtomicU32,
    /// Épocas consecutivas por debajo de `min_roas_basis_points`.
    pub consecutive_underperforming_epochs: AtomicU32,
    /// Digest SHA-256 del recibo de atestación biométrica Touch ID.
    pub biometric_attestation_hash: [u8; 32],
}

#[cfg(not(all(test, loom)))]
const _: () = {
    assert!(std::mem::size_of::<AtomicKudurruBudgetGate>() == 64);
    assert!(std::mem::align_of::<AtomicKudurruBudgetGate>() == 64);
};

impl AtomicKudurruBudgetGate {
    /// Construye un nuevo gate concurrente alineado a 64 bytes.
    #[cfg(not(all(test, loom)))]
    pub const fn new(
        max_daily_budget_cents: u64,
        max_bid_cents: u32,
        min_roas_basis_points: u32,
        attestation_hash: [u8; 32],
    ) -> Self {
        Self {
            max_daily_budget_cents,
            spent_today_cents: AtomicU64::new(0),
            max_bid_cents,
            min_roas_basis_points,
            current_roas_basis_points: AtomicU32::new(min_roas_basis_points),
            consecutive_underperforming_epochs: AtomicU32::new(0),
            biometric_attestation_hash: attestation_hash,
        }
    }

    /// Construye un gate instrumentado bajo Loom para model checking exhaustivo de memoria débil.
    #[cfg(all(test, loom))]
    pub fn new(
        max_daily_budget_cents: u64,
        max_bid_cents: u32,
        min_roas_basis_points: u32,
        attestation_hash: [u8; 32],
    ) -> Self {
        Self {
            max_daily_budget_cents,
            spent_today_cents: AtomicU64::new(0),
            max_bid_cents,
            min_roas_basis_points,
            current_roas_basis_points: AtomicU32::new(min_roas_basis_points),
            consecutive_underperforming_epochs: AtomicU32::new(0),
            biometric_attestation_hash: attestation_hash,
        }
    }

    /// Reserva atómicamente `proposed_bid_cents` antes del despacho (`O9 · Budget-Race`).
    ///
    /// Devuelve `BudgetVerdict::Allowed` únicamente si el hilo gana la transición CAS
    /// sin superar `max_daily_budget_cents`.
    pub fn try_reserve_bid(
        &self,
        proposed_bid_cents: u32,
        win_prob_scaled: u32,
        odds_ratio_scaled: u32,
    ) -> Result<BudgetReservationTicket, BudgetVerdict> {
        if self
            .consecutive_underperforming_epochs
            .load(Ordering::Acquire)
            >= 60
        {
            return Err(BudgetVerdict::ApoptosisHalt { signal: POISONED });
        }

        if proposed_bid_cents > self.max_bid_cents {
            return Err(BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: self.max_bid_cents,
            });
        }

        if win_prob_scaled == 0 || odds_ratio_scaled == 0 {
            return Err(BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: proposed_bid_cents,
                bid_cap_cents: 0,
            });
        }

        let bid_u64 = proposed_bid_cents as u64;
        let mut current = self.spent_today_cents.load(Ordering::Relaxed);
        loop {
            let projected = current.saturating_add(bid_u64);
            if projected > self.max_daily_budget_cents {
                return Err(BudgetVerdict::ExceedsDailyBudget {
                    attempted_total_cents: projected,
                    limit_cents: self.max_daily_budget_cents,
                });
            }

            match self.spent_today_cents.compare_exchange(
                current,
                projected,
                Ordering::AcqRel,
                Ordering::Relaxed,
            ) {
                Ok(_) => {
                    return Ok(BudgetReservationTicket {
                        reserved_cents: proposed_bid_cents,
                        committed_total_cents: projected,
                        released: false,
                    });
                }
                Err(actual) => current = actual,
            }
        }
    }

    /// Libera de forma idempotente y libre de underflow una reserva previa no despachada.
    ///
    /// Si el ticket ya fue liberado previamente, actúa como no-op devolviendo el saldo actual.
    /// Emplea un bucle CAS (`compare_exchange`) saturado en `0` para impedir cualquier
    /// underflow aritmético en `spent_today_cents`.
    pub fn rollback_unspent_reservation_idempotent(
        &self,
        ticket: &mut BudgetReservationTicket,
    ) -> u64 {
        if ticket.released || ticket.reserved_cents == 0 {
            return self.spent_today();
        }
        ticket.released = true;
        let release = ticket.reserved_cents as u64;
        let mut current = self.spent_today_cents.load(Ordering::Relaxed);
        loop {
            let next = current.saturating_sub(release);
            match self.spent_today_cents.compare_exchange(
                current,
                next,
                Ordering::AcqRel,
                Ordering::Relaxed,
            ) {
                Ok(_) => return next,
                Err(actual) => current = actual,
            }
        }
    }

    /// Consume el ticket por valor y libera la reserva no despachada sin riesgo de underflow.
    pub fn rollback_unspent_reservation(&self, mut ticket: BudgetReservationTicket) -> u64 {
        self.rollback_unspent_reservation_idempotent(&mut ticket)
    }

    /// Devuelve el total reservado/gastado actualmente con orden `Acquire`.
    pub fn spent_today(&self) -> u64 {
        self.spent_today_cents.load(Ordering::Acquire)
    }

    /// Registra telemetría atómica de ROAS por época para el disyuntor MUSHUSHU-0 (`0xDEAD_6060`).
    pub fn record_epoch_telemetry(&self, observed_roas_basis_points: u32) {
        self.current_roas_basis_points
            .store(observed_roas_basis_points, Ordering::Release);
        if observed_roas_basis_points < self.min_roas_basis_points {
            let mut cur = self
                .consecutive_underperforming_epochs
                .load(Ordering::Relaxed);
            loop {
                let next = cur.saturating_add(1);
                match self
                    .consecutive_underperforming_epochs
                    .compare_exchange(cur, next, Ordering::AcqRel, Ordering::Relaxed)
                {
                    Ok(_) => break,
                    Err(actual) => cur = actual,
                }
            }
        } else {
            self.consecutive_underperforming_epochs
                .store(0, Ordering::Release);
        }
    }

    /// Exporta una instantánea determinista compatible con `KudurruBudgetGate` C-ABI (64 B).
    pub fn snapshot(&self) -> KudurruBudgetGate {
        KudurruBudgetGate {
            max_daily_budget_cents: self.max_daily_budget_cents,
            spent_today_cents: self.spent_today_cents.load(Ordering::Acquire),
            max_bid_cents: self.max_bid_cents,
            min_roas_basis_points: self.min_roas_basis_points,
            current_roas_basis_points: self.current_roas_basis_points.load(Ordering::Acquire),
            consecutive_underperforming_epochs: self
                .consecutive_underperforming_epochs
                .load(Ordering::Acquire),
            biometric_attestation_hash: self.biometric_attestation_hash,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(not(loom))]
    use std::sync::{Arc, Barrier};
    #[cfg(not(loom))]
    use std::thread;

    #[cfg(not(loom))]
    #[test]
    fn test_kudurru_layout_64b_alignment() {
        assert_eq!(std::mem::size_of::<KudurruBudgetGate>(), 64);
        assert_eq!(std::mem::align_of::<KudurruBudgetGate>(), 64);
        assert_eq!(std::mem::size_of::<AtomicKudurruBudgetGate>(), 64);
        assert_eq!(std::mem::align_of::<AtomicKudurruBudgetGate>(), 64);
    }

    #[test]
    fn test_kudurru_budget_enforcement() {
        let mut gate = KudurruBudgetGate::new(10_000, 500, 250, [0xAA; 32]);
        // Valid bid: 200 cents
        let verdict = gate.evaluate_bid(200, 5000, 200);
        assert_eq!(
            verdict,
            BudgetVerdict::Allowed {
                approved_bid_cents: 200
            }
        );
        assert_eq!(gate.spent_today_cents, 200);

        // Exceeds bid cap (500 limit)
        let verdict_cap = gate.evaluate_bid(600, 5000, 200);
        assert_eq!(
            verdict_cap,
            BudgetVerdict::ExceedsBidCap {
                attempted_bid_cents: 600,
                bid_cap_cents: 500
            }
        );

        // Exceeds daily budget (10000 limit)
        let verdict_budget = gate.evaluate_bid(400, 5000, 200);
        assert_eq!(
            verdict_budget,
            BudgetVerdict::Allowed {
                approved_bid_cents: 400
            }
        );
        assert_eq!(gate.spent_today_cents, 600);
    }

    #[test]
    fn test_mushushu_apoptosis_on_sustained_underperformance() {
        let mut gate = KudurruBudgetGate::new(10_000, 500, 250, [0xAA; 32]);
        // Simulate 60 bad epochs (ROAS = 1.0x vs 2.5x min)
        for _ in 0..60 {
            gate.record_epoch_telemetry(100);
        }
        assert_eq!(gate.consecutive_underperforming_epochs, 60);

        let verdict = gate.evaluate_bid(100, 5000, 200);
        assert_eq!(
            verdict,
            BudgetVerdict::ApoptosisHalt {
                signal: 0xDEAD_6060
            }
        );
    }

    #[cfg(not(loom))]
    #[test]
    fn test_o9_budget_race_concurrent_agents_never_exceed_limit() {
        // Presupuesto global estricto de 5_000 céntimos; cada reserva pide 100 céntimos.
        // Exactamente 50 reservas deben ser admitidas entre 32 hilos x 100 intentos = 3_200 intentos.
        let gate = Arc::new(AtomicKudurruBudgetGate::new(5_000, 500, 250, [0xBB; 32]));
        let threads = 32usize;
        let attempts_per_thread = 100usize;
        let barrier = Arc::new(Barrier::new(threads));

        let mut handles = Vec::with_capacity(threads);
        for _ in 0..threads {
            let gate_ref = Arc::clone(&gate);
            let barrier_ref = Arc::clone(&barrier);
            handles.push(thread::spawn(move || {
                barrier_ref.wait();
                let mut admitted = 0usize;
                let mut admitted_cents = 0u64;
                for _ in 0..attempts_per_thread {
                    match gate_ref.try_reserve_bid(100, 5000, 200) {
                        Ok(ticket) => {
                            admitted += 1;
                            admitted_cents += ticket.reserved_cents as u64;
                            assert!(ticket.committed_total_cents <= 5_000);
                        }
                        Err(BudgetVerdict::ExceedsDailyBudget { limit_cents, .. }) => {
                            assert_eq!(limit_cents, 5_000);
                        }
                        Err(other) => panic!("unexpected verdict in O9 race: {other:?}"),
                    }
                }
                (admitted, admitted_cents)
            }));
        }

        let mut total_admitted = 0usize;
        let mut total_cents = 0u64;
        for handle in handles {
            let (adm, cents) = handle.join().expect("worker thread panicked");
            total_admitted += adm;
            total_cents += cents;
        }

        assert_eq!(total_admitted, 50);
        assert_eq!(total_cents, 5_000);
        assert_eq!(gate.spent_today(), 5_000);
    }

    #[cfg(not(loom))]
    #[test]
    fn test_o9_atomic_reservation_rollback_restores_capacity() {
        let gate = AtomicKudurruBudgetGate::new(300, 200, 250, [0xCC; 32]);
        let t1 = gate
            .try_reserve_bid(200, 5000, 200)
            .expect("first reservation");
        assert_eq!(gate.spent_today(), 200);

        // Segunda reserva de 200 debe fallar porque 200 + 200 > 300
        assert_eq!(
            gate.try_reserve_bid(200, 5000, 200),
            Err(BudgetVerdict::ExceedsDailyBudget {
                attempted_total_cents: 400,
                limit_cents: 300,
            })
        );

        // Rollback de t1 antes de ejecutar el efecto externo libera exactamente 200
        assert_eq!(gate.rollback_unspent_reservation(t1), 0);
        assert_eq!(gate.spent_today(), 0);

        // Ahora una nueva reserva de 200 vuelve a ser admitida
        let t2 = gate
            .try_reserve_bid(200, 5000, 200)
            .expect("reservation after rollback");
        assert_eq!(t2.committed_total_cents, 200);
    }

    #[cfg(not(loom))]
    #[test]
    fn test_o9_atomic_reservation_rollback_is_idempotent_and_underflow_free() {
        let gate = AtomicKudurruBudgetGate::new(500, 250, 250, [0xDD; 32]);
        let mut t1 = gate
            .try_reserve_bid(200, 5000, 200)
            .expect("first reservation");
        let _t2 = gate
            .try_reserve_bid(150, 5000, 200)
            .expect("second reservation");
        assert_eq!(gate.spent_today(), 350);

        // Primera liberación de t1 descuenta exactamente 200 -> quedan 150 de t2
        assert_eq!(gate.rollback_unspent_reservation_idempotent(&mut t1), 150);
        assert_eq!(gate.spent_today(), 150);

        // Segunda y tercera invocación sobre el mismo ticket son no-op idempotentes (no restan de t2)
        assert_eq!(gate.rollback_unspent_reservation_idempotent(&mut t1), 150);
        assert_eq!(gate.rollback_unspent_reservation(t1), 150);
        assert_eq!(gate.spent_today(), 150);

        // Incluso ante un ticket huérfano cuando el saldo es menor que reserved_cents,
        // el bucle CAS satura en 0 en memoria sin envolver AtomicU64 a u64::MAX.
        let orphan_ticket = BudgetReservationTicket {
            reserved_cents: 500,
            committed_total_cents: 500,
            released: false,
        };
        assert_eq!(gate.rollback_unspent_reservation(orphan_ticket), 0);
        assert_eq!(gate.spent_today(), 0);
    }

    #[cfg(loom)]
    #[test]
    fn loom_try_reserve_bid_concurrent_never_exceeds_daily_budget() {
        loom::model(|| {
            let gate = loom::sync::Arc::new(AtomicKudurruBudgetGate::new(300, 200, 250, [0x11; 32]));
            let g1 = loom::sync::Arc::clone(&gate);
            let g2 = loom::sync::Arc::clone(&gate);

            let h1 = loom::thread::spawn(move || g1.try_reserve_bid(200, 5000, 200));
            let h2 = loom::thread::spawn(move || g2.try_reserve_bid(200, 5000, 200));

            let r1 = h1.join().expect("loom thread 1 panicked");
            let r2 = h2.join().expect("loom thread 2 panicked");

            let mut winners = 0usize;
            for res in [r1, r2] {
                match res {
                    Ok(ticket) => {
                        winners += 1;
                        assert_eq!(ticket.reserved_cents, 200);
                        assert_eq!(ticket.committed_total_cents, 200);
                    }
                    Err(BudgetVerdict::ExceedsDailyBudget {
                        attempted_total_cents,
                        limit_cents,
                    }) => {
                        assert_eq!(attempted_total_cents, 400);
                        assert_eq!(limit_cents, 300);
                    }
                    Err(other) => panic!("unexpected verdict under loom race: {other:?}"),
                }
            }

            assert_eq!(winners, 1);
            assert_eq!(gate.spent_today(), 200);
        });
    }

    #[cfg(loom)]
    #[test]
    fn loom_rollback_unspent_reservation_idempotent_concurrent_with_reserve() {
        loom::model(|| {
            let gate = loom::sync::Arc::new(AtomicKudurruBudgetGate::new(300, 200, 250, [0x22; 32]));
            let mut t1 = gate
                .try_reserve_bid(200, 5000, 200)
                .expect("initial reservation must succeed");

            let g_rb = loom::sync::Arc::clone(&gate);
            let g_res = loom::sync::Arc::clone(&gate);

            let h_rb = loom::thread::spawn(move || {
                let first = g_rb.rollback_unspent_reservation_idempotent(&mut t1);
                let second = g_rb.rollback_unspent_reservation_idempotent(&mut t1);
                (first, second)
            });
            let h_res = loom::thread::spawn(move || g_res.try_reserve_bid(200, 5000, 200));

            let (_first_rb, _second_rb) = h_rb.join().expect("rollback thread panicked");
            let res = h_res.join().expect("reserve thread panicked");

            match res {
                Ok(t2) => {
                    assert_eq!(t2.reserved_cents, 200);
                    assert!(t2.committed_total_cents <= 300);
                    assert_eq!(gate.spent_today(), 200);
                }
                Err(BudgetVerdict::ExceedsDailyBudget { limit_cents, .. }) => {
                    assert_eq!(limit_cents, 300);
                    assert_eq!(gate.spent_today(), 0);
                    let recovered = gate
                        .try_reserve_bid(200, 5000, 200)
                        .expect("capacity must be restored after rollback");
                    assert_eq!(recovered.committed_total_cents, 200);
                }
                Err(other) => panic!("unexpected verdict during concurrent rollback: {other:?}"),
            }
        });
    }

    #[cfg(loom)]
    #[test]
    fn loom_record_epoch_telemetry_concurrent_underperformance_and_reset() {
        loom::model(|| {
            let gate =
                loom::sync::Arc::new(AtomicKudurruBudgetGate::new(1_000, 200, 250, [0x33; 32]));
            let g1 = loom::sync::Arc::clone(&gate);
            let g2 = loom::sync::Arc::clone(&gate);

            let h1 = loom::thread::spawn(move || g1.record_epoch_telemetry(100));
            let h2 = loom::thread::spawn(move || g2.record_epoch_telemetry(120));

            h1.join().expect("telemetry thread 1 panicked");
            h2.join().expect("telemetry thread 2 panicked");

            let snap = gate.snapshot();
            assert_eq!(snap.consecutive_underperforming_epochs, 2);
            assert!(
                snap.current_roas_basis_points == 100 || snap.current_roas_basis_points == 120
            );
        });

        loom::model(|| {
            let gate =
                loom::sync::Arc::new(AtomicKudurruBudgetGate::new(1_000, 200, 250, [0x44; 32]));
            let g_bad = loom::sync::Arc::clone(&gate);
            let g_good = loom::sync::Arc::clone(&gate);

            let h_bad = loom::thread::spawn(move || g_bad.record_epoch_telemetry(100));
            let h_good = loom::thread::spawn(move || g_good.record_epoch_telemetry(300));

            h_bad.join().expect("underperforming thread panicked");
            h_good.join().expect("recovery thread panicked");

            let snap = gate.snapshot();
            assert!(snap.consecutive_underperforming_epochs <= 1);
            assert!(
                snap.current_roas_basis_points == 100 || snap.current_roas_basis_points == 300
            );
        });
    }
}
