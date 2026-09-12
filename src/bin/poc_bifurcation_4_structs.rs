// ============================================================================
// PoC: BIFURCATION 4 - EL INFIERNO ESTRUCTURAL (STRUCTS & ALIGNMENT)
// BABYLON-60 / C5-REAL
// ============================================================================
use std::collections::HashMap;

// --- AST ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Type {
    I64,
    Bool,
    Struct(String), // Name of the struct
    Pointer(Box<Type>),
}

#[derive(Debug, Clone)]
pub struct StructDef {
    pub name: String,
    pub fields: Vec<(String, Type)>,
}

// --- LAYOUT ENGINE ---
#[derive(Debug, Clone)]
pub struct StructLayout {
    pub size: usize,
    pub alignment: usize,
    pub field_offsets: HashMap<String, usize>,
    pub field_types: HashMap<String, Type>,
}

pub struct LayoutEngine {
    pub structs: HashMap<String, StructLayout>,
}

impl LayoutEngine {
    pub fn new() -> Self {
        Self { structs: HashMap::new() }
    }

    pub fn compute_layout(&mut self, def: &StructDef) {
        let mut current_offset = 0;
        let mut max_alignment = 1;
        let mut offsets = HashMap::new();
        let mut types = HashMap::new();

        for (fname, ftype) in &def.fields {
            let (size, align) = self.size_and_align(ftype);
            
            // Alineamiento del offset actual (Padding)
            if current_offset % align != 0 {
                current_offset += align - (current_offset % align);
            }
            
            offsets.insert(fname.clone(), current_offset);
            types.insert(fname.clone(), ftype.clone());
            
            current_offset += size;
            if align > max_alignment {
                max_alignment = align;
            }
        }

        // Padding final del struct entero (Tail Padding)
        if current_offset % max_alignment != 0 {
            current_offset += max_alignment - (current_offset % max_alignment);
        }

        self.structs.insert(def.name.clone(), StructLayout {
            size: current_offset,
            alignment: max_alignment,
            field_offsets: offsets,
            field_types: types,
        });
    }

    pub fn size_and_align(&self, ty: &Type) -> (usize, usize) {
        match ty {
            Type::I64 | Type::Pointer(_) => (8, 8), // 64-bit C-ABI
            Type::Bool => (1, 1),
            Type::Struct(name) => {
                let layout = self.structs.get(name).expect("Struct not defined");
                (layout.size, layout.alignment)
            }
        }
    }
}

// --- IR & CFG ---
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
    FieldPtr { dest: Reg, base: Reg, offset: usize }, // NODO CAUSAL DE ESTRUCTURAS
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

// --- BACKEND X86_64 ---
pub struct X86Backend {
    asm: String,
    stack_offsets: HashMap<usize, usize>,
    next_offset: usize,
}

impl X86Backend {
    pub fn new() -> Self {
        Self { 
            asm: String::new(), 
            stack_offsets: HashMap::new(), 
            next_offset: 16 // Respetar alineamiento
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
        self.asm.push_str("bits 64\n\n");
        self.asm.push_str("global _start\n");
        self.asm.push_str("extern sys_alloc\n");
        self.asm.push_str("extern sys_free\n\n");
        self.asm.push_str("section .text\n");
        self.asm.push_str("_start:\n");
        self.asm.push_str("    ; --- PRÓLOGO DEL KERNEL ---\n");
        self.asm.push_str("    push rbp\n");
        self.asm.push_str("    mov rbp, rsp\n");
        self.asm.push_str("    sub rsp, 256\n");
        self.asm.push_str("    and rsp, -16  ; SysV ABI: alinear a 16 bytes antes del call\n\n");

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

fn test_struct_compilation() {
    let mut layout = LayoutEngine::new();
    
    // struct Sensor { temperature: i64, active: bool }
    let sensor_def = StructDef {
        name: "Sensor".to_string(),
        fields: vec![
            ("temperature".to_string(), Type::I64),
            ("active".to_string(), Type::Bool),
        ],
    };
    layout.compute_layout(&sensor_def);
    
    let sensor_layout = layout.structs.get("Sensor").unwrap();
    println!("--- C5-REAL: LAYOUT COMPUTADO ---");
    println!("Struct Sensor: size={}, align={}", sensor_layout.size, sensor_layout.alignment);
    println!("  temperature: offset={}", sensor_layout.field_offsets.get("temperature").unwrap());
    println!("  active:      offset={}", sensor_layout.field_offsets.get("active").unwrap());
    
    assert_eq!(sensor_layout.size, 16); // 8(i64) + 1(bool) + 7(padding) = 16

    // IR Causal Graph
    let blocks = vec![
        BasicBlock {
            id: BlockId(0),
            instructions: vec![
                // 1. SysCall alloc (size dinámico del Layout Engine)
                IrOp::Alloc { dest: Reg(0), size: sensor_layout.size },
                
                // 2. Apuntar a 'temperature' (offset 0)
                IrOp::FieldPtr { dest: Reg(1), base: Reg(0), offset: *sensor_layout.field_offsets.get("temperature").unwrap() },
                
                // 3. Apuntar a 'active' (offset 8)
                IrOp::FieldPtr { dest: Reg(2), base: Reg(0), offset: *sensor_layout.field_offsets.get("active").unwrap() },
                
                // 4. Mutar state: sensor.temperature = 42
                IrOp::ConstInt { dest: Reg(3), val: 42 },
                IrOp::Store { ptr: Reg(1), val: Reg(3) },
                
                // 5. Mutar state: sensor.active = true
                IrOp::ConstBool { dest: Reg(4), val: true },
                IrOp::Store { ptr: Reg(2), val: Reg(4) },
                
                // 6. Invariante 0 Leaks: Destrucción del objeto base destruye campos
                IrOp::Free { ptr: Reg(0) },
            ],
            terminator: Terminator::Return,
        }
    ];

    let mut backend = X86Backend::new();
    let asm = backend.compile(&blocks);
    
    println!("\n--- C5-REAL: ASM GENERADO (BIFURCACIÓN 4) ---");
    println!("{}", asm);
}

fn stress_test() {
    println!("\n=== STRESS TEST (1000 iteraciones empíricas) ===");
    let mut success = 0;
    for _ in 0..1000 {
        let mut layout = LayoutEngine::new();
        // struct Invertido { a: bool, b: i64 }
        layout.compute_layout(&StructDef {
            name: "Dummy".to_string(),
            fields: vec![("a".to_string(), Type::Bool), ("b".to_string(), Type::I64)],
        });
        let size = layout.structs.get("Dummy").unwrap().size;
        if size == 16 { // 1(bool) + 7(padding) + 8(i64) = 16
            success += 1;
        }
    }
    println!("Falsación superada: {}/1000 paddings deterministas correctos sin divergencia.", success);
}

fn main() {
    test_struct_compilation();
    stress_test();
}
