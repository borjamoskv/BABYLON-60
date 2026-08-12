use ark_ff::Field;
use ark_relations::r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError, Variable, LinearCombination};

#[derive(Clone)]
pub struct Multiplier<F: Field> {
    pub c: Option<F>,
    pub a: Option<F>,
    pub b: Option<F>,
}

impl<F: Field> ConstraintSynthesizer<F> for Multiplier<F> {
    fn generate_constraints(self, cs: ConstraintSystemRef<F>) -> Result<(), SynthesisError> {
        let var_c = cs.new_input_variable(|| self.c.ok_or(SynthesisError::AssignmentMissing))?;
        let var_a = cs.new_witness_variable(|| self.a.ok_or(SynthesisError::AssignmentMissing))?;
        let var_b = cs.new_witness_variable(|| self.b.ok_or(SynthesisError::AssignmentMissing))?;

        let val_l = cs.lc_val(LinearCombination::from(var_a));
        let val_r = cs.lc_val(LinearCombination::from(var_b));
        let val_v0 = val_l * val_r;
        let var_v0 = cs.new_witness_variable(|| Ok(val_v0))?;
        cs.enforce_constraint(LinearCombination::from(var_a), LinearCombination::from(var_b), LinearCombination::from(var_v0))?;
        cs.enforce_constraint(LinearCombination::from(var_v0), LinearCombination::from(Variable::One), LinearCombination::from(var_c))?;
        Ok(())
    }
}
