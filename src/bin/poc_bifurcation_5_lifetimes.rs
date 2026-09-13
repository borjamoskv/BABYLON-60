// ============================================================================
// PoC: BIFURCATION 5 - EL TEOREMA DE LA VIDA (LIFETIMES & BORROW CHECKER)
// BABYLON-60 / C5-REAL
// ============================================================================
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Reg(pub usize);

#[derive(Debug, Clone)]
pub enum IrOp {
    Alloc { dest: Reg },
    BorrowShared { dest: Reg, src: Reg },
    BorrowMut { dest: Reg, src: Reg },
    EndBorrow { ptr: Reg }, // Simulador de final de bloque de vida léxica
    Read { src: Reg },
    Write { dest: Reg },
    Free { ptr: Reg },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BorrowState {
    Unborrowed,
    Shared(Vec<Reg>),
    Mut(Reg),
}

pub struct BorrowChecker {
    pub states: HashMap<Reg, BorrowState>,
    pub reference_map: HashMap<Reg, Reg>,
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
            IrOp::Alloc { dest } => {
                self.states.insert(*dest, BorrowState::Unborrowed);
                Ok(())
            }
            IrOp::BorrowShared { dest, src } => {
                let owner = *self.reference_map.get(src).unwrap_or(src);
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get_mut(&owner).unwrap() {
                    BorrowState::Unborrowed => {
                        *self.states.get_mut(&owner).unwrap() = BorrowState::Shared(vec![*dest]);
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
                match self.states.get(&owner).unwrap() {
                    BorrowState::Unborrowed => {
                        *self.states.get_mut(&owner).unwrap() = BorrowState::Mut(*dest);
                        self.reference_map.insert(*dest, owner);
                        Ok(())
                    }
                    BorrowState::Shared(_) => Err(BorrowError::CannotBorrowMutablyWhileShared(owner)),
                    BorrowState::Mut(_) => Err(BorrowError::CannotBorrowMutablyWhileMutablyBorrowed(owner)),
                }
            }
            IrOp::Read { src } => {
                let owner = *self.reference_map.get(src).unwrap_or(src);
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get(&owner).unwrap() {
                    BorrowState::Unborrowed | BorrowState::Shared(_) => Ok(()),
                    BorrowState::Mut(mut_ref) => {
                        if *mut_ref == *src { Ok(()) } else { Err(BorrowError::CannotReadMutablyBorrowed(owner)) }
                    }
                }
            }
            IrOp::Write { dest } => {
                let owner = *self.reference_map.get(dest).unwrap_or(dest);
                if !self.states.contains_key(&owner) {
                    return Err(BorrowError::UseAfterFree(owner));
                }
                match self.states.get(&owner).unwrap() {
                    BorrowState::Unborrowed => Ok(()),
                    BorrowState::Shared(_) => Err(BorrowError::CannotWriteBorrowed(owner)),
                    BorrowState::Mut(mut_ref) => {
                        if *mut_ref == *dest { Ok(()) } else { Err(BorrowError::CannotWriteBorrowed(owner)) }
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
                let state = self.states.get(&owner).unwrap().clone();
                if state != BorrowState::Unborrowed {
                    return Err(BorrowError::DanglingPointerOnFree(owner, state));
                }
                self.states.remove(&owner);
                Ok(())
            }
        }
    }
}

fn test_valid_borrows() {
    let ops = vec![
        IrOp::Alloc { dest: Reg(0) },
        IrOp::BorrowShared { dest: Reg(1), src: Reg(0) },
        IrOp::Read { src: Reg(1) },
        IrOp::EndBorrow { ptr: Reg(1) },
        IrOp::BorrowMut { dest: Reg(2), src: Reg(0) },
        IrOp::Write { dest: Reg(2) },
        IrOp::EndBorrow { ptr: Reg(2) },
        IrOp::Free { ptr: Reg(0) },
    ];
    let mut checker = BorrowChecker::new();
    assert_eq!(checker.check(&ops), Ok(()));
    println!("[OK] Valid Borrows Passed.");
}

fn test_dangling_pointer() {
    let ops = vec![
        IrOp::Alloc { dest: Reg(0) },
        IrOp::BorrowShared { dest: Reg(1), src: Reg(0) },
        IrOp::Free { ptr: Reg(0) }, // Error! Still borrowed by Reg(1)
    ];
    let mut checker = BorrowChecker::new();
    assert_eq!(checker.check(&ops), Err(BorrowError::DanglingPointerOnFree(Reg(0), BorrowState::Shared(vec![Reg(1)]))));
    println!("[OK] Dangling Pointer Prevention Passed.");
}

fn test_aliasing_violation() {
    let ops = vec![
        IrOp::Alloc { dest: Reg(0) },
        IrOp::BorrowMut { dest: Reg(1), src: Reg(0) },
        IrOp::BorrowShared { dest: Reg(2), src: Reg(0) }, // Error! Already borrowed mutably
    ];
    let mut checker = BorrowChecker::new();
    assert_eq!(checker.check(&ops), Err(BorrowError::CannotBorrowSharedWhileMutablyBorrowed(Reg(0))));
    println!("[OK] Aliasing Violation Prevention Passed.");
}

fn stress_test() {
    println!("\n=== STRESS TEST (1000 iteraciones empíricas) ===");
    let ops = vec![
        IrOp::Alloc { dest: Reg(0) },
        IrOp::BorrowMut { dest: Reg(1), src: Reg(0) },
        IrOp::Write { dest: Reg(1) },
        IrOp::EndBorrow { ptr: Reg(1) },
        IrOp::BorrowShared { dest: Reg(2), src: Reg(0) },
        IrOp::Read { src: Reg(2) },
        IrOp::EndBorrow { ptr: Reg(2) },
        IrOp::Free { ptr: Reg(0) },
    ];
    
    let mut success = 0;
    for _ in 0..1000 {
        let mut checker = BorrowChecker::new();
        if checker.check(&ops).is_ok() {
            success += 1;
        }
    }
    println!("Falsación superada: {}/1000 análisis de ciclo de vida completados sin anomalías.", success);
}

fn main() {
    println!("--- C5-REAL: INYECTOR DE LIFETIMES (BORROW CHECKER PoC) ---");
    test_valid_borrows();
    test_dangling_pointer();
    test_aliasing_violation();
    stress_test();
}
