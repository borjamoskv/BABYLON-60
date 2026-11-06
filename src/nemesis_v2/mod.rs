//! # NEMESIS v2: Scheduler de Simulación de Eventos Discretos (DES)
//!
//! Hypervisor de orquestación temporal determinista para pruebas de robustez adversarial.

#![allow(missing_docs)]

pub mod faults;
pub mod oracles;
pub mod replay;

use std::collections::{BTreeMap, BinaryHeap};
use core::cmp::Ordering;

use crate::larsa_pure::{
    step, DeclarativeEffect, Epoch, LarsaPureState, LogicalEvent, NodeId,
};
use self::faults::{AdversarialFault, FaultPlan, PartitionMatrix};
use self::oracles::{InvariantViolation, NemesisOracles};

/// Evento programado en la cola con timestamp lógico virtual.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ScheduledEvent {
    pub tick: u64,
    pub event_id: u64,
    pub recipient: Option<NodeId>,
    pub event: LogicalEvent,
}

impl Ord for ScheduledEvent {
    fn cmp(&self, other: &Self) -> Ordering {
        // Invertido para BinaryHeap min-heap: menor tick tiene mayor prioridad
        other
            .tick
            .cmp(&self.tick)
            .then_with(|| other.event_id.cmp(&self.event_id))
    }
}

impl PartialOrd for ScheduledEvent {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// Scheduler determinista de eventos discretos de NEMESIS v2.
pub struct NemesisScheduler {
    pub logical_clock: u64,
    next_event_id: u64,
    queue: BinaryHeap<ScheduledEvent>,
    pub state: LarsaPureState,
    pub network_topology: PartitionMatrix,
    pub fault_plan: FaultPlan,
    pub committed_history: BTreeMap<Epoch, [u8; 32]>,
    pub executed_trace: Vec<(u64, LogicalEvent)>,
    pub emitted_effects: Vec<(u64, DeclarativeEffect)>,
}

impl NemesisScheduler {
    /// Inicializa un scheduler con estado inicial, topología y plan de fallos.
    pub fn new(
        initial_state: LarsaPureState,
        topology: PartitionMatrix,
        fault_plan: FaultPlan,
    ) -> Self {
        Self {
            logical_clock: 0,
            next_event_id: 0,
            queue: BinaryHeap::new(),
            state: initial_state,
            network_topology: topology,
            fault_plan,
            committed_history: BTreeMap::new(),
            executed_trace: Vec::new(),
            emitted_effects: Vec::new(),
        }
    }

    /// Programa un evento en la cola para ejecutarse en `tick`.
    pub fn schedule_event(&mut self, tick: u64, recipient: Option<NodeId>, event: LogicalEvent) {
        let event_id = self.next_event_id;
        self.next_event_id = self.next_event_id.saturating_add(1);
        self.queue.push(ScheduledEvent {
            tick,
            event_id,
            recipient,
            event,
        });
    }

    /// Ejecuta el siguiente evento programado y aplica los fallos correspondientes al tick.
    pub fn step_next(&mut self) -> Result<Option<LogicalEvent>, InvariantViolation> {
        let scheduled = match self.queue.pop() {
            Some(ev) => ev,
            None => return Ok(None),
        };

        // Avanzar el reloj lógico monótonamente
        if scheduled.tick > self.logical_clock {
            self.logical_clock = scheduled.tick;
        }

        // Aplicar fallos programados para el tick actual
        for fault in &self.fault_plan.faults {
            match fault {
                AdversarialFault::InjectPartition { at_tick, matrix } => {
                    if *at_tick == self.logical_clock {
                        self.network_topology = matrix.clone();
                    }
                }
                AdversarialFault::CrashNode { at_tick, node } => {
                    if *at_tick == self.logical_clock {
                        let (s, _) = step(self.state.clone(), LogicalEvent::NodeOffline { node: *node });
                        self.state = s;
                    }
                }
                AdversarialFault::RecoverNode { at_tick, node } => {
                    if *at_tick == self.logical_clock {
                        let (s, _) = step(self.state.clone(), LogicalEvent::NodeRecovered { node: *node });
                        self.state = s;
                    }
                }
                AdversarialFault::DelayDelivery { .. } => {}
            }
        }

        // Verificar partición si el evento tiene destinatario y emisor
        if let LogicalEvent::VoteReceived { voter, .. } = &scheduled.event {
            if let Some(target) = scheduled.recipient {
                if !self.network_topology.can_communicate(*voter, target) {
                    // Mensaje descartado o bloqueado por partición de red
                    return Ok(Some(scheduled.event));
                }
            }
        }

        // Ejecutar transición pura
        let (next_state, effects) = step(self.state.clone(), scheduled.event.clone());
        self.state = next_state;

        // Registrar efectos y comprobar commits
        for effect in &effects {
            self.emitted_effects.push((self.logical_clock, effect.clone()));
            if let DeclarativeEffect::NotifyCommit { epoch, trace_hash, .. } = effect {
                self.committed_history.insert(*epoch, *trace_hash);
            }
        }

        // Registrar en traza de auditoría
        self.executed_trace.push((self.logical_clock, scheduled.event.clone()));

        // Evaluar oráculos de invariantes en silicio
        NemesisOracles::verify_all(&self.state, &self.committed_history)?;

        Ok(Some(scheduled.event))
    }

    /// Ejecuta todos los eventos programados hasta agotar la cola o alcanzar una cuota máxima.
    pub fn run_until_quiescence(&mut self, max_ticks: u64) -> Result<u64, InvariantViolation> {
        let mut executed_count = 0;
        while executed_count < max_ticks && !self.queue.is_empty() {
            if self.step_next()?.is_some() {
                executed_count += 1;
            }
        }
        Ok(executed_count)
    }
}
