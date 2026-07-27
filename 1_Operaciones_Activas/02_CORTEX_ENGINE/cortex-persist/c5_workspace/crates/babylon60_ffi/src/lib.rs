use babylon60_chaos::parse_ir;
use babylon60_rs::{Babylon60Kernel, KernelTrait};

#[derive(Clone, Debug)]
pub struct BoundaryKernel {
    inner: Babylon60Kernel,
}

impl BoundaryKernel {
    pub fn new() -> Self {
        Self {
            inner: Babylon60Kernel::new(),
        }
    }

    pub fn submit_ir(&mut self, ir: &str) -> String {
        if ir.contains('\0') {
            return "REJECTED".to_string();
        }
        let event = parse_ir(ir).unwrap_or(babylon60_types::Event::Unknown(ir.to_string()));
        match self.inner.apply_event(event) {
            babylon60_types::KernelResult::Accepted => "ACCEPTED".to_string(),
            babylon60_types::KernelResult::Rejected => "REJECTED".to_string(),
            babylon60_types::KernelResult::Collapse { reason } => format!("HARD_FAIL:{:?}", reason),
        }
    }

    pub fn state_hash(&self) -> String {
        babylon60_types::hex32(&self.inner.state_hash())
    }

    pub fn ledger_root(&self) -> String {
        babylon60_types::hex32(&self.inner.ledger_root())
    }
}
