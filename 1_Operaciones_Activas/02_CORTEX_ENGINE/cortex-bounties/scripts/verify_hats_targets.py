import json
from web3 import Web3

# CORTEX Telemetry: Hats Finance V2 Vault Monitor (Specific Strike Targeting)
# Status: C5-REAL | Exergy: High
# RPC: Public Node (Stability Focus)

RPC_URL = "https://ethereum-rpc.publicnode.com"
HAT_VAULTS_ADDRESS = "0x571f39d351513146248AcafA9D0509319A327C4D"

# ABI for HATVaults (Master/Registry)
HAT_VAULTS_ABI = json.loads('''[
    {"inputs":[],"name":"poolLength","outputs":[
        {"internalType":"uint256","name":"","type":"uint256"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],
    "name":"poolInfo","outputs":[
        {"internalType":"address","name":"lpToken","type":"address"},
        {"internalType":"uint256","name":"allocPoint","type":"uint256"},
        {"internalType":"uint256","name":"lastRewardBlock","type":"uint256"},
        {"internalType":"uint256","name":"rewardPerShare","type":"uint256"},
        {"internalType":"uint256","name":"totalUsersAmount","type":"uint256"},
        {"internalType":"uint256","name":"lastProcessedTotalAllocPoint","type":"uint256"},
        {"internalType":"uint256","name":"balance","type":"uint256"}
    ],"stateMutability":"view","type":"function"}
]''')

# Minimal ERC20 ABI
ERC20_ABI = json.loads('''[
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"}
]''')


def verify_target_pools(pool_ids):
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("[-] Fallo de conexión al RPC.")
        return

    contract = w3.eth.contract(address=HAT_VAULTS_ADDRESS, abi=HAT_VAULTS_ABI)

    print(f"[+] Verificando Pools de Hats Finance: {pool_ids}")

    for i in pool_ids:
        try:
            info = contract.functions.poolInfo(i).call()
            token_addr = info[0]
            balance = info[6]

            t_contract = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
            symbol = t_contract.functions.symbol().call()
            decimals = t_contract.functions.decimals().call()
            name = t_contract.functions.name().call()
            
            readable_balance = balance / (10 ** decimals)
            
            print(f"    [Pool {i}] Asset: {symbol} | {name}")
            print(f"              Address: {token_addr}")
            print(f"              Balance: {readable_balance:,.2f} {symbol}")
            
            if readable_balance > 10000:
                print("              [STATE] PRIME")
            else:
                print("              [STATE] STANDARD")

        except Exception as e:
            print(f"    [Pool {i}] Error: {e}")


if __name__ == "__main__":
    verify_target_pools([19, 20, 22, 23, 25])
