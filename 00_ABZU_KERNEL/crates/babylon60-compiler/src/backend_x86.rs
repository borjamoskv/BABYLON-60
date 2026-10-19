use std::collections::HashMap;
use crate::ir::{Reg, IrOp, Terminator, BasicBlock};

pub struct X86Backend {
    asm: String,
    stack_offsets: HashMap<usize, usize>,
    next_offset: usize,
}

impl Default for X86Backend {
    fn default() -> Self {
        Self::new()
    }
}

impl X86Backend {
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
bits 64

; --- CABECERA MULTIBOOT2 ---
section .multiboot_header
align 8
header_start:
    dd 0xE85250D6                ; magic number
    dd 0                         ; architecture 0 (i386)
    dd header_end - header_start ; header length
    dd 0x100000000 - (0xE85250D6 + 0 + (header_end - header_start)) ; checksum
    dw 0
    dw 0
    dd 8
header_end:

; --- MEMORIA FÍSICA (BSS) ---
section .bss
align 16
stack_bottom:
    resb 16384 ; Pila del Kernel de 16 KB
stack_top:

heap_ptr:
    resq 1 ; Puntero físico al tope del montículo

; --- CÓDIGO BARE-METAL ---
section .text
global _start

; SOBERANÍA: Implementación nativa de sys_alloc (Bump Allocator)
sys_alloc:
    mov rax, qword [rel heap_ptr]
    mov rcx, rax
    add rcx, rdi
    mov qword [rel heap_ptr], rcx
    ret

; SOBERANÍA: Implementación nativa de sys_free (No-op)
sys_free:
    ret

_start:
    mov rsp, stack_top
    ; Setup del heap a partir del megabyte 2 (fuera del kernel base)
    mov rax, 0x200000
    mov qword [rel heap_ptr], rax
    
    ; --- PRÓLOGO LÓGICO DEL KERNEL ---
    push rbp
    mov rbp, rsp
    sub rsp, 256
    and rsp, -16  ; SysV ABI
\n");

        for blk in blocks {
            self.asm.push_str(&format!(".L{}:\n", blk.id.0));
            for op in &blk.instructions {
                match op {
                    IrOp::ConstInt { dest, val } => {
                        let off = self.get_offset(*dest);
                        self.asm.push_str(&format!("    mov qword [rbp - {}], {}  ; Reg({})\n", off, val, dest.0));
                    }
                    IrOp::ConstBool { dest, val } => {
                        let off = self.get_offset(*dest);
                        let v = if *val { 1 } else { 0 };
                        self.asm.push_str(&format!("    mov qword [rbp - {}], {}  ; Reg({})\n", off, v, dest.0));
                    }
                    IrOp::Alloc { dest, size } => {
                        self.asm.push_str(&format!("    mov rdi, {}  ; call arg1: size\n", size));
                        self.asm.push_str("    call sys_alloc\n");
                        let off = self.get_offset(*dest);
                        self.asm.push_str(&format!("    mov qword [rbp - {}], rax  ; ptr -> Reg({})\n", off, dest.0));
                    }
                    IrOp::Store { ptr, val } | IrOp::VolatileStore { ptr, val } => {
                        let ptr_off = self.get_offset(*ptr);
                        let val_off = self.get_offset(*val);
                        self.asm.push_str(&format!("    mov rax, qword [rbp - {}]  ; load ptr\n", ptr_off));
                        self.asm.push_str(&format!("    mov rcx, qword [rbp - {}]  ; load val\n", val_off));
                        self.asm.push_str("    mov qword [rax], rcx\n");
                    }
                    IrOp::Load { dest, ptr } => {
                        let dest_off = self.get_offset(*dest);
                        let ptr_off = self.get_offset(*ptr);
                        self.asm.push_str(&format!("    mov rax, qword [rbp - {}]  ; load ptr\n", ptr_off));
                        self.asm.push_str("    mov rcx, qword [rax]  ; deref\n");
                        self.asm.push_str(&format!("    mov qword [rbp - {}], rcx\n", dest_off));
                    }
                    IrOp::FieldPtr { dest, base, offset } => {
                        let dest_off = self.get_offset(*dest);
                        let base_off = self.get_offset(*base);
                        self.asm.push_str(&format!("    mov rax, qword [rbp - {}]  ; base ptr\n", base_off));
                        self.asm.push_str(&format!("    lea rcx, [rax + {}]  ; LEA field offset\n", offset));
                        self.asm.push_str(&format!("    mov qword [rbp - {}], rcx  ; field ptr -> Reg({})\n", dest_off, dest.0));
                    }
                    IrOp::BorrowShared { dest, src } | IrOp::BorrowMut { dest, src } => {
                        let dest_off = self.get_offset(*dest);
                        let src_off = self.get_offset(*src);
                        self.asm.push_str(&format!("    mov rax, qword [rbp - {}]  ; copy ptr\n", src_off));
                        self.asm.push_str(&format!("    mov qword [rbp - {}], rax  ; borrow -> Reg({})\n", dest_off, dest.0));
                    }
                    IrOp::EndBorrow { .. } => {
                        self.asm.push_str("    ; EndBorrow (no-op en runtime)\n");
                    }
                    IrOp::Free { ptr } => {
                        let off = self.get_offset(*ptr);
                        self.asm.push_str(&format!("    mov rdi, qword [rbp - {}]\n", off));
                        self.asm.push_str("    call sys_free\n");
                    }
                }
            }

            match &blk.terminator {
                Terminator::Jump(target) => {
                    self.asm.push_str(&format!("    jmp .L{}\n\n", target.0));
                }
                Terminator::BranchIf { cond, then_blk, else_blk } => {
                    let off = self.get_offset(*cond);
                    self.asm.push_str(&format!("    cmp qword [rbp - {}], 0\n", off));
                    self.asm.push_str(&format!("    jne .L{}\n", then_blk.0));
                    self.asm.push_str(&format!("    jmp .L{}\n\n", else_blk.0));
                }
                Terminator::Return => {
                    self.asm.push_str("    mov rsp, rbp\n");
                    self.asm.push_str("    pop rbp\n");
                    self.asm.push_str("    cli\n");
                    self.asm.push_str(".hang:\n");
                    self.asm.push_str("    hlt\n");
                    self.asm.push_str("    jmp .hang\n\n");
                }
                Terminator::None => panic!("Bloque sin terminador"),
            }
        }

        self.asm.clone()
    }
}
