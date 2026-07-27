use alloy::rpc::types::eth::Transaction;
use alloy::consensus::Transaction as _;

fn main() {
    let tx: Transaction = unimplemented!();
    let to: Option<alloy::primitives::Address> = tx.inner.to();
}
