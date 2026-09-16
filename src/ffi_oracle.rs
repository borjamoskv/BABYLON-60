//! # API C-ABI para Evaluación de Trazas (AOT Oracle & Python Bridge)
//! Extiende la pasarela nativa para permitir a Python (ctypes) interactuar
//! con el Lóbulo Inhibidor (Lean 4) y el Firewall Neurosimbólico Z3 a través de Rust Ring-0.

use crate::larsa_bft::LarsaTriadConsensus;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::slice;

/// Bucle singleton (thread-safe) del Consenso para FFI
static BFT_CONSENSUS: std::sync::OnceLock<LarsaTriadConsensus> = std::sync::OnceLock::new();

fn get_bft() -> &'static LarsaTriadConsensus {
    BFT_CONSENSUS.get_or_init(LarsaTriadConsensus::new)
}

/// Somete una traza binaria en memoria a la Tríada de Larsa y Lean 4 desde el entorno C/Python.
///
/// `trace_bytes`: Puntero C a los bytes de la traza empaquetada.
/// `len`: Longitud en bytes.
/// Retorna:
/// 1: Validado (RUNNING)
/// 0xDEAD_6060: Paradoja / Fallo BFT (POISONED)
///
/// # Safety
/// `trace_bytes` debe apuntar a un buffer legible de al menos `len` bytes.
#[no_mangle]
pub unsafe extern "C" fn b60_eval_trace(trace_bytes: *const u8, len: usize) -> u32 {
    if trace_bytes.is_null() || len == 0 {
        return crate::manifest::POISONED;
    }
    let data = unsafe { slice::from_raw_parts(trace_bytes, len) };
    let tmp_path = std::env::temp_dir().join(format!("bft_trace_{}_{}.bin", std::process::id(), len));
    if std::fs::write(&tmp_path, data).is_err() {
        return crate::manifest::POISONED;
    }
    let res = get_bft().evaluate_trace(&tmp_path);
    let _ = std::fs::remove_file(&tmp_path);
    res
}

/// Tipo para el callback C-ABI de Z3: `extern "C" fn(*const u8, usize) -> u32`
pub type Z3Callback = extern "C" fn(trace_bytes: *const u8, len: usize) -> u32;

/// Puntero global atómico al callback SMT de Python
static Z3_CALLBACK: std::sync::atomic::AtomicPtr<std::os::raw::c_void> =
    std::sync::atomic::AtomicPtr::new(std::ptr::null_mut());

/// Expone el registro de callbacks para que Python inyecte su motor Z3.
#[no_mangle]
pub extern "C" fn b60_register_z3_callback(cb: Z3Callback) {
    Z3_CALLBACK.store(cb as *mut _, std::sync::atomic::Ordering::SeqCst);
}

/// Obtiene el callback Z3 registrado
pub fn get_z3_callback() -> Option<Z3Callback> {
    let ptr = Z3_CALLBACK.load(std::sync::atomic::Ordering::SeqCst);
    if ptr.is_null() {
        None
    } else {
        Some(unsafe { std::mem::transmute::<*mut std::ffi::c_void, Z3Callback>(ptr) })
    }
}

/// Retorna la versión canónica de BABYLON-60 como string C estático
#[no_mangle]
pub extern "C" fn b60_version() -> *const c_char {
    static VERSION: &[u8] = b"4.3.0\0";
    VERSION.as_ptr() as *const c_char
}

/// Suma exacta sexagesimal en base 60^4 con cero deriva (carry a s y residuo a f)
///
/// # Safety
/// `out_s` y `out_f` deben ser punteros válidos para escribir `u64`.
#[no_mangle]
pub unsafe extern "C" fn b60_sexa_add(
    s1: u64,
    f1: u64,
    s2: u64,
    f2: u64,
    out_s: *mut u64,
    out_f: *mut u64,
) -> i32 {
    if out_s.is_null() || out_f.is_null() {
        return -1;
    }
    let fraction_base: u64 = 12_960_000; // 60^4
    let total_frac = f1 + f2;
    let carry = total_frac / fraction_base;
    let rem = total_frac % fraction_base;
    unsafe {
        *out_s = s1 + s2 + carry;
        *out_f = rem;
    }
    0
}

/// Calcula la distancia geodésica de Fisher-Rao entre dos distribuciones de probabilidad
///
/// # Safety
/// `p_ptr` y `q_ptr` deben apuntar a bloques válidos de al menos `dim` elementos `f64`.
#[no_mangle]
pub unsafe extern "C" fn b60_fisher_distance(dim: usize, p_ptr: *const f64, q_ptr: *const f64) -> f64 {
    if p_ptr.is_null() || q_ptr.is_null() || dim == 0 {
        return -1.0;
    }
    let p = unsafe { slice::from_raw_parts(p_ptr, dim) };
    let q = unsafe { slice::from_raw_parts(q_ptr, dim) };
    crate::fluid_thermo::fisher_rao_geodesic_distance(p, q)
}

/// Calcula la divergencia de Kullback-Leibler (entropía relativa) entre dos distribuciones
///
/// # Safety
/// `p_ptr` y `q_ptr` deben apuntar a bloques válidos de al menos `dim` elementos `f64`.
#[no_mangle]
pub unsafe extern "C" fn b60_kullback_leibler(dim: usize, p_ptr: *const f64, q_ptr: *const f64) -> f64 {
    if p_ptr.is_null() || q_ptr.is_null() || dim == 0 {
        return -1.0;
    }
    let p = unsafe { slice::from_raw_parts(p_ptr, dim) };
    let q = unsafe { slice::from_raw_parts(q_ptr, dim) };
    let mut d_kl = 0.0;
    for (&pi, &qi) in p.iter().zip(q.iter()) {
        if pi > 1e-12 {
            let q_c = if qi < 1e-12 { 1e-12 } else { qi };
            d_kl += pi * (pi / q_c).ln();
        }
    }
    d_kl
}

/// Evalúa una intención agéntica bajo la compuerta epistémica de Kolmogorov (Aforismo 5)
/// Códigos de retorno:
///   0 = Admitido (Alta Exergía) -> Escribe el hash SHA-256 en `out_root_buf`
///   2 = Rechazado por Cheap Talk
///   3 = Rechazado por Presupuesto Exergético Excedido
///  -1 = Error de punteros o argumentos inválidos
///
/// # Safety
/// `agent_id_ptr` y `tool_ptr` deben ser cadenas C válidas terminadas en nulo.
/// Si no es nulo, `out_root_buf` debe apuntar a un buffer de al menos `out_root_len` bytes.
#[no_mangle]
pub unsafe extern "C" fn b60_eval_agent_intent(
    agent_id_ptr: *const c_char,
    _tool_ptr: *const c_char,
    reasoning_len: usize,
    payload_len: usize,
    budget: u64,
    out_root_buf: *mut c_char,
    out_root_len: usize,
) -> i32 {
    if agent_id_ptr.is_null() {
        return -1;
    }
    if budget > 3600 {
        return 3;
    }
    let eff = if payload_len == 0 { 1 } else { payload_len };
    if reasoning_len > 100 && (reasoning_len / eff) > 50 {
        return 2;
    }
    if !out_root_buf.is_null() && out_root_len >= 65 {
        let agent_bytes = unsafe { CStr::from_ptr(agent_id_ptr).to_bytes() };
        let mut hasher = Sha256::new();
        hasher.update(agent_bytes);
        hasher.update(budget.to_le_bytes());
        let hex_hash = format!("{:064x}", hasher.finalize());
        let c_str = std::ffi::CString::new(hex_hash).unwrap();
        let bytes = c_str.as_bytes_with_nul();
        unsafe {
            std::ptr::copy_nonoverlapping(bytes.as_ptr() as *const c_char, out_root_buf, bytes.len());
        }
    }
    0
}

/// Valida y compila un grafo causal verificando aciclicidad y orden de Lamport
/// Códigos de retorno:
///   0 = DAG Válido (Escribe el número de etapas paralelas en out_num_stages)
///   1 = Paradoja Cíclica
///   2 = Inversión Temporal de Lamport (from_ts >= to_ts)
///  -1 = Punteros inválidos
///
/// # Safety
/// `node_ids` y `lamport_ts` deben apuntar a bloques válidos de longitud `num_nodes`.
/// Si `num_edges > 0`, `edge_from` y `edge_to` deben apuntar a bloques válidos de longitud `num_edges`.
/// Si no es nulo, `out_num_stages` debe ser válido para escribir un `usize`.
#[no_mangle]
pub unsafe extern "C" fn b60_dag_validate(
    num_nodes: usize,
    node_ids: *const u32,
    lamport_ts: *const u64,
    num_edges: usize,
    edge_from: *const u32,
    edge_to: *const u32,
    out_num_stages: *mut usize,
) -> i32 {
    if node_ids.is_null() || lamport_ts.is_null() {
        return -1;
    }
    let ids = unsafe { slice::from_raw_parts(node_ids, num_nodes) };
    let ts = unsafe { slice::from_raw_parts(lamport_ts, num_nodes) };

    let mut ts_map = HashMap::new();
    for i in 0..num_nodes {
        ts_map.insert(ids[i], ts[i]);
    }

    if num_edges > 0 {
        if edge_from.is_null() || edge_to.is_null() {
            return -1;
        }
        let e_from = unsafe { slice::from_raw_parts(edge_from, num_edges) };
        let e_to = unsafe { slice::from_raw_parts(edge_to, num_edges) };

        // 1. Verificar existencia de nodos en el mapa
        for i in 0..num_edges {
            let u = e_from[i];
            let v = e_to[i];
            if !ts_map.contains_key(&u) || !ts_map.contains_key(&v) {
                return -1;
            }
        }

        // 2. Detección formal de ciclos (Algoritmo de Kahn)
        let mut in_degree: HashMap<u32, usize> = HashMap::with_capacity(num_nodes);
        let mut adj: HashMap<u32, Vec<u32>> = HashMap::with_capacity(num_nodes);
        for &id in ids {
            in_degree.insert(id, 0);
            adj.insert(id, Vec::new());
        }
        for i in 0..num_edges {
            let u = e_from[i];
            let v = e_to[i];
            adj.get_mut(&u).unwrap().push(v);
            *in_degree.get_mut(&v).unwrap() += 1;
        }

        let mut queue: std::collections::VecDeque<u32> = in_degree
            .iter()
            .filter(|(_, &deg)| deg == 0)
            .map(|(&id, _)| id)
            .collect();

        let mut visited_count = 0;
        while let Some(u) = queue.pop_front() {
            visited_count += 1;
            if let Some(neighbors) = adj.get(&u) {
                for &v in neighbors {
                    if let Some(deg) = in_degree.get_mut(&v) {
                        *deg -= 1;
                        if *deg == 0 {
                            queue.push_back(v);
                        }
                    }
                }
            }
        }

        if visited_count != num_nodes {
            return 1; // Paradoja Cíclica
        }

        // 3. Verificación de Inversión Temporal de Lamport (from_ts < to_ts)
        for i in 0..num_edges {
            let u = e_from[i];
            let v = e_to[i];
            let u_ts = ts_map[&u];
            let v_ts = ts_map[&v];
            if u_ts >= v_ts {
                return 2; // Inversión temporal de Lamport
            }
        }
    }

    if !out_num_stages.is_null() {
        if num_edges > 0 {
            let e_from = unsafe { slice::from_raw_parts(edge_from, num_edges) };
            let e_to = unsafe { slice::from_raw_parts(edge_to, num_edges) };
            let mut depth: HashMap<u32, usize> = HashMap::new();
            for &id in ids {
                depth.insert(id, 1);
            }
            for _ in 0..num_nodes {
                for i in 0..num_edges {
                    let u = e_from[i];
                    let v = e_to[i];
                    let u_d = depth.get(&u).copied().unwrap_or(1);
                    let v_d = depth.get(&v).copied().unwrap_or(1);
                    if u_d + 1 > v_d {
                        depth.insert(v, u_d + 1);
                    }
                }
            }
            let max_stages = depth.values().copied().max().unwrap_or(1);
            unsafe {
                *out_num_stages = max_stages;
            }
        } else {
            unsafe {
                *out_num_stages = 1;
            }
        }
    }

    0
}
