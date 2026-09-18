// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened (LOWERING: AST -> IR)
// ============================================================================
use crate::ast::{AST, Stmt};
use crate::ir::{Reg, IrOp, BasicBlock, Terminator, BlockId};
use crate::layout::LayoutEngine;
use std::collections::HashMap;

pub struct LoweringContext {
    pub current_reg: usize,
    pub var_to_reg: HashMap<String, Reg>,
}

impl Default for LoweringContext {
    fn default() -> Self {
        Self::new()
    }
}

impl LoweringContext {
    pub fn new() -> Self {
        Self {
            current_reg: 0,
            var_to_reg: HashMap::new(),
        }
    }

    fn next_reg(&mut self) -> Reg {
        let r = Reg(self.current_reg);
        self.current_reg += 1;
        r
    }

    pub fn lower(&mut self, ast: &AST, layout: &LayoutEngine) -> BasicBlock {
        let mut ops = Vec::new();
        
        for stmt in &ast.statements {
            match stmt {
                Stmt::LetAlloc(var, struct_name) => {
                    let r = self.next_reg();
                    self.var_to_reg.insert(var.clone(), r);
                    
                    if let Some(st) = layout.structs.get(struct_name) {
                        ops.push(IrOp::Alloc { dest: r, size: st.size });
                    } else {
                        panic!("Struct {} not defined in layout", struct_name);
                    }
                }
                Stmt::AssignField(var, _field, val) => {
                    let base_reg = *self.var_to_reg.get(var).expect("Undefined var");
                    let field_ptr = self.next_reg();
                    let val_reg = self.next_reg();
                    
                    // Note: full lowering would lookup the struct type of var, then find the field offset.
                    // For now, assume dummy offset 0 (PoC constraint).
                    ops.push(IrOp::FieldPtr { dest: field_ptr, base: base_reg, offset: 0 });
                    ops.push(IrOp::ConstInt { dest: val_reg, val: *val });
                    ops.push(IrOp::Store { ptr: field_ptr, val: val_reg });
                }
                Stmt::Free(var) => {
                    let base_reg = *self.var_to_reg.get(var).expect("Undefined var");
                    ops.push(IrOp::Free { ptr: base_reg });
                }
            }
        }
        
        BasicBlock {
            id: BlockId(0),
            instructions: ops,
            terminator: Terminator::Return,
        }
    }
}
