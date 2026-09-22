use std::collections::HashMap;
use crate::ir::{Reg, IrOp, Terminator, BasicBlock};

pub struct Arm64Backend {
    asm: String,
    stack_offsets: HashMap<usize, usize>,
    next_offset: usize,
}

impl Default for Arm64Backend {
    fn default() -> Self {
        Self::new()
    }
}

impl Arm64Backend {
    pub fn new() -> Self {
        Self { 
            asm: String::new(), 
            stack_offsets: HashMap::new(), 
            next_offset: 16
        }
    }

    fn get_offset(&mut self, reg: Reg) -> usize {
        if let Some(&offset) = self.stack_offsets.get(&reg.0) {
            offset
        } else {
            let offset = self.next_offset;
            self.stack_offsets.insert(reg.0, offset);
            self.next_offset += 8; 
            offset
        }
    }

    pub fn compile(&mut self, blocks: &[BasicBlock]) -> String {
        self.asm.push_str("
.align 4
.text
.global _start

// SOBERANÍA: Implementación nativa de sys_alloc (Bump Allocator ARM64)
sys_alloc:
    adrp x1, heap_ptr@PAGE
    add x1, x1, heap_ptr@PAGEOFF
    ldr x2, [x1]
    mov x0, x2
    add x2, x2, x0
    str x2, [x1]
    ret

// SOBERANÍA: Implementación nativa de sys_free (No-op ARM64)
sys_free:
    ret

_start:
    // Setup AAPCS (ARM64 ABI)
    adrp x0, stack_top@PAGE
    add x0, x0, stack_top@PAGEOFF
    mov sp, x0
    
    // Setup del heap a partir del megabyte 2 (fuera del kernel base)
    mov x0, 0x200000
    adrp x1, heap_ptr@PAGE
    add x1, x1, heap_ptr@PAGEOFF
    str x0, [x1]
    
    // --- PRÓLOGO LÓGICO DEL KERNEL ---
    stp x29, x30, [sp, -16]!
    mov x29, sp
    sub sp, sp, #256
\n");

        for blk in blocks {
            self.asm.push_str(&format!(".L{}:\n", blk.id.0));
            for op in &blk.instructions {
                match op {
                    IrOp::ConstInt { dest, val } => {
                        let off = self.get_offset(*dest);
                        self.asm.push_str(&format!("    ldr x0, ={}  // Reg({})\n", val, dest.0));
                        self.asm.push_str(&format!("    str x0, [x29, -{}]\n", off));
                    }
                    IrOp::ConstBool { dest, val } => {
                        let off = self.get_offset(*dest);
                        let v = if *val { 1 } else { 0 };
                        self.asm.push_str(&format!("    mov x0, {}  // Reg({})\n", v, dest.0));
                        self.asm.push_str(&format!("    str x0, [x29, -{}]\n", off));
                    }
                    IrOp::Alloc { dest, size } => {
                        self.asm.push_str(&format!("    mov x0, {}  // call arg1: size\n", size));
                        self.asm.push_str("    bl sys_alloc\n");
                        let off = self.get_offset(*dest);
                        self.asm.push_str(&format!("    str x0, [x29, -{}]  // ptr -> Reg({})\n", off, dest.0));
                    }
                    IrOp::Store { ptr, val } | IrOp::VolatileStore { ptr, val } => {
                        let ptr_off = self.get_offset(*ptr);
                        let val_off = self.get_offset(*val);
                        self.asm.push_str(&format!("    ldr x0, [x29, -{}]  // load ptr\n", ptr_off));
                        self.asm.push_str(&format!("    ldr x1, [x29, -{}]  // load val\n", val_off));
                        self.asm.push_str("    str x1, [x0]\n");
                    }
                    IrOp::Load { dest, ptr } => {
                        let dest_off = self.get_offset(*dest);
                        let ptr_off = self.get_offset(*ptr);
                        self.asm.push_str(&format!("    ldr x0, [x29, -{}]  // load ptr\n", ptr_off));
                        self.asm.push_str("    ldr x1, [x0]  // deref\n");
                        self.asm.push_str(&format!("    str x1, [x29, -{}]\n", dest_off));
                    }
                    IrOp::FieldPtr { dest, base, offset } => {
                        let dest_off = self.get_offset(*dest);
                        let base_off = self.get_offset(*base);
                        self.asm.push_str(&format!("    ldr x0, [x29, -{}]  // base ptr\n", base_off));
                        self.asm.push_str(&format!("    add x1, x0, {}  // field offset\n", offset));
                        self.asm.push_str(&format!("    str x1, [x29, -{}]  // field ptr -> Reg({})\n", dest_off, dest.0));
                    }
                    IrOp::BorrowShared { dest, src } | IrOp::BorrowMut { dest, src } => {
                        let dest_off = self.get_offset(*dest);
                        let src_off = self.get_offset(*src);
                        self.asm.push_str(&format!("    ldr x0, [x29, -{}]  // copy ptr\n", src_off));
                        self.asm.push_str(&format!("    str x0, [x29, -{}]  // borrow -> Reg({})\n", dest_off, dest.0));
                    }
                    IrOp::EndBorrow { .. } => {
                        self.asm.push_str("    // EndBorrow (no-op en runtime)\n");
                    }
                    IrOp::Free { ptr } => {
                        let off = self.get_offset(*ptr);
                        self.asm.push_str(&format!("    ldr x0, [x29, -{}]\n", off));
                        self.asm.push_str("    bl sys_free\n");
                    }
                    IrOp::HardwareAcquire { dest, peripheral_id } => {
                        let off = self.get_offset(*dest);
                        self.asm.push_str(&format!("    mov x0, {}  // hw_acquire peripheral({})\n", peripheral_id, peripheral_id));
                        self.asm.push_str(&format!("    str x0, [x29, -{}]\n", off));
                    }
                    IrOp::HardwareTransition { reg, from_channel, to_channel } => {
                        self.asm.push_str(&format!("    // hw_transition Reg({}) ch {} -> {}\n", reg.0, from_channel, to_channel));
                    }
                    IrOp::HardwareRelease { reg } => {
                        let off = self.get_offset(*reg);
                        self.asm.push_str("    mov x0, 0\n");
                        self.asm.push_str(&format!("    str x0, [x29, -{}]  // hw_release Reg({})\n", off, reg.0));
                    }
                }
            }

            match &blk.terminator {
                Terminator::Jump(target) => {
                    self.asm.push_str(&format!("    b .L{}\n\n", target.0));
                }
                Terminator::BranchIf { cond, then_blk, else_blk } => {
                    let off = self.get_offset(*cond);
                    self.asm.push_str(&format!("    ldr x0, [x29, -{}]\n", off));
                    self.asm.push_str("    cbz x0, 1f\n");
                    self.asm.push_str(&format!("    b .L{}\n", then_blk.0));
                    self.asm.push_str("1:\n");
                    self.asm.push_str(&format!("    b .L{}\n\n", else_blk.0));
                }
                Terminator::Return => {
                    self.asm.push_str("    mov sp, x29\n");
                    self.asm.push_str("    ldp x29, x30, [sp], 16\n");
                    self.asm.push_str(".hang:\n");
                    self.asm.push_str("    wfi\n");
                    self.asm.push_str("    b .hang\n\n");
                }
                Terminator::None => panic!("Bloque sin terminador"),
            }
        }
        
        self.asm.push_str("
.bss
.align 4
stack_bottom:
    .space 16384
stack_top:

heap_ptr:
    .space 8
\n");

        self.asm.clone()
    }
}
