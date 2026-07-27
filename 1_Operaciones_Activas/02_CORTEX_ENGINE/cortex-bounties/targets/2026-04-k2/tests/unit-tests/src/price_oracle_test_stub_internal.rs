#![cfg(test)]

use k2_shared::{
    Asset, PriceData, TEST_PRICE_BTC, TEST_PRICE_DEFAULT, TEST_PRICE_ETH, TEST_PRICE_USD,
};
use soroban_sdk::{contract, contractimpl, Env, Symbol};

#[contract]
pub struct ReflectorStub;

#[contractimpl]
impl ReflectorStub {
    pub fn lastprice(env: Env, asset: Asset) -> Option<PriceData> {
        let price = match asset {
            Asset::Stellar(_) => TEST_PRICE_DEFAULT,
            Asset::Other(symbol) => {
                if symbol == Symbol::new(&env, "BTC") {
                    TEST_PRICE_BTC
                } else if symbol == Symbol::new(&env, "ETH") {
                    TEST_PRICE_ETH
                } else if symbol == Symbol::new(&env, "USD") {
                    TEST_PRICE_USD
                } else {
                    TEST_PRICE_DEFAULT
                }
            }
        };

        Some(PriceData {
            price,
            timestamp: env.ledger().timestamp(),
        })
    }

    pub fn twap(env: Env, asset: Asset, _periods: u32) -> Option<i128> {
        let price = match asset {
            Asset::Stellar(_) => TEST_PRICE_DEFAULT as i128,
            Asset::Other(symbol) => {
                if symbol == Symbol::new(&env, "BTC") {
                    TEST_PRICE_BTC as i128
                } else if symbol == Symbol::new(&env, "ETH") {
                    TEST_PRICE_ETH as i128
                } else if symbol == Symbol::new(&env, "USD") {
                    TEST_PRICE_USD as i128
                } else {
                    TEST_PRICE_DEFAULT as i128
                }
            }
        };

        Some(price)
    }

    pub fn decimals(_env: Env) -> u32 {
        14
    }

    pub fn base(env: Env) -> Asset {
        Asset::Other(Symbol::new(&env, "USD"))
    }
}
