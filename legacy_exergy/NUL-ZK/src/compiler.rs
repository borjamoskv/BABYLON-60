use crate::ast::*;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Gate {
    Add { out: String, lhs: String, rhs: String },
    Sub { out: String, lhs: String, rhs: String },
    Mul { out: String, lhs: String, rhs: String },
    AssertEq { lhs: String, rhs: String },
    Constant { out: String, value: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompiledCircuit {
    pub name: String,
    pub public_inputs: Vec<String>,
    pub private_inputs: Vec<String>,
    pub gates: Vec<Gate>,
}

pub struct Compiler {
    var_count: usize,
    gates: Vec<Gate>,
    env: HashMap<String, String>,
}

impl Compiler {
    pub fn new() -> Self {
        Self {
            var_count: 0,
            gates: Vec::new(),
            env: HashMap::new(),
        }
    }

    fn new_var(&mut self) -> String {
        let v = format!("v{}", self.var_count);
        self.var_count += 1;
        v
    }

    pub fn compile(mut self, circuit: Circuit) -> CompiledCircuit {
        let mut public_inputs = Vec::new();
        let mut private_inputs = Vec::new();

        for param in circuit.params {
            self.env.insert(param.ident.clone(), param.ident.clone());
            match param.visibility {
                Visibility::Public => public_inputs.push(param.ident),
                Visibility::Private => private_inputs.push(param.ident),
            }
        }

        for stmt in circuit.body {
            self.compile_stmt(stmt);
        }

        // Optimization Pass: Constant Folding & Dead Code Elimination
        let optimized_gates = self.optimize_constraints(self.gates.clone());

        CompiledCircuit {
            name: circuit.name,
            public_inputs,
            private_inputs,
            gates: optimized_gates,
        }
    }

    fn optimize_constraints(&self, gates: Vec<Gate>) -> Vec<Gate> {
        let mut constants: HashMap<String, u64> = HashMap::new();
        let mut optimized = Vec::new();

        // Pass 1: Constant Folding
        for gate in gates {
            match &gate {
                Gate::Constant { out, value } => {
                    if let Ok(v) = value.parse::<u64>() {
                        constants.insert(out.clone(), v);
                    }
                    optimized.push(gate);
                }
                Gate::Add { out, lhs, rhs } => {
                    if let (Some(l), Some(r)) = (constants.get(lhs), constants.get(rhs)) {
                        let sum = l.wrapping_add(*r);
                        constants.insert(out.clone(), sum);
                        optimized.push(Gate::Constant { out: out.clone(), value: sum.to_string() });
                    } else {
                        optimized.push(gate);
                    }
                }
                Gate::Sub { out, lhs, rhs } => {
                    if let (Some(l), Some(r)) = (constants.get(lhs), constants.get(rhs)) {
                        let sub = l.wrapping_sub(*r);
                        constants.insert(out.clone(), sub);
                        optimized.push(Gate::Constant { out: out.clone(), value: sub.to_string() });
                    } else {
                        optimized.push(gate);
                    }
                }
                Gate::Mul { out, lhs, rhs } => {
                    if let (Some(l), Some(r)) = (constants.get(lhs), constants.get(rhs)) {
                        let mul = l.wrapping_mul(*r);
                        constants.insert(out.clone(), mul);
                        optimized.push(Gate::Constant { out: out.clone(), value: mul.to_string() });
                    } else {
                        optimized.push(gate);
                    }
                }
                Gate::AssertEq { lhs, rhs } => {
                    if let (Some(l), Some(r)) = (constants.get(lhs), constants.get(rhs)) {
                        if l != r {
                            panic!("Compile-time assertion failed: {} != {}", l, r);
                        }
                        // If trivially true, remove the gate entirely (Zero Anergy)
                    } else {
                        optimized.push(gate);
                    }
                }
            }
        }

        // Pass 2: Dead Code Elimination (DCE)
        // Backwards pass to find used variables
        let mut used = HashSet::new();
        for gate in optimized.iter().rev() {
            match gate {
                Gate::AssertEq { lhs, rhs } => {
                    used.insert(lhs.clone());
                    used.insert(rhs.clone());
                }
                Gate::Add { out, lhs, rhs } | Gate::Sub { out, lhs, rhs } | Gate::Mul { out, lhs, rhs } => {
                    if used.contains(out) {
                        used.insert(lhs.clone());
                        used.insert(rhs.clone());
                    }
                }
                Gate::Constant { out, .. } => {
                    // Do not mark constants used implicitly
                    let _ = out; 
                }
            }
        }

        // Keep only variables that are used
        let mut final_gates = Vec::new();
        for gate in optimized {
            match &gate {
                Gate::Add { out, .. } | Gate::Sub { out, .. } | Gate::Mul { out, .. } | Gate::Constant { out, .. } => {
                    if used.contains(out) {
                        final_gates.push(gate);
                    }
                }
                Gate::AssertEq { .. } => {
                    final_gates.push(gate);
                }
            }
        }

        final_gates
    }

    fn compile_stmt(&mut self, stmt: Stmt) {
        match stmt {
            Stmt::Let { ident, expr } => {
                let out = self.compile_expr(expr);
                self.env.insert(ident, out);
            }
            Stmt::Assert { expr } => {
                match expr {
                    Expr::BinOp { lhs, op: Op::Eq, rhs } => {
                        let l_var = self.compile_expr(*lhs);
                        let r_var = self.compile_expr(*rhs);
                        self.gates.push(Gate::AssertEq { lhs: l_var, rhs: r_var });
                    }
                    _ => {
                        let out = self.compile_expr(expr);
                        let one = self.new_var();
                        self.gates.push(Gate::Constant { out: one.clone(), value: "1".to_string() });
                        self.gates.push(Gate::AssertEq { lhs: out, rhs: one });
                    }
                }
            }
        }
    }

    fn compile_expr(&mut self, expr: Expr) -> String {
        match expr {
            Expr::Number(n) => {
                let out = self.new_var();
                self.gates.push(Gate::Constant { out: out.clone(), value: n });
                out
            }
            Expr::Ident(id) => {
                self.env.get(&id).cloned().unwrap_or_else(|| panic!("Unknown variable: {}", id))
            }
            Expr::BinOp { lhs, op, rhs } => {
                let l_var = self.compile_expr(*lhs);
                let r_var = self.compile_expr(*rhs);
                let out = self.new_var();
                
                let gate = match op {
                    Op::Add => Gate::Add { out: out.clone(), lhs: l_var, rhs: r_var },
                    Op::Sub => Gate::Sub { out: out.clone(), lhs: l_var, rhs: r_var },
                    Op::Mul => Gate::Mul { out: out.clone(), lhs: l_var, rhs: r_var },
                    Op::Eq => panic!("Eq operator is only allowed in asserts"),
                };
                
                self.gates.push(gate);
                out
            }
        }
    }
}

pub fn generate_arkworks_rust(circuit: &CompiledCircuit) -> String {
    let mut code = String::new();
    
    code.push_str("use ark_ff::Field;\n");
    code.push_str("use ark_relations::r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError, Variable, LinearCombination};\n\n");
    
    // Struct definition
    code.push_str(&format!("#[derive(Clone)]\npub struct {}<F: Field> {{\n", circuit.name));
    for pub_in in &circuit.public_inputs {
        code.push_str(&format!("    pub {}: Option<F>,\n", pub_in));
    }
    for priv_in in &circuit.private_inputs {
        code.push_str(&format!("    pub {}: Option<F>,\n", priv_in));
    }
    code.push_str("}\n\n");
    
    // Implementation of ConstraintSynthesizer
    code.push_str(&format!("impl<F: Field> ConstraintSynthesizer<F> for {}<F> {{\n", circuit.name));
    code.push_str("    fn generate_constraints(self, cs: ConstraintSystemRef<F>) -> Result<(), SynthesisError> {\n");
    
    // Allocating inputs
    for pub_in in &circuit.public_inputs {
        code.push_str(&format!("        let var_{} = cs.new_input_variable(|| self.{}.ok_or(SynthesisError::AssignmentMissing))?;\n", pub_in, pub_in));
    }
    for priv_in in &circuit.private_inputs {
        code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| self.{}.ok_or(SynthesisError::AssignmentMissing))?;\n", priv_in, priv_in));
    }
    code.push_str("\n");
    
    // Evaluating gates with closures (Proper Arkworks Pattern)
    for gate in &circuit.gates {
        match gate {
            Gate::Constant { out, value } => {
                code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| Ok(F::from({}u64)))?;\n", out, value));
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(Variable::One), LinearCombination::from(var_{}), LinearCombination::from(F::from({}u64)))?;\n", out, value));
            }
            Gate::Add { out, lhs, rhs } => {
                code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| {{\n", out));
                code.push_str(&format!("            let l = cs.assigned_value(var_{}).unwrap_or_default();\n", lhs));
                code.push_str(&format!("            let r = cs.assigned_value(var_{}).unwrap_or_default();\n", rhs));
                code.push_str("            Ok(l + r)\n");
                code.push_str("        })?;\n");
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(var_{}) + LinearCombination::from(var_{}), LinearCombination::from(Variable::One), LinearCombination::from(var_{}))?;\n", lhs, rhs, out));
            }
            Gate::Sub { out, lhs, rhs } => {
                code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| {{\n", out));
                code.push_str(&format!("            let l = cs.assigned_value(var_{}).unwrap_or_default();\n", lhs));
                code.push_str(&format!("            let r = cs.assigned_value(var_{}).unwrap_or_default();\n", rhs));
                code.push_str("            Ok(l - r)\n");
                code.push_str("        })?;\n");
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(var_{}) - LinearCombination::from(var_{}), LinearCombination::from(Variable::One), LinearCombination::from(var_{}))?;\n", lhs, rhs, out));
            }
            Gate::Mul { out, lhs, rhs } => {
                code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| {{\n", out));
                code.push_str(&format!("            let l = cs.assigned_value(var_{}).unwrap_or_default();\n", lhs));
                code.push_str(&format!("            let r = cs.assigned_value(var_{}).unwrap_or_default();\n", rhs));
                code.push_str("            Ok(l * r)\n");
                code.push_str("        })?;\n");
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(var_{}), LinearCombination::from(var_{}), LinearCombination::from(var_{}))?;\n", lhs, rhs, out));
            }
            Gate::AssertEq { lhs, rhs } => {
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(var_{}), LinearCombination::from(Variable::One), LinearCombination::from(var_{}))?;\n", lhs, rhs));
            }
        }
    }
    
    code.push_str("        Ok(())\n");
    code.push_str("    }\n");
    code.push_str("}\n");
    
    code
}
