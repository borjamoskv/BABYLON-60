"""
HYDRA — Hats Finance On-Chain Vault Scanner (C5-REAL)

Direct Web3.py interaction with HATVaults smart contract.
Scans ALL pools, not just hardcoded IDs. Calculates USD values.
Refactored from scripts/hats_telemetry.py + verify_hats_targets.py
"""
import json
from dataclasses import dataclass

import httpx

from cortex_bounty.config import ETH_RPC_URL, HATS_VAULTS_V2, COINGECKO_BASE


@dataclass
class HatsVault:
    """Single Hats Finance vault."""
    pool_id: int = 0
    token_address: str = ""
    token_symbol: str = ""
    token_name: str = ""
    balance_raw: int = 0
    balance_human: float = 0.0
    balance_usd: float = 0.0
    decimals: int = 18
    status: str = ""  # prime, standard, dust


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

ERC20_ABI = json.loads('''[
    {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],
    "stateMutability":"view","type":"function"}
]''')


class HatsOnChainScanner:
    """
    Scans ALL active Hats Finance V2 vaults on-chain.
    Enriches with CoinGecko price data for USD valuation.
    """

    def __init__(self):
        self.w3 = None
        self.price_cache: dict[str, float] = {}

    def _init_web3(self):
        """Lazy init Web3 — only when needed."""
        if self.w3 is None:
            try:
                from web3 import Web3
                self.w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
                if not self.w3.is_connected():
                    raise ConnectionError("Web3 RPC connection failed")
            except ImportError:
                raise ImportError("web3 package required: pip install web3")

    async def _fetch_token_price(self, symbol: str) -> float:
        """Fetch token price from CoinGecko. Returns 0 if not found."""
        symbol_lower = symbol.lower()
        if symbol_lower in self.price_cache:
            return self.price_cache[symbol_lower]

        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "eth": "ethereum", "weth": "ethereum", "usdc": "usd-coin",
            "usdt": "tether", "dai": "dai", "wbtc": "wrapped-bitcoin",
            "angle": "angle-protocol", "insure": "insurace",
            "pal": "paladin", "fin": "definer",
        }

        cg_id = symbol_map.get(symbol_lower, symbol_lower)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{COINGECKO_BASE}/simple/price",
                    params={"ids": cg_id, "vs_currencies": "usd"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    price = data.get(cg_id, {}).get("usd", 0.0)
                    self.price_cache[symbol_lower] = price
                    return price
        except httpx.HTTPError:
            pass

        self.price_cache[symbol_lower] = 0.0
        return 0.0

    def scan_all_vaults(self) -> list[HatsVault]:
        """
        Scan ALL Hats Finance V2 pools on-chain.
        C5-REAL: Every read comes from the Ethereum state trie.
        """
        self._init_web3()

        contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(HATS_VAULTS_V2),
            abi=HAT_VAULTS_ABI
        )

        pool_count = contract.functions.poolLength().call()
        vaults = []

        for i in range(pool_count):
            try:
                info = contract.functions.poolInfo(i).call()
                token_addr = info[0]
                balance = info[6]

                if balance == 0:
                    continue

                # Read token metadata
                token_contract = self.w3.eth.contract(
                    address=token_addr,
                    abi=ERC20_ABI
                )

                try:
                    symbol = token_contract.functions.symbol().call()
                    decimals = token_contract.functions.decimals().call()
                    name = token_contract.functions.name().call()
                except Exception:
                    symbol = "???"
                    decimals = 18
                    name = "Unknown"

                human_balance = balance / (10 ** decimals)

                status = "dust"
                if human_balance > 100_000:
                    status = "prime"
                elif human_balance > 10_000:
                    status = "standard"

                vaults.append(HatsVault(
                    pool_id=i,
                    token_address=token_addr,
                    token_symbol=symbol,
                    token_name=name,
                    balance_raw=balance,
                    balance_human=human_balance,
                    decimals=decimals,
                    status=status,
                ))

            except Exception:
                continue

        return sorted(vaults, key=lambda x: x.balance_human, reverse=True)

    async def scan_with_prices(self) -> list[HatsVault]:
        """Scan vaults and enrich with USD prices."""
        vaults = self.scan_all_vaults()

        for v in vaults:
            if v.status in ("prime", "standard"):
                price = await self._fetch_token_price(v.token_symbol)
                v.balance_usd = v.balance_human * price

        return vaults

    def scan_specific_pools(self, pool_ids: list[int]) -> list[HatsVault]:
        """Scan specific pool IDs only."""
        self._init_web3()

        contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(HATS_VAULTS_V2),
            abi=HAT_VAULTS_ABI
        )

        vaults = []
        for i in pool_ids:
            try:
                info = contract.functions.poolInfo(i).call()
                token_addr = info[0]
                balance = info[6]

                token_contract = self.w3.eth.contract(
                    address=token_addr,
                    abi=ERC20_ABI
                )

                symbol = token_contract.functions.symbol().call()
                decimals = token_contract.functions.decimals().call()
                name = token_contract.functions.name().call()

                human_balance = balance / (10 ** decimals)

                status = "prime" if human_balance > 100_000 else ("standard" if human_balance > 10_000 else "dust")

                vaults.append(HatsVault(
                    pool_id=i,
                    token_address=token_addr,
                    token_symbol=symbol,
                    token_name=name,
                    balance_raw=balance,
                    balance_human=human_balance,
                    decimals=decimals,
                    status=status,
                ))
            except Exception as e:
                print(f"  [Pool {i}] Error: {e}")

        return vaults


def _test():
    """Quick test against live chain."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    scanner = HatsOnChainScanner()

    console.print("[bold]HYDRA · Hats On-Chain Scan[/bold]", style="blue")
    try:
        vaults = scanner.scan_all_vaults()
        console.print(f"  Found {len(vaults)} non-empty vaults")

        if vaults:
            table = Table(title="Hats Finance Vaults (Non-Zero)")
            table.add_column("Pool", justify="right", style="dim")
            table.add_column("Token", style="cyan")
            table.add_column("Name")
            table.add_column("Balance", justify="right", style="green")
            table.add_column("Status", justify="center")

            for v in vaults[:20]:
                style = "bold green" if v.status == "prime" else ("yellow" if v.status == "standard" else "dim")
                table.add_row(
                    str(v.pool_id),
                    v.token_symbol,
                    v.token_name[:25],
                    f"{v.balance_human:,.2f}",
                    v.status.upper(),
                    style=style,
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        console.print("  Install web3: pip install web3")


if __name__ == "__main__":
    _test()
