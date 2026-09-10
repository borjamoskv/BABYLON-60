use std::collections::HashMap;
use serde::{Deserialize, Serialize};

use crate::ast::*;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Gate {
    Constant { out: String, value: u64 },
    Add { out: String, lhs: String, rhs: String },
    Sub { out: String, lhs: String, rhs: String },
    Mul { out: String, lhs: String, rhs: String },
    AssertEq { lhs: String, rhs: String },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompiledCircuit {
    pub name: String,
    pub public_inputs: Vec<String>,
    pub private_inputs: Vec<String>,
    pub gates: Vec<Gate>,
}

#[derive(Default)]
pub struct Compiler {
    var_counter: usize,
    env: HashMap<String, String>,
    gates: Vec<Gate>,
}

impl Compiler {
    pub fn new() -> Self {
        Self::default()
    }

    fn new_var(&mut self) -> String {
        let name = format!("v{}", self.var_counter);
        self.var_counter += 1;
        name
    }

    pub fn compile(mut self, circuit: Circuit) -> CompiledCircuit {
        let mut public_inputs = Vec::new();
        let mut private_inputs = Vec::new();

        for param in circuit.params {
            match param.visibility {
                Visibility::Public => public_inputs.push(param.name.clone()),
                Visibility::Private => private_inputs.push(param.name.clone()),
            }
            self.env.insert(param.name.clone(), param.name.clone());
        }

        for stmt in circuit.main_fn.statements {
            match stmt {
                Statement::Let { name, expr } => {
                    let res_var = self.compile_expr(&expr);
                    self.env.insert(name, res_var);
                }
                Statement::Assert { expr } => {
                    if let Expression::BinaryOp { op: Op::Eq, lhs, rhs } = expr {
                        let l_var = self.compile_expr(&lhs);
                        let r_var = self.compile_expr(&rhs);
                        self.gates.push(Gate::AssertEq { lhs: l_var, rhs: r_var });
                    } else {
                        panic!("Assert expression must be an equality (==)");
                    }
                }
            }
        }

        CompiledCircuit {
            name: circuit.name,
            public_inputs,
            private_inputs,
            gates: self.gates,
        }
    }

    fn compile_expr(&mut self, expr: &Expression) -> String {
        match expr {
            Expression::Identifier(name) => {
                self.env.get(name).cloned().unwrap_or_else(|| panic!("Undefined variable: {}", name))
            }
            Expression::Literal(val) => {
                let out = self.new_var();
                self.gates.push(Gate::Constant { out: out.clone(), value: *val });
                out
            }
            Expression::BinaryOp { op, lhs, rhs } => {
                let l_var = self.compile_expr(lhs);
                let r_var = self.compile_expr(rhs);
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
    code.push('\n');
    
    // Evaluating gates
    for gate in &circuit.gates {
        match gate {
            Gate::Constant { out, value } => {
                code.push_str(&format!("        let var_{} = cs.new_witness_variable(|| Ok(F::from({}u64)))?;\n", out, value));
                code.push_str(&format!("        cs.enforce_constraint(LinearCombination::from(Variable::One), LinearCombination::from(var_{}), LinearCombination::from((F::from({}u64), Variable::One)))?;\n", out, value));
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
