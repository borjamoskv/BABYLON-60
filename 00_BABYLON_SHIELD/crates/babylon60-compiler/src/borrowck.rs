use crate::ir::{Reg, IrOp};
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BorrowState {
    Unborrowed,
    Shared(Vec<Reg>),
    Mut(Reg),
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
}

pub struct BorrowChecker {
    pub states: HashMap<Reg, BorrowState>,
    pub reference_map: HashMap<Reg, Reg>,
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
            IrOp::Load { ptr, .. } => {
                let owner = *self.reference_map.get(ptr).unwrap_or(ptr);
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
            IrOp::Store { ptr, .. } | IrOp::VolatileStore { ptr, .. } => {
                let owner = *self.reference_map.get(ptr).unwrap_or(ptr);
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
            _ => Ok(())
        }
    }
}
