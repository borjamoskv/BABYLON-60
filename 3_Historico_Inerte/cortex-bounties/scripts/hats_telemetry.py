import json
from web3 import Web3

# CORTEX Telemetry: Hats Finance V2 Vault Monitor
# Status: C5-REAL | Exergy: High
# RPC: 1RPC (Public / Stability Focus)

RPC_URL = "https://1rpc.io/eth"
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
    "stateMutability":"view","type":"function"}
]''')


def monitor_vaults():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("[-] Fallo de conexión al RPC.")
        return

    contract = w3.eth.contract(address=HAT_VAULTS_ADDRESS, abi=HAT_VAULTS_ABI)

    try:
        count = contract.functions.poolLength().call()
        print(f"[+] Hats Finance V2 Detectado. Pools totales: {count}")

        # Escanear las últimas 10 pools
        for i in range(max(0, count - 10), count):
            info = contract.functions.poolInfo(i).call()
            # info structure: [lpToken, allocPoint, ..., balance]
            token_addr = info[0]
            balance = info[6]

            try:
                t_contract = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
                symbol = t_contract.functions.symbol().call()
                decimals = t_contract.functions.decimals().call()
                
                readable_balance = balance / (10 ** decimals)
                
                print(f"    [Pool {i}] Asset: {symbol} ({token_addr})")
                print(f"              Balance: {readable_balance:.2f} {symbol}")

                if readable_balance > 10000:
                    print("              [!!!] OBJETIVO PRIME DETECTADO.")
            except Exception as e_inner:
                print(f"    [Pool {i}] Error: {e_inner}")

    except Exception as e:
        print(f"[-] Error en telemetría: {e}")


if __name__ == "__main__":
    monitor_vaults()
