use alloy::rpc::types::eth::Transaction;
fn main() {
    let tx: Transaction = unimplemented!();
    let from = tx.inner.signer();
    let to = tx.inner.to();
    let val = tx.inner.value();
    let input = tx.inner.input();
}
