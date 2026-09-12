#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Reg(pub usize);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct BlockId(pub usize);

#[derive(Debug, Clone)]
pub enum IrOp {
    ConstInt { dest: Reg, val: i64 },
    ConstBool { dest: Reg, val: bool },
    Alloc { dest: Reg, size: usize },
    Free { ptr: Reg },
    Store { ptr: Reg, val: Reg },
    VolatileStore { ptr: Reg, val: Reg },
    Load { dest: Reg, ptr: Reg }, 
    FieldPtr { dest: Reg, base: Reg, offset: usize },
    // --- LIFETIMES & BORROWS ---
    BorrowShared { dest: Reg, src: Reg },
    BorrowMut { dest: Reg, src: Reg },
    EndBorrow { ptr: Reg },
}

#[derive(Debug, Clone)]
pub enum Terminator {
    Jump(BlockId),
    BranchIf { cond: Reg, then_blk: BlockId, else_blk: BlockId },
    Return,
    None,
}

#[derive(Debug, Clone)]
pub struct BasicBlock {
    pub id: BlockId,
    pub instructions: Vec<IrOp>,
    pub terminator: Terminator,
}
