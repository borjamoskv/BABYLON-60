use crate::ir::{IrOp, Reg};
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BorrowState {
    Unborrowed,
    Shared(Vec<Reg>),
    Mut(Reg),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HardwareSessionState {
    Active { peripheral_id: usize, channel: usize },
    Released,
}

#[derive(Debug, PartialEq, Eq)]
pub enum BorrowError {
    CannotBorrowMutablyWhileShared(Reg),
    CannotBorrowMutablyWhileMutablyBorrowed(Reg),
    CannotBorrowSharedWhileMutablyBorrowed(Reg),
    CannotReadMutablyBorrowed(Reg),
    CannotWriteBorrowed(Reg),
    UseAfterFree(Reg),
    DanglingPointerOnFree(Reg, BorrowState),
    HardwareIllegalTransition(Reg),
    HardwareUseAfterRelease(Reg),
    HardwareDoubleAcquire(Reg),
}

pub struct BorrowChecker {
    pub states: HashMap<Reg, BorrowState>,
    pub reference_map: HashMap<Reg, Reg>,
    pub hardware_sessions: HashMap<Reg, HardwareSessionState>,
}

impl Default for BorrowChecker {
    fn default() -> Self {
        Self::new()
    }
}

impl BorrowChecker {
    pub fn new() -> Self {
        Self {
            states: HashMap::new(),
            reference_map: HashMap::new(),
            hardware_sessions: HashMap::new(),
        }
    }

    pub fn check(&mut self, ops: &[IrOp]) -> Result<(), BorrowError> {
        for op in ops {
            self.check_op(op)?;
        }
        Ok(())
    }

    fn check_op(&mut self, op: &IrOp) -> Result<(), BorrowError> {
        match op {
            IrOp::Alloc { dest, .. } => {
                self.states.insert(*dest, BorrowState::Unborrowed);
                Ok(())
            }
            IrOp::BorrowShared { dest, src } => {
                let owner = *self.reference_map.get(src).unwrap_or(src);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get_mut(&owner).expect("BFT Fallback") {
                    BorrowState::Unborrowed => {
                        *self.states.get_mut(&owner).expect("BFT Fallback") = BorrowState::Shared(vec![*dest]);
                        self.reference_map.insert(*dest, owner);
                        Ok(())
                    }
                    BorrowState::Shared(refs) => {
                        refs.push(*dest);
                        self.reference_map.insert(*dest, owner);
                        Ok(())
                    }
                    BorrowState::Mut(_) => {
                        Err(BorrowError::CannotBorrowSharedWhileMutablyBorrowed(owner))
                    }
                }
            }
            IrOp::BorrowMut { dest, src } => {
                let owner = *self.reference_map.get(src).unwrap_or(src);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get(&owner).expect("BFT Fallback") {
                    BorrowState::Unborrowed => {
                        *self.states.get_mut(&owner).expect("BFT Fallback") = BorrowState::Mut(*dest);
                        self.reference_map.insert(*dest, owner);
                        Ok(())
                    }
                    BorrowState::Shared(_) => Err(BorrowError::CannotBorrowMutablyWhileShared(owner)),
                    BorrowState::Mut(_) => Err(BorrowError::CannotBorrowMutablyWhileMutablyBorrowed(owner)),
                }
            }
            IrOp::Load { dest, ptr } => {
                let owner = *self.reference_map.get(ptr).unwrap_or(ptr);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(dest) {
                    return Err(BorrowError::HardwareUseAfterRelease(*dest));
                }
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get(&owner).expect("BFT Fallback") {
                    BorrowState::Unborrowed | BorrowState::Shared(_) => Ok(()),
                    BorrowState::Mut(mut_ref) => {
                        if *mut_ref == *ptr { Ok(()) } else { Err(BorrowError::CannotReadMutablyBorrowed(owner)) }
                    }
                }
            }
            IrOp::Store { ptr, val } | IrOp::VolatileStore { ptr, val } => {
                let owner = *self.reference_map.get(ptr).unwrap_or(ptr);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                let val_owner = *self.reference_map.get(val).unwrap_or(val);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&val_owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(val_owner));
                }
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get(&owner).expect("BFT Fallback") {
                    BorrowState::Unborrowed => Ok(()),
                    BorrowState::Shared(_) => Err(BorrowError::CannotWriteBorrowed(owner)),
                    BorrowState::Mut(mut_ref) => {
                        if *mut_ref == *ptr { Ok(()) } else { Err(BorrowError::CannotWriteBorrowed(owner)) }
                    }
                }
            }
            IrOp::FieldPtr { dest: _, base, .. } => {
                let owner = *self.reference_map.get(base).unwrap_or(base);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                Ok(())
            }
            IrOp::EndBorrow { ptr } => {
                if let Some(&owner) = self.reference_map.get(ptr) {
                    if let Some(state) = self.states.get_mut(&owner) {
                        match state {
                            BorrowState::Shared(refs) => {
                                refs.retain(|&r| r != *ptr);
                                if refs.is_empty() { *state = BorrowState::Unborrowed; }
                            }
                            BorrowState::Mut(r)
                                if *r == *ptr => { *state = BorrowState::Unborrowed; }
                            _ => {}
                        }
                    }
                    self.reference_map.remove(ptr);
                }
                Ok(())
            }
            IrOp::Free { ptr } => {
                let owner = *self.reference_map.get(ptr).unwrap_or(ptr);
                if let Some(HardwareSessionState::Released) = self.hardware_sessions.get(&owner) {
                    return Err(BorrowError::HardwareUseAfterRelease(owner));
                }
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                let state = self.states.get(&owner).expect("BFT Fallback").clone();
                if state != BorrowState::Unborrowed {
                    return Err(BorrowError::DanglingPointerOnFree(owner, state));
                }
                self.states.remove(&owner);
                Ok(())
            }
            IrOp::HardwareAcquire { dest, peripheral_id } => {
                if self.hardware_sessions.contains_key(dest) {
                    return Err(BorrowError::HardwareDoubleAcquire(*dest));
                }
                for session in self.hardware_sessions.values() {
                    if let HardwareSessionState::Active { peripheral_id: pid, .. } = session {
                        if *pid == *peripheral_id {
                            return Err(BorrowError::HardwareDoubleAcquire(*dest));
                        }
                    }
                }
                self.hardware_sessions.insert(
                    *dest,
                    HardwareSessionState::Active {
                        peripheral_id: *peripheral_id,
                        channel: *peripheral_id,
                    },
                );
                self.states.insert(*dest, BorrowState::Unborrowed);
                Ok(())
            }
            IrOp::HardwareTransition { reg, from_channel, to_channel } => {
                let owner = *self.reference_map.get(reg).unwrap_or(reg);
                match self.hardware_sessions.get_mut(&owner) {
                    Some(HardwareSessionState::Active { peripheral_id, channel }) => {
                        let matches_channel = *channel == *from_channel
                            || (*channel == *peripheral_id && *from_channel == 0)
                            || (*channel == 0 && *from_channel == *peripheral_id);
                        if !matches_channel {
                            return Err(BorrowError::HardwareIllegalTransition(owner));
                        }
                        *channel = *to_channel;
                        Ok(())
                    }
                    Some(HardwareSessionState::Released) => {
                        Err(BorrowError::HardwareIllegalTransition(owner))
                    }
                    None => {
                        Err(BorrowError::HardwareIllegalTransition(owner))
                    }
                }
            }
            IrOp::HardwareRelease { reg } => {
                let owner = *self.reference_map.get(reg).unwrap_or(reg);
                match self.hardware_sessions.get_mut(&owner) {
                    Some(state @ HardwareSessionState::Active { .. }) => {
                        *state = HardwareSessionState::Released;
                        self.states.remove(&owner);
                        Ok(())
                    }
                    Some(HardwareSessionState::Released) => {
                        Err(BorrowError::HardwareUseAfterRelease(owner))
                    }
                    None => {
                        Err(BorrowError::HardwareUseAfterRelease(owner))
                    }
                }
            }
            _ => Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ir::{IrOp, Reg};

    #[test]
    fn test_valid_hardware_acquire_and_transition() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(0), peripheral_id: 1 },
            IrOp::HardwareTransition { reg: Reg(0), from_channel: 1, to_channel: 2 },
            IrOp::HardwareTransition { reg: Reg(0), from_channel: 2, to_channel: 3 },
            IrOp::HardwareRelease { reg: Reg(0) },
        ];
        assert!(checker.check(&ops).is_ok());
        assert_eq!(
            checker.hardware_sessions.get(&Reg(0)),
            Some(&HardwareSessionState::Released)
        );
    }

    #[test]
    fn test_valid_hardware_acquire_channel_zero() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(10), peripheral_id: 0 },
            IrOp::HardwareTransition { reg: Reg(10), from_channel: 0, to_channel: 1 },
            IrOp::HardwareRelease { reg: Reg(10) },
        ];
        assert!(checker.check(&ops).is_ok());
    }

    #[test]
    fn test_detect_hardware_double_acquire_same_reg() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 1 },
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 2 },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareDoubleAcquire(Reg(1)));
    }

    #[test]
    fn test_detect_hardware_double_acquire_same_peripheral() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 42 },
            IrOp::HardwareAcquire { dest: Reg(2), peripheral_id: 42 },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareDoubleAcquire(Reg(2)));
    }

    #[test]
    fn test_detect_hardware_illegal_transition_wrong_channel() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 1 },
            IrOp::HardwareTransition { reg: Reg(1), from_channel: 99, to_channel: 2 },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareIllegalTransition(Reg(1)));
    }

    #[test]
    fn test_detect_hardware_illegal_transition_unacquired() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareTransition { reg: Reg(99), from_channel: 0, to_channel: 1 },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareIllegalTransition(Reg(99)));
    }

    #[test]
    fn test_detect_hardware_use_after_release_double_release() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 1 },
            IrOp::HardwareRelease { reg: Reg(1) },
            IrOp::HardwareRelease { reg: Reg(1) },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareUseAfterRelease(Reg(1)));
    }

    #[test]
    fn test_detect_hardware_use_after_release_unacquired_release() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareRelease { reg: Reg(77) },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareUseAfterRelease(Reg(77)));
    }

    #[test]
    fn test_detect_hardware_use_after_release_load() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 1 },
            IrOp::HardwareRelease { reg: Reg(1) },
            IrOp::Load { dest: Reg(2), ptr: Reg(1) },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareUseAfterRelease(Reg(1)));
    }

    #[test]
    fn test_detect_hardware_use_after_release_store() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::Alloc { dest: Reg(2), size: 8 },
            IrOp::HardwareAcquire { dest: Reg(1), peripheral_id: 1 },
            IrOp::HardwareRelease { reg: Reg(1) },
            IrOp::Store { ptr: Reg(1), val: Reg(2) },
        ];
        let err = checker.check(&ops).unwrap_err();
        assert_eq!(err, BorrowError::HardwareUseAfterRelease(Reg(1)));
    }

    #[test]
    fn test_standard_borrow_checker_rules() {
        let mut checker = BorrowChecker::new();
        let ops = vec![
            IrOp::Alloc { dest: Reg(1), size: 8 },
            IrOp::BorrowShared { dest: Reg(2), src: Reg(1) },
            IrOp::BorrowShared { dest: Reg(3), src: Reg(1) },
            IrOp::EndBorrow { ptr: Reg(2) },
            IrOp::EndBorrow { ptr: Reg(3) },
            IrOp::Free { ptr: Reg(1) },
        ];
        assert!(checker.check(&ops).is_ok());
    }
}
