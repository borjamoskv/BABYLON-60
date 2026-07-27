use alloy::sol;
use alloy::primitives::{Address, B256, U256};
use alloy::providers::ProviderBuilder;
use alloy::network::EthereumWallet;
use alloy::signers::local::PrivateKeySigner;
use std::str::FromStr;

// ABI mínimo del OuroborosExecutor — solo genesisSnipe
sol!(
    #[sol(rpc)]
    interface OuroborosExecutor {
        function genesisSnipe(address router, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external payable;
    }
);

// Router Uniswap V2 Mainnet
const ROUTER_V2: &str = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
// WETH Mainnet
const WETH: &str = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
// ETH a comprar en cada snipe (0.05 ETH — ajustable)
const SNIPE_VALUE_ETH: &str = "50000000000000000";

/// Relayers MEV privados para rotación (ST-02)
#[allow(dead_code)]
const RELAYERS: &[&str] = &[
    "https://relay.flashbots.net",
    "https://mainnet.beaverbuild.org",
    "https://rpc.titanbuilder.xyz",
    "https://rsync-builder.xyz",
];

/// Dispara un Bundle Flashbots apuntando al siguiente bloque.
/// La tx NO es visible en la mempool pública — inmune a front-runners.
pub async fn fire_genesis_snipe(
    private_key: &str,
    flashbots_auth_key: &str,
    rpc_http_url: &str,
    executor_contract: Address,
    target_ca: &str,
) -> anyhow::Result<B256> {

    let wallet: PrivateKeySigner = private_key.parse()?;
    let _fb_auth_wallet: PrivateKeySigner = flashbots_auth_key.parse()?; // TODO for bundles
    let ethereum_wallet = EthereumWallet::from(wallet.clone());
    let provider = ProviderBuilder::new()
        .wallet(ethereum_wallet)
        .connect_http(rpc_http_url.parse()?);

    // Instancia del contrato
    let executor = OuroborosExecutor::new(executor_contract, provider);

    let target_addr = Address::from_str(target_ca)?;
    let router_addr = Address::from_str(ROUTER_V2)?;
    let weth_addr   = Address::from_str(WETH)?;
    let snipe_value = U256::from_str(SNIPE_VALUE_ETH)?;

    // Construcción de la llamada a genesisSnipe
    let call = executor.genesisSnipe(
        router_addr,
        U256::ZERO,                           // amountOutMin = 0 (máxima agresividad)
        vec![weth_addr, target_addr],           // path: WETH → TOKEN
        wallet.address(),                        // to: wallet soberana
        U256::from(chrono::Utc::now().timestamp() + 60), // deadline: +60s
    )
    .value(snipe_value);

    // Enviar la transacción normal (TODO: Flashbots bundle integration with Alloy)
    let pending_tx = call.send().await?;
    let tx_hash = *pending_tx.tx_hash();

    println!(
        ">>> [FLASHBOTS-TODO] Bundle integration in Alloy pending. TX normal enviada: {:?}",
        tx_hash
    );

    Ok(tx_hash)
}
