// ============================================================================
// B60 C-ABI FOREIGN FUNCTION INTERFACE (FFI) FOR PYTHON & BARE-METAL EMBEDDING
// Framework: C5-REAL | Teorema 14: Isomorfismo Semántico C-ABI
// ============================================================================

use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::slice;

use crate::arithmetic::{Tick60, FRACTION_BASE};
use crate::fisher::FisherSimplex;
use crate::transducer::{AgentActionIntent, EpistemicEvaluation, EpistemicGate};
use crate::vm::F60VM;

/// Retorna la versión canónica del runtime B60 como string C estático
#[no_mangle]
pub extern "C" fn b60_version() -> *const c_char {
    static VERSION: &[u8] = b"1.0.0-omega\0";
    VERSION.as_ptr() as *const c_char
}

/// Suma exacta sexagesimal en base 60^4 con cero deriva
#[no_mangle]
pub extern "C" fn b60_sexa_add(
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
    let total_frac = f1 + f2;
    let carry = total_frac / FRACTION_BASE;
    let rem = total_frac % FRACTION_BASE;
    unsafe {
        *out_s = s1 + s2 + carry;
        *out_f = rem;
    }
    0
}

/// Calcula la distancia geodésica de Fisher-Rao entre dos distribuciones de probabilidad
#[no_mangle]
pub extern "C" fn b60_fisher_distance(dim: usize, p_ptr: *const f64, q_ptr: *const f64) -> f64 {
    if p_ptr.is_null() || q_ptr.is_null() || dim == 0 {
        return -1.0;
    }
    let p = unsafe { slice::from_raw_parts(p_ptr, dim) };
    let q = unsafe { slice::from_raw_parts(q_ptr, dim) };

    FisherSimplex::fisher_rao_distance(p, q)
}

/// Calcula la divergencia de Kullback-Leibler (entropía relativa) entre dos distribuciones
#[no_mangle]
pub extern "C" fn b60_kullback_leibler(dim: usize, p_ptr: *const f64, q_ptr: *const f64) -> f64 {
    if p_ptr.is_null() || q_ptr.is_null() || dim == 0 {
        return -1.0;
    }
    let p = unsafe { slice::from_raw_parts(p_ptr, dim) };
    let q = unsafe { slice::from_raw_parts(q_ptr, dim) };

    FisherSimplex::relative_entropy_kl(p, q)
}

/// Evalúa una intención agéntica bajo la compuerta epistémica de Kolmogorov (Aforismo 5)
/// Códigos de retorno:
///   0 = Admitido (Alta Exergía) -> Escribe el hash SHA3 del MMR Root en `out_root_buf`
///   2 = Rechazado por Cheap Talk
///   3 = Rechazado por Presupuesto Exergético Excedido
///  -1 = Error de punteros o argumentos inválidos
#[no_mangle]
pub extern "C" fn b60_eval_agent_intent(
    agent_id_ptr: *const c_char,
    tool_ptr: *const c_char,
    reasoning_len: usize,
    payload_len: usize,
    budget: u64,
    out_root_buf: *mut c_char,
    out_root_len: usize,
) -> i32 {
    if agent_id_ptr.is_null() || tool_ptr.is_null() {
        return -1;
    }

    let agent_id = match unsafe { CStr::from_ptr(agent_id_ptr) }.to_str() {
        Ok(s) => s.to_string(),
        Err(_) => return -1,
    };

    let tool_name = match unsafe { CStr::from_ptr(tool_ptr) }.to_str() {
        Ok(s) => s.to_string(),
        Err(_) => return -1,
    };

    let mut gate = EpistemicGate::new(50, 3600);
    let intent = AgentActionIntent {
        agent_id,
        tool_name,
        reasoning_trace_len: reasoning_len,
        executable_payload_len: payload_len,
        exergy_budget: budget,
        timestamp: Tick60::zero(),
    };

    let evaluation = gate.transduce_and_execute(&intent);
    match evaluation {
        EpistemicEvaluation::Accepted { mmr_root, .. } => {
            if !out_root_buf.is_null() && out_root_len > mmr_root.len() {
                if let Ok(c_str) = CString::new(mmr_root) {
                    let bytes = c_str.as_bytes_with_nul();
                    unsafe {
                        std::ptr::copy_nonoverlapping(bytes.as_ptr() as *const c_char, out_root_buf, bytes.len());
                    }
                }
            }
            0
        }
        EpistemicEvaluation::RejectedCheapTalk { .. } => 2,
        EpistemicEvaluation::RejectedBudgetExceeded { .. } => 3,
        EpistemicEvaluation::RuntimeError(_) => -2,
    }
}

/// Ejecuta una tira de bytecode sexagesimal en la VM F60
#[no_mangle]
pub extern "C" fn b60_run_bytecode(
    bytecode_ptr: *const u8,
    bytecode_len: usize,
    out_cycles: *mut u64,
) -> i32 {
    if bytecode_ptr.is_null() || bytecode_len == 0 {
        return -1;
    }
    let bytecode = unsafe { slice::from_raw_parts(bytecode_ptr, bytecode_len) };
    let mut vm = F60VM::new();

    match vm.execute(bytecode) {
        Ok(()) => {
            if !out_cycles.is_null() {
                unsafe {
                    *out_cycles = vm.pc as u64;
                }
            }
            0
        }
        Err(_) => -2,
    }
}

/// Valida y compila un grafo causal verificando aciclicidad y orden de Lamport
/// Códigos de retorno:
///   0 = DAG Válido (Escribe el número de etapas paralelas en out_num_stages)
///   1 = Paradoja Cíclica (Contiene ciclos dirigidos)
///   2 = Inversión Temporal de Lamport (from_ts >= to_ts)
///  -1 = Punteros inválidos
#[no_mangle]
pub extern "C" fn b60_dag_validate(
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
    if num_edges > 0 && (edge_from.is_null() || edge_to.is_null()) {
        return -1;
    }

    let ids = unsafe { slice::from_raw_parts(node_ids, num_nodes) };
    let ts = unsafe { slice::from_raw_parts(lamport_ts, num_nodes) };
    let e_from = if num_edges > 0 { unsafe { slice::from_raw_parts(edge_from, num_edges) } } else { &[] };
    let e_to = if num_edges > 0 { unsafe { slice::from_raw_parts(edge_to, num_edges) } } else { &[] };

    let mut dag = crate::dag::CausalDag::new();

    for i in 0..num_nodes {
        let node = crate::dag::CausalNode {
            id: ids[i],
            label: format!("node_{}", ids[i]),
            exergy_cost: 10,
            belief_coords: vec![],
            lamport_ts: ts[i],
        };
        if dag.add_node(node).is_err() {
            return -1;
        }
    }

    for i in 0..num_edges {
        match dag.add_edge(e_from[i], e_to[i]) {
            Ok(()) => {}
            Err(crate::dag::CausalParadoxError::TemporalInversion { .. }) => return 2,
            Err(_) => return -1,
        }
    }

    match dag.compile() {
        Ok(plan) => {
            if !out_num_stages.is_null() {
                unsafe {
                    *out_num_stages = plan.execution_stages.len();
                }
            }
            0
        }
        Err(crate::dag::CausalParadoxError::CyclicAnomaly { .. }) => 1,
        Err(_) => -1,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CStr;

    #[test]
    fn test_ffi_version() {
        let v_ptr = b60_version();
        let c_str = unsafe { CStr::from_ptr(v_ptr) };
        assert_eq!(c_str.to_str().unwrap(), "1.0.0-omega");
    }

    #[test]
    fn test_ffi_sexa_add() {
        let mut s: u64 = 0;
        let mut f: u64 = 0;
        let ret = b60_sexa_add(10, 6480000, 5, 6480000, &mut s, &mut f);
        assert_eq!(ret, 0);
        assert_eq!(s, 16); // 10 + 5 + 1 carry
        assert_eq!(f, 0);
    }

    #[test]
    fn test_ffi_fisher_distance() {
        let p = [0.5, 0.5];
        let q = [0.5, 0.5];
        let dist = b60_fisher_distance(2, p.as_ptr(), q.as_ptr());
        assert!(dist.abs() < 1e-12);
    }

    #[test]
    fn test_ffi_eval_agent_intent() {
        let agent = CString::new("AGENT-TEST").unwrap();
        let tool = CString::new("tool_action").unwrap();
        let mut buf = [0 as c_char; 128];

        // Valid call
        let ret = b60_eval_agent_intent(agent.as_ptr(), tool.as_ptr(), 100, 50, 1000, buf.as_mut_ptr(), buf.len());
        assert_eq!(ret, 0);
        let root_str = unsafe { CStr::from_ptr(buf.as_ptr()) }.to_str().unwrap();
        assert_eq!(root_str.len(), 64);

        // Cheap talk call
        let ret_cheap = b60_eval_agent_intent(agent.as_ptr(), tool.as_ptr(), 4000, 10, 1000, buf.as_mut_ptr(), buf.len());
        assert_eq!(ret_cheap, 2);
    }

    #[test]
    fn test_ffi_dag_validate() {
        let node_ids = [1u32, 2, 3];
        let lamport_ts = [1u64, 2, 3];
        let edge_from = [1u32, 2];
        let edge_to = [2u32, 3];
        let mut stages: usize = 0;

        let ret = b60_dag_validate(
            3,
            node_ids.as_ptr(),
            lamport_ts.as_ptr(),
            2,
            edge_from.as_ptr(),
            edge_to.as_ptr(),
            &mut stages,
        );
        assert_eq!(ret, 0);
        assert_eq!(stages, 3);
    }
}
