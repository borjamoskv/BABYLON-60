use soroban_sdk::{contracttype, symbol_short, Address, Env, Symbol};

/// Event symbols for treasury contract events.
///
/// Events are published to enable off-chain monitoring and indexing of treasury
/// operations. Each event includes relevant context for audit trails.
const EVENT_DEPOSIT: Symbol = symbol_short!("deposit");
const EVENT_WITHDRAW: Symbol = symbol_short!("withdraw");
const EVENT_INIT: Symbol = symbol_short!("init");

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DepositEventData {
    pub asset: Address,
    pub amount: u128,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WithdrawEventData {
    pub asset: Address,
    pub amount: u128,
    pub to: Address,
}

/// Publish a deposit event.
///
/// Event structure: (EVENT_DEPOSIT, from) -> DepositEventData
/// This allows off-chain systems to track which addresses are depositing
/// which assets and in what amounts.
pub fn publish_deposit(env: &Env, asset: Address, amount: u128, from: Address) {
    env.events().publish(
        (EVENT_DEPOSIT, from),
        DepositEventData { asset, amount },
    );
}

/// Publish a withdrawal event.
///
/// Event structure: (EVENT_WITHDRAW, admin) -> WithdrawEventData
/// Includes the admin address that authorized the withdrawal for accountability.
pub fn publish_withdraw(env: &Env, asset: Address, amount: u128, to: Address, admin: Address) {
    env.events().publish(
        (EVENT_WITHDRAW, admin),
        WithdrawEventData { asset, amount, to },
    );
}

/// Publish an initialization event.
///
/// Event structure: (EVENT_INIT, "treasury") -> admin
/// Published once when the contract is initialized to establish the admin address.
pub fn publish_init(env: &Env, admin: Address) {
    env.events().publish(
        (EVENT_INIT, symbol_short!("treasury")),
        admin,
    );
}

