use std::collections::HashMap;
use crate::types::{Type, StructDef};

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
            Type::I64 | Type::Pointer(_) => (8, 8),
            Type::Bool => (1, 1),
            Type::Struct(name) => {
                let layout = self.structs.get(name).expect("Struct not defined");
                (layout.size, layout.alignment)
            }
        }
    }
}
