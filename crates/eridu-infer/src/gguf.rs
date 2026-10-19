//! Parser binario zero-copy para especificación GGUF v3 sobre mmap.
//! Diseñado para deserialización en O(1) de metadatos y tensores en Apple Silicon UMA.

use std::collections::HashMap;
use std::fs::File;
use std::path::Path;
use byteorder::{ByteOrder, LittleEndian};
use memmap2::Mmap;

pub const GGUF_MAGIC: u32 = 0x46554747; // "GGUF" en Little-Endian

#[derive(Debug, Clone)]
pub struct GgufTensorMeta {
    pub name: String,
    pub dims: Vec<u64>,
    pub tensor_type: u32,
    pub offset: u64,
    pub byte_size: usize,
}

#[derive(Debug)]
pub struct GgufModel {
    #[allow(dead_code)]
    mmap: Mmap,
    pub version: u32,
    pub tensor_count: u64,
    pub metadata: HashMap<String, String>,
    pub tensors: Vec<GgufTensorMeta>,
    pub tensor_data_offset: usize,
}

impl GgufModel {
    /// Carga y mapea en memoria un archivo GGUF de forma zero-copy.
    pub fn load_mmap<P: AsRef<Path>>(path: P) -> Result<Self, String> {
        let file = File::open(path).map_err(|e| format!("Error abriendo archivo GGUF: {}", e))?;
        let mmap = unsafe {
            Mmap::map(&file).map_err(|e| format!("Error mapeando archivo en UMA: {}", e))?
        };

        if mmap.len() < 24 {
            return Err("Archivo GGUF demasiado pequeño para contener cabecera válida".into());
        }

        let magic = LittleEndian::read_u32(&mmap[0..4]);
        if magic != GGUF_MAGIC {
            return Err(format!("Magic inválido: 0x{:08X} (se esperaba 0x{:08X})", magic, GGUF_MAGIC));
        }

        let version = LittleEndian::read_u32(&mmap[4..8]);
        if version != 2 && version != 3 {
            return Err(format!("Versión GGUF no soportada: {} (esperada v2 o v3)", version));
        }

        let tensor_count = LittleEndian::read_u64(&mmap[8..16]);
        let metadata_kv_count = LittleEndian::read_u64(&mmap[16..24]);

        let mut cursor = 24;
        let mut metadata = HashMap::new();

        // Parseo de metadatos KV
        for _ in 0..metadata_kv_count {
            if cursor + 8 > mmap.len() {
                return Err("Buffer truncado al leer clave de metadatos".into());
            }
            let key_len = LittleEndian::read_u64(&mmap[cursor..cursor + 8]) as usize;
            cursor += 8;

            if cursor + key_len > mmap.len() {
                return Err("Buffer truncado al leer contenido de clave".into());
            }
            let key = std::str::from_utf8(&mmap[cursor..cursor + key_len])
                .map_err(|e| format!("Clave no es UTF-8 válido: {}", e))?
                .to_string();
            cursor += key_len;

            if cursor + 4 > mmap.len() {
                return Err("Buffer truncado al leer tipo de valor".into());
            }
            let val_type = LittleEndian::read_u32(&mmap[cursor..cursor + 4]);
            cursor += 4;

            let (val_str, new_cursor) = parse_metadata_value(&mmap, cursor, val_type)?;
            cursor = new_cursor;
            metadata.insert(key, val_str);
        }

        let alignment = metadata
            .get("general.alignment")
            .and_then(|v| v.parse::<usize>().ok())
            .unwrap_or(32);

        // Parseo de descriptores de tensores
        let mut tensors = Vec::with_capacity(tensor_count as usize);
        for _ in 0..tensor_count {
            if cursor + 8 > mmap.len() {
                return Err("Buffer truncado al leer nombre de tensor".into());
            }
            let name_len = LittleEndian::read_u64(&mmap[cursor..cursor + 8]) as usize;
            cursor += 8;

            if cursor + name_len > mmap.len() {
                return Err("Buffer truncado al leer nombre de tensor".into());
            }
            let name = std::str::from_utf8(&mmap[cursor..cursor + name_len])
                .map_err(|e| format!("Nombre de tensor no es UTF-8: {}", e))?
                .to_string();
            cursor += name_len;

            if cursor + 4 > mmap.len() {
                return Err("Buffer truncado al leer n_dims de tensor".into());
            }
            let n_dims = LittleEndian::read_u32(&mmap[cursor..cursor + 4]) as usize;
            cursor += 4;

            let mut dims = Vec::with_capacity(n_dims);
            for _ in 0..n_dims {
                if cursor + 8 > mmap.len() {
                    return Err("Buffer truncado al leer dimensiones de tensor".into());
                }
                dims.push(LittleEndian::read_u64(&mmap[cursor..cursor + 8]));
                cursor += 8;
            }

            if cursor + 4 > mmap.len() {
                return Err("Buffer truncado al leer tipo de tensor".into());
            }
            let tensor_type = LittleEndian::read_u32(&mmap[cursor..cursor + 4]);
            cursor += 4;

            if cursor + 8 > mmap.len() {
                return Err("Buffer truncado al leer offset de tensor".into());
            }
            let offset = LittleEndian::read_u64(&mmap[cursor..cursor + 8]);
            cursor += 8;

            let byte_size = calculate_tensor_byte_size(&dims, tensor_type);

            tensors.push(GgufTensorMeta {
                name,
                dims,
                tensor_type,
                offset,
                byte_size,
            });
        }

        // Alinear offset de inicio de datos
        let tensor_data_offset = (cursor + alignment - 1) & !(alignment - 1);

        Ok(Self {
            mmap,
            version,
            tensor_count,
            metadata,
            tensors,
            tensor_data_offset,
        })
    }

    /// Obtiene una referencia directa zero-copy a los bytes de un tensor específico.
    pub fn get_tensor_data(&self, tensor_index: usize) -> Option<&[u8]> {
        let meta = self.tensors.get(tensor_index)?;
        let start = self.tensor_data_offset + meta.offset as usize;
        let end = start + meta.byte_size;
        if end <= self.mmap.len() {
            Some(&self.mmap[start..end])
        } else {
            None
        }
    }
}

fn parse_metadata_value(mmap: &[u8], mut cursor: usize, val_type: u32) -> Result<(String, usize), String> {
    match val_type {
        0 => { // UINT8
            let v = mmap[cursor];
            Ok((v.to_string(), cursor + 1))
        }
        1 => { // INT8
            let v = mmap[cursor] as i8;
            Ok((v.to_string(), cursor + 1))
        }
        2 => { // UINT16
            let v = LittleEndian::read_u16(&mmap[cursor..cursor + 2]);
            Ok((v.to_string(), cursor + 2))
        }
        3 => { // INT16
            let v = LittleEndian::read_i16(&mmap[cursor..cursor + 2]);
            Ok((v.to_string(), cursor + 2))
        }
        4 => { // UINT32
            let v = LittleEndian::read_u32(&mmap[cursor..cursor + 4]);
            Ok((v.to_string(), cursor + 4))
        }
        5 => { // INT32
            let v = LittleEndian::read_i32(&mmap[cursor..cursor + 4]);
            Ok((v.to_string(), cursor + 4))
        }
        6 => { // FLOAT32
            let v = LittleEndian::read_f32(&mmap[cursor..cursor + 4]);
            Ok((v.to_string(), cursor + 4))
        }
        7 => { // BOOL
            let v = mmap[cursor] != 0;
            Ok((v.to_string(), cursor + 1))
        }
        8 => { // STRING
            let s_len = LittleEndian::read_u64(&mmap[cursor..cursor + 8]) as usize;
            cursor += 8;
            let s = std::str::from_utf8(&mmap[cursor..cursor + s_len])
                .map_err(|e| format!("String inválido: {}", e))?
                .to_string();
            Ok((s, cursor + s_len))
        }
        10 => { // UINT64
            let v = LittleEndian::read_u64(&mmap[cursor..cursor + 8]);
            Ok((v.to_string(), cursor + 8))
        }
        11 => { // INT64
            let v = LittleEndian::read_i64(&mmap[cursor..cursor + 8]);
            Ok((v.to_string(), cursor + 8))
        }
        12 => { // FLOAT64
            let v = LittleEndian::read_f64(&mmap[cursor..cursor + 8]);
            Ok((v.to_string(), cursor + 8))
        }
        9 => { // ARRAY
            let elem_type = LittleEndian::read_u32(&mmap[cursor..cursor + 4]);
            cursor += 4;
            let count = LittleEndian::read_u64(&mmap[cursor..cursor + 8]) as usize;
            cursor += 8;
            let mut items = Vec::new();
            for _ in 0..count.min(10) { // Limitamos para display
                let (val, next) = parse_metadata_value(mmap, cursor, elem_type)?;
                items.push(val);
                cursor = next;
            }
            if count > 10 {
                items.push(format!("... (+{} elementos)", count - 10));
            }
            Ok((format!("[{}]", items.join(", ")), cursor))
        }
        _ => Err(format!("Tipo de valor de metadatos desconocido: {}", val_type)),
    }
}

fn calculate_tensor_byte_size(dims: &[u64], tensor_type: u32) -> usize {
    let num_elements: u64 = dims.iter().product();
    match tensor_type {
        0 => (num_elements * 4) as usize, // F32
        1 => (num_elements * 2) as usize, // F16
        2 => (num_elements.div_ceil(32) * 18) as usize, // Q4_0 (block_size=32, 18 bytes)
        8 => (num_elements.div_ceil(32) * 34) as usize, // Q8_0 (block_size=32, 34 bytes)
        12 => (num_elements.div_ceil(256) * 144) as usize, // Q4_K
        _ => (num_elements * 2) as usize, // Default fallback aproximado
    }
}
