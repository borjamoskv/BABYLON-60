//! # Cliente del Oráculo AOT (INV_C5_LEAN_AOT_ORACLE)
//!
//! Punto de anclaje termodinámico para invocar el binario nativo compilado desde Lean 4.
//! Transduce la causalidad de Ring-0 al Lóbulo Inhibidor (Proof-Carrying Execution)
//! mediante streaming de I/O a coste O(1).

use std::process::Command;
use std::path::Path;
use std::time::Instant;

/// Resultado de la Inferencia AOT.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OracleVerdict {
    /// El oráculo certificó la traza. Exit 0. Causalidad intacta.
    Validated,
    /// El oráculo colapsó la traza por paradoja o violación estructural. Exit != 0.
    ParadoxDetected,
    /// Error de Invocación (el binario no existe o el I/O falló).
    SystemFailure,
}

/// Cliente proxy para el Oráculo de C-FFI compilado desde Lean 4.
pub struct AotOracleClient;

impl AotOracleClient {
    /// Invoca el oráculo binario precompilado pasándole el `trace_path`.
    /// La invocación es síncrona pero fuera del Hot Path (vía I/O de disco o pipes).
    pub fn verify_trace<P: AsRef<Path>>(trace_path: P) -> OracleVerdict {
        let binary_path = "proof/lean/.lake/build/bin/babylon_aot_oracle";
        
        if Path::new(binary_path).exists() {
            if let Ok(status) = Command::new(binary_path).arg(trace_path.as_ref()).status() {
                if status.success() {
                    return OracleVerdict::Validated;
                } else {
                    return OracleVerdict::ParadoxDetected;
                }
            }
        }

        // Fallback determinista nativo (isomorfo formal a BabylonTrace.lean / BabylonAOTOracle.lean)
        // cuando el binario Lean 4 AOT no está precompilado en el runtime de CI/CD.
        Self::verify_trace_native(trace_path.as_ref())
    }

    /// Evaluador de la máquina de estados Seqlock estricto O(N) idéntico a BabylonTrace.lean
    pub fn verify_trace_native(trace_path: &Path) -> OracleVerdict {
        let bytes = match std::fs::read(trace_path) {
            Ok(b) => b,
            Err(_) => return OracleVerdict::SystemFailure,
        };

        if bytes.len() % 8 != 0 {
            return OracleVerdict::ParadoxDetected;
        }

        let mut curr_seq: u32 = 0;
        let mut curr_writer: Option<u32> = None;

        for chunk in bytes.as_chunks::<8>().0 {
            let packed = u64::from_le_bytes(*chunk);
            let action = (packed & 0xFF) as u8;
            let thread_id = ((packed >> 8) & 0xFFFFFF) as u32;
            let seq = ((packed >> 32) & 0xFFFFFFFF) as u32;

            match action {
                // Action::writeBegin
                0 => {
                    if curr_seq.is_multiple_of(2) && seq == curr_seq + 1 && curr_writer.is_none() {
                        curr_seq = seq;
                        curr_writer = Some(thread_id);
                    } else {
                        return OracleVerdict::ParadoxDetected;
                    }
                }
                // Action::writeEnd
                1 => {
                    if curr_seq % 2 == 1 && seq == curr_seq + 1 && curr_writer == Some(thread_id) {
                        curr_seq = seq;
                        curr_writer = None;
                    } else {
                        return OracleVerdict::ParadoxDetected;
                    }
                }
                // Action::read
                2 if seq.is_multiple_of(2) && seq <= curr_seq => {
                    // Las lecturas puras no alteran la memoria causal global
                }
                2 => {
                    return OracleVerdict::ParadoxDetected;
                }
                // Acción desconocida
                _ => return OracleVerdict::ParadoxDetected,
            }
        }

        OracleVerdict::Validated
    }

    /// Método analítico: devuelve además la latencia de la certificación formal.
    pub fn verify_trace_with_latency<P: AsRef<Path>>(trace_path: P) -> (OracleVerdict, std::time::Duration) {
        let t0 = Instant::now();
        let verdict = Self::verify_trace(trace_path);
        (verdict, t0.elapsed())
    }
}

// ============================================================================
// BOUNDED E-GRAPH & BRANCHLESS AOT COMPILER PARA LA 7-TUPLA (NEMESIS / ABZU)
// ============================================================================

use std::collections::HashMap;

/// Árbol Sintáctico Abstracto (AST) para políticas booleanas sobre la 7-Tupla de Decisión:
/// `0 = Authority, 1 = Capability, 2 = Policy, 3 = Resource, 4 = Effect, 5 = Context, 6 = Epoch`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum PolicyExpr {
    /// Constante booleana (`true` o `false`).
    Const(bool),
    /// Índice de dimensión de la 7-Tupla (`0..=6`).
    Var(u8),
    /// Negación lógica (`!x`).
    Not(Box<PolicyExpr>),
    /// Conjunción lógica (`x & y`).
    And(Box<PolicyExpr>, Box<PolicyExpr>),
    /// Disyunción lógica (`x | y`).
    Or(Box<PolicyExpr>, Box<PolicyExpr>),
}

impl PolicyExpr {
    /// Evalúa recursivamente el árbol sintáctico contra la máscara de 7 bits de la 7-Tupla.
    /// Se utiliza como oráculo de referencia frente a la cinta plana AOT (`CompiledPolicyTape`).
    pub fn eval_recursive(&self, tuple_mask: u8) -> bool {
        match self {
            PolicyExpr::Const(b) => *b,
            PolicyExpr::Var(idx) => ((tuple_mask >> (*idx & 7)) & 1) != 0,
            PolicyExpr::Not(inner) => !inner.eval_recursive(tuple_mask),
            PolicyExpr::And(lhs, rhs) => {
                lhs.eval_recursive(tuple_mask) && rhs.eval_recursive(tuple_mask)
            }
            PolicyExpr::Or(lhs, rhs) => {
                lhs.eval_recursive(tuple_mask) || rhs.eval_recursive(tuple_mask)
            }
        }
    }
}

/// Instrucción plana en formato SSA (Single Static Assignment) sin ramificaciones
/// para la cinta de evaluación AOT de políticas de la 7-Tupla.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FlatOp {
    /// Carga una constante booleana literal.
    ConstBool(bool),
    /// Extrae el bit correspondiente a la dimensión `0..=6` de la máscara de la 7-Tupla.
    LoadTupleBit(u8),
    /// Negación bit a bit del registro indicado.
    BitNot(usize),
    /// Conjunción bit a bit de dos registros previos (`lhs <= rhs` por forma canónica).
    BitAnd(usize, usize),
    /// Disyunción bit a bit de dos registros previos (`lhs <= rhs` por forma canónica).
    BitOr(usize, usize),
}

/// Cinta lineal compilada AOT con Eliminación de Subexpresiones Comunes (CSE)
/// y simplificación algebraica por saturación de igualdad acotada (Bounded E-Graph).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledPolicyTape {
    /// Secuencia topológica lineal de instrucciones planas deduplicadas.
    pub ops: Vec<FlatOp>,
    /// Índice del registro raíz cuyo valor final representa el veredicto de la política.
    pub root_reg: usize,
}

/// Compila una expresión de política `PolicyExpr` en una cinta lineal `CompiledPolicyTape`
/// aplicando simplificación algebraica canónica y Hashconsing (CSE) bajo un presupuesto
/// estricto de `max_nodes` e-nodos únicos (Fail-Closed).
pub fn compile_bounded_egraph(
    expr: &PolicyExpr,
    max_nodes: usize,
) -> Result<CompiledPolicyTape, &'static str> {
    struct BoundedEGraph {
        ops: Vec<FlatOp>,
        memo: HashMap<FlatOp, usize>,
        max_nodes: usize,
    }

    impl BoundedEGraph {
        fn new(max_nodes: usize) -> Self {
            Self {
                ops: Vec::new(),
                memo: HashMap::new(),
                max_nodes,
            }
        }

        fn intern(&mut self, op: FlatOp) -> Result<usize, &'static str> {
            if let Some(&id) = self.memo.get(&op) {
                return Ok(id);
            }
            if self.ops.len() >= self.max_nodes {
                return Err("Bounded E-Graph node budget exceeded");
            }
            let id = self.ops.len();
            self.ops.push(op);
            self.memo.insert(op, id);
            Ok(id)
        }

        fn is_complement(&self, a: usize, b: usize) -> bool {
            matches!(self.ops[a], FlatOp::BitNot(inner) if inner == b)
                || matches!(self.ops[b], FlatOp::BitNot(inner) if inner == a)
        }

        fn compile_node(&mut self, expr: &PolicyExpr) -> Result<usize, &'static str> {
            match expr {
                PolicyExpr::Const(b) => self.intern(FlatOp::ConstBool(*b)),
                PolicyExpr::Var(idx) => self.intern(FlatOp::LoadTupleBit(*idx & 7)),
                PolicyExpr::Not(inner) => {
                    let r = self.compile_node(inner)?;
                    match self.ops[r] {
                        // Plegado de constantes: !true -> false, !false -> true
                        FlatOp::ConstBool(b) => self.intern(FlatOp::ConstBool(!b)),
                        // Doble negación: !!x -> x
                        FlatOp::BitNot(orig) => Ok(orig),
                        _ => self.intern(FlatOp::BitNot(r)),
                    }
                }
                PolicyExpr::And(lhs, rhs) => {
                    let mut a = self.compile_node(lhs)?;
                    let mut b = self.compile_node(rhs)?;

                    // Ordenación conmutativa canónica de operandos
                    if a > b {
                        std::mem::swap(&mut a, &mut b);
                    }

                    // Idempotencia: x & x -> x
                    if a == b {
                        return Ok(a);
                    }

                    // Aniquilación e Identidad: x & false -> false, x & true -> x
                    if matches!(self.ops[a], FlatOp::ConstBool(false))
                        || matches!(self.ops[b], FlatOp::ConstBool(false))
                    {
                        return self.intern(FlatOp::ConstBool(false));
                    }
                    if matches!(self.ops[a], FlatOp::ConstBool(true)) {
                        return Ok(b);
                    }
                    if matches!(self.ops[b], FlatOp::ConstBool(true)) {
                        return Ok(a);
                    }

                    // Complementación: x & !x -> false
                    if self.is_complement(a, b) {
                        return self.intern(FlatOp::ConstBool(false));
                    }

                    // Absorción: x & (x | y) -> x
                    if let FlatOp::BitOr(x, y) = self.ops[b] {
                        if x == a || y == a {
                            return Ok(a);
                        }
                    }
                    if let FlatOp::BitOr(x, y) = self.ops[a] {
                        if x == b || y == b {
                            return Ok(b);
                        }
                    }

                    // Reducción asociativa e inspección de complementos internos: x & (x & y) -> x & y
                    if let FlatOp::BitAnd(x, y) = self.ops[b] {
                        if x == a || y == a {
                            return Ok(b);
                        }
                        if self.is_complement(a, x) || self.is_complement(a, y) {
                            return self.intern(FlatOp::ConstBool(false));
                        }
                    }
                    if let FlatOp::BitAnd(x, y) = self.ops[a] {
                        if x == b || y == b {
                            return Ok(a);
                        }
                        if self.is_complement(b, x) || self.is_complement(b, y) {
                            return self.intern(FlatOp::ConstBool(false));
                        }
                    }

                    self.intern(FlatOp::BitAnd(a, b))
                }
                PolicyExpr::Or(lhs, rhs) => {
                    let mut a = self.compile_node(lhs)?;
                    let mut b = self.compile_node(rhs)?;

                    // Ordenación conmutativa canónica de operandos
                    if a > b {
                        std::mem::swap(&mut a, &mut b);
                    }

                    // Idempotencia: x | x -> x
                    if a == b {
                        return Ok(a);
                    }

                    // Aniquilación e Identidad: x | true -> true, x | false -> x
                    if matches!(self.ops[a], FlatOp::ConstBool(true))
                        || matches!(self.ops[b], FlatOp::ConstBool(true))
                    {
                        return self.intern(FlatOp::ConstBool(true));
                    }
                    if matches!(self.ops[a], FlatOp::ConstBool(false)) {
                        return Ok(b);
                    }
                    if matches!(self.ops[b], FlatOp::ConstBool(false)) {
                        return Ok(a);
                    }

                    // Complementación: x | !x -> true
                    if self.is_complement(a, b) {
                        return self.intern(FlatOp::ConstBool(true));
                    }

                    // Absorción: x | (x & y) -> x
                    if let FlatOp::BitAnd(x, y) = self.ops[b] {
                        if x == a || y == a {
                            return Ok(a);
                        }
                    }
                    if let FlatOp::BitAnd(x, y) = self.ops[a] {
                        if x == b || y == b {
                            return Ok(b);
                        }
                    }

                    // Reducción asociativa e inspección de complementos internos: x | (x | y) -> x | y
                    if let FlatOp::BitOr(x, y) = self.ops[b] {
                        if x == a || y == a {
                            return Ok(b);
                        }
                        if self.is_complement(a, x) || self.is_complement(a, y) {
                            return self.intern(FlatOp::ConstBool(true));
                        }
                    }
                    if let FlatOp::BitOr(x, y) = self.ops[a] {
                        if x == b || y == b {
                            return Ok(a);
                        }
                        if self.is_complement(b, x) || self.is_complement(b, y) {
                            return self.intern(FlatOp::ConstBool(true));
                        }
                    }

                    self.intern(FlatOp::BitOr(a, b))
                }
            }
        }

        /// Extrae el cono causal alcanzable desde `root`, eliminando e-nodos huérfanos
        /// que hayan colapsado por leyes de aniquilación, absorción o complementación.
        fn extract_compact_tape(&self, root: usize) -> CompiledPolicyTape {
            let mut reachable = vec![false; self.ops.len()];
            reachable[root] = true;
            for i in (0..=root).rev() {
                if reachable[i] {
                    match self.ops[i] {
                        FlatOp::ConstBool(_) | FlatOp::LoadTupleBit(_) => {}
                        FlatOp::BitNot(src) => {
                            reachable[src] = true;
                        }
                        FlatOp::BitAnd(lhs, rhs) | FlatOp::BitOr(lhs, rhs) => {
                            reachable[lhs] = true;
                            reachable[rhs] = true;
                        }
                    }
                }
            }

            let mut remap = vec![0usize; self.ops.len()];
            let mut compact_ops = Vec::new();
            for (old_idx, &op) in self.ops.iter().enumerate() {
                if reachable[old_idx] {
                    let new_op = match op {
                        FlatOp::ConstBool(b) => FlatOp::ConstBool(b),
                        FlatOp::LoadTupleBit(bit) => FlatOp::LoadTupleBit(bit),
                        FlatOp::BitNot(src) => FlatOp::BitNot(remap[src]),
                        FlatOp::BitAnd(lhs, rhs) => {
                            let nl = remap[lhs];
                            let nr = remap[rhs];
                            if nl <= nr {
                                FlatOp::BitAnd(nl, nr)
                            } else {
                                FlatOp::BitAnd(nr, nl)
                            }
                        }
                        FlatOp::BitOr(lhs, rhs) => {
                            let nl = remap[lhs];
                            let nr = remap[rhs];
                            if nl <= nr {
                                FlatOp::BitOr(nl, nr)
                            } else {
                                FlatOp::BitOr(nr, nl)
                            }
                        }
                    };
                    remap[old_idx] = compact_ops.len();
                    compact_ops.push(new_op);
                }
            }

            CompiledPolicyTape {
                ops: compact_ops,
                root_reg: remap[root],
            }
        }
    }

    let mut egraph = BoundedEGraph::new(max_nodes);
    let root = egraph.compile_node(expr)?;
    Ok(egraph.extract_compact_tape(root))
}

impl CompiledPolicyTape {
    /// Compila una expresión de política `PolicyExpr` en una cinta lineal `CompiledPolicyTape`
    /// bajo un presupuesto estricto de `max_nodes` e-nodos únicos.
    pub fn compile_bounded_egraph(
        expr: &PolicyExpr,
        max_nodes: usize,
    ) -> Result<Self, &'static str> {
        compile_bounded_egraph(expr, max_nodes)
    }

    /// Evalúa la cinta lineal `ops` en una sola pasada secuencial usando operaciones
    /// bit a bit puras (`&`, `|`, `!`) sobre un vector de registros sin recursión,
    /// devolviendo el valor booleano final alojado en `root_reg`.
    pub fn eval_branchless(&self, tuple_mask: u8) -> bool {
        if self.ops.is_empty() {
            return false;
        }
        let mut regs = vec![false; self.ops.len()];
        for (i, op) in self.ops.iter().enumerate() {
            regs[i] = match *op {
                FlatOp::ConstBool(val) => val,
                FlatOp::LoadTupleBit(bit) => ((tuple_mask >> (bit & 7)) & 1) != 0,
                FlatOp::BitNot(src) => !regs[src],
                FlatOp::BitAnd(lhs, rhs) => regs[lhs] & regs[rhs],
                FlatOp::BitOr(lhs, rhs) => regs[lhs] | regs[rhs],
            };
        }
        regs[self.root_reg]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_egraph_algebraic_simplification_and_cse() {
        // 1. Contradicción algebraica: (Authority & !Authority) -> false (1 único nodo ConstBool(false))
        let contradiction = PolicyExpr::And(
            Box::new(PolicyExpr::Var(0)),
            Box::new(PolicyExpr::Not(Box::new(PolicyExpr::Var(0)))),
        );
        let tape_contra =
            compile_bounded_egraph(&contradiction, 16).expect("Debe compilar contradicción");
        assert_eq!(tape_contra.ops, vec![FlatOp::ConstBool(false)]);
        assert_eq!(tape_contra.root_reg, 0);
        assert!(!tape_contra.eval_branchless(0b0111_1111));

        // 2. Conmutatividad + Idempotencia + CSE:
        // (Authority & Capability) | (Capability & Authority) -> (Authority & Capability)
        // Solo 3 nodos únicos: LoadTupleBit(0), LoadTupleBit(1), BitAnd(0, 1).
        let cse_expr = PolicyExpr::Or(
            Box::new(PolicyExpr::And(
                Box::new(PolicyExpr::Var(0)),
                Box::new(PolicyExpr::Var(1)),
            )),
            Box::new(PolicyExpr::And(
                Box::new(PolicyExpr::Var(1)),
                Box::new(PolicyExpr::Var(0)),
            )),
        );
        let tape_cse = compile_bounded_egraph(&cse_expr, 3)
            .expect("CSE + conmutatividad debe caber en 3 nodos exactos");
        assert_eq!(tape_cse.ops.len(), 3);
        assert_eq!(
            tape_cse.ops,
            vec![
                FlatOp::LoadTupleBit(0),
                FlatOp::LoadTupleBit(1),
                FlatOp::BitAnd(0, 1),
            ]
        );
        assert_eq!(tape_cse.root_reg, 2);

        // 3. Absorción + Doble Negación:
        // !!Policy & (Policy | Resource) -> Policy (1 único nodo LoadTupleBit(2))
        let absorption = PolicyExpr::And(
            Box::new(PolicyExpr::Not(Box::new(PolicyExpr::Not(Box::new(
                PolicyExpr::Var(2),
            ))))),
            Box::new(PolicyExpr::Or(
                Box::new(PolicyExpr::Var(2)),
                Box::new(PolicyExpr::Var(3)),
            )),
        );
        let tape_abs =
            compile_bounded_egraph(&absorption, 16).expect("Debe simplificar por absorción");
        assert_eq!(tape_abs.ops, vec![FlatOp::LoadTupleBit(2)]);
        assert_eq!(tape_abs.root_reg, 0);
    }

    #[test]
    fn test_egraph_node_budget_fail_closed() {
        // Expresión que requiere 7 nodos únicos:
        // (Authority & Capability) & (Policy & Resource)
        let expr = PolicyExpr::And(
            Box::new(PolicyExpr::And(
                Box::new(PolicyExpr::Var(0)),
                Box::new(PolicyExpr::Var(1)),
            )),
            Box::new(PolicyExpr::And(
                Box::new(PolicyExpr::Var(2)),
                Box::new(PolicyExpr::Var(3)),
            )),
        );

        // Con presupuesto insuficiente (max_nodes = 4), aborta Fail-Closed
        let err_res = compile_bounded_egraph(&expr, 4);
        assert_eq!(err_res, Err("Bounded E-Graph node budget exceeded"));

        // Con presupuesto exacto (max_nodes = 7), compila satisfactoriamente
        let ok_res = compile_bounded_egraph(&expr, 7);
        assert!(ok_res.is_ok());
    }

    #[test]
    fn test_compiled_policy_tape_equivalence() {
        // Política compuesta no trivial sobre las 7 dimensiones (0..=6):
        // ((Authority & Capability & Policy) & (Resource | !Effect)) & (Context | !Epoch)
        // junto con subexpresiones redundantes para ejercitar CSE al mismo tiempo.
        let base_auth = PolicyExpr::And(
            Box::new(PolicyExpr::Var(0)),
            Box::new(PolicyExpr::And(
                Box::new(PolicyExpr::Var(1)),
                Box::new(PolicyExpr::Var(2)),
            )),
        );
        let res_or_not_eff = PolicyExpr::Or(
            Box::new(PolicyExpr::Var(3)),
            Box::new(PolicyExpr::Not(Box::new(PolicyExpr::Var(4)))),
        );
        let ctx_or_not_epoch = PolicyExpr::Or(
            Box::new(PolicyExpr::Var(5)),
            Box::new(PolicyExpr::Not(Box::new(PolicyExpr::Var(6)))),
        );
        let redundant_dup = PolicyExpr::And(
            Box::new(ctx_or_not_epoch.clone()),
            Box::new(base_auth.clone()),
        );

        let full_policy = PolicyExpr::And(
            Box::new(PolicyExpr::And(
                Box::new(base_auth),
                Box::new(res_or_not_eff),
            )),
            Box::new(PolicyExpr::Or(
                Box::new(ctx_or_not_epoch),
                Box::new(redundant_dup),
            )),
        );

        let tape =
            compile_bounded_egraph(&full_policy, 32).expect("Debe compilar política 7-Tupla");

        // Verificación exhaustiva sobre las 2^7 = 128 combinaciones de la máscara de la 7-Tupla
        for mask in 0u8..128u8 {
            let expected = full_policy.eval_recursive(mask);
            let actual = tape.eval_branchless(mask);
            assert_eq!(
                actual, expected,
                "Divergencia en máscara 7-Tupla {:#09b}",
                mask
            );
        }
    }
}

