# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty Feed Ingestion Transducer
"""bounty_feed_transducer.py - Ingestión de feeds de vulnerabilidad y bounties.

Convierte eventos JSON y APIs públicas (GitHub Security Advisories, Code4rena,
Huntr, Immunefi) en tramas binarias compactas B60IPC (CBOR puro) sin fricción
de I/O en la ruta caliente, cumpliendo la invariante INV_C5_SHM.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import logging
import os
import shutil
import subprocess
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Sequence, cast

from babylon60.bft.exergy_binary_ipc import pack_agent_message

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger("babylon60.transducers.bounty")


def _get_api_headers() -> Dict[str, str]:
    """Genera cabeceras HTTP con autenticación opcional de entorno o gh auth token para evitar 403."""
    headers = {"User-Agent": "BABYLON-60-Bounty-Transducer/1.0", "Accept": "application/json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        gh_bin = shutil.which("gh")
        if gh_bin:
            try:
                res = subprocess.run(
                    [gh_bin, "auth", "token"], capture_output=True, text=True, timeout=2.0, check=False
                )
                if res.returncode == 0 and res.stdout.strip():
                    token = res.stdout.strip()
            except Exception:  # noqa: BLE001
                pass
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class BountyDomain(str, Enum):
    """Dominios canónicos para clasificación de superficies de ataque."""

    DOMAIN_EVM = "DOMAIN_EVM"
    DOMAIN_NATIVE = "DOMAIN_NATIVE"
    DOMAIN_AI = "DOMAIN_AI"
    DOMAIN_GENERAL = "DOMAIN_GENERAL"


@dataclass(frozen=True)
class BountyAdvisory:
    """Representación normalizada y canónica de una oportunidad de auditoría."""

    advisory_id: str
    source: str
    title: str
    target_ecosystem: str
    domain: BountyDomain
    severity: str
    reference_url: str
    payload_summary: str
    raw_fingerprint: str

    def to_dict(self) -> Dict[str, object]:
        """Serializa la entidad a diccionario compatible con CBOR/B60IPC."""
        d = asdict(self)
        d["domain"] = self.domain.value
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BountyAdvisory:
        """Reconstruye una instancia desde un mapeo tipado."""
        return cls(
            advisory_id=str(data.get("advisory_id", "")),
            source=str(data.get("source", "")),
            title=str(data.get("title", "")),
            target_ecosystem=str(data.get("target_ecosystem", "")),
            domain=BountyDomain(str(data.get("domain", BountyDomain.DOMAIN_GENERAL.value))),
            severity=str(data.get("severity", "unknown")),
            reference_url=str(data.get("reference_url", "")),
            payload_summary=str(data.get("payload_summary", "")),
            raw_fingerprint=str(data.get("raw_fingerprint", "")),
        )


class ExergyFilter:
    """Filtro de exergía termodinámica con ventana LRU acotada O(1).

    Purga eventos redundantes o duplicados antes de alocar tramas binarias.
    """

    def __init__(self, capacity: int = 10_000) -> None:
        self._capacity = capacity
        self._seen: OrderedDict[str, None] = OrderedDict()

    def is_novel(self, fingerprint: str) -> bool:
        """Determina si un fingerprint es nuevo o debe ser disipado térmicamente."""
        if fingerprint in self._seen:
            self._seen.move_to_end(fingerprint)
            return False

        self._seen[fingerprint] = None
        if len(self._seen) > self._capacity:
            self._seen.popitem(last=False)
        return True

    @staticmethod
    def classify_domain(title: str, text: str, ecosystem: str) -> BountyDomain:
        """Clasifica el dominio ontológico en base a descriptores de superficie."""
        combined = f"{title} {text} {ecosystem}".lower()

        # Dominio EVM / DeFi (Uniswap hooks, solidity, reentrancy, etc.)
        evm_markers = (
            "solidity",
            "evm",
            "uniswap",
            "reentrancy",
            "smart contract",
            "erc20",
            "erc721",
            "eip1153",
            "transient storage",
            "flash loan",
            "defi",
            "foundry",
            "hardhat",
        )
        if any(m in combined for m in evm_markers):
            return BountyDomain.DOMAIN_EVM

        # Dominio Nativo / Silicio (WebKit, JSC, V8, memory corruption, C-ABI)
        native_markers = (
            "webkit",
            "jscore",
            "javascriptcore",
            "v8",
            "gigacage",
            "isomalloc",
            "use-after-free",
            "out-of-bounds",
            "heap overflow",
            "buffer overflow",
            "kernel",
            "memory corruption",
            "arm64",
        )
        if any(m in combined for m in native_markers):
            return BountyDomain.DOMAIN_NATIVE

        # Dominio AI / MLOps (PyTorch, prompt injection, RLHF, safe tensors)
        ai_markers = (
            "prompt injection",
            "pytorch",
            "langchain",
            "huggingface",
            "safetensors",
            "jailbreak",
            "rlhf",
            "llm",
            "transformer",
            "model inversion",
            "tensor",
        )
        if any(m in combined for m in ai_markers):
            return BountyDomain.DOMAIN_AI

        return BountyDomain.DOMAIN_GENERAL


class BountyFeedTransducer:
    """Transductor soberano de feeds a frames de memoria IPC B60IPC."""

    def __init__(self, filter_capacity: int = 10_000) -> None:
        self._filter = ExergyFilter(capacity=filter_capacity)
        self._lamport_clock = 0

    def normalize_github_advisory(self, raw: Mapping[str, object]) -> Optional[BountyAdvisory]:
        """Convierte una entrada de GitHub Security Advisory en BountyAdvisory."""
        ghsa_id = str(raw.get("ghsa_id", ""))
        summary = str(raw.get("summary", ""))
        description = str(raw.get("description", ""))
        severity = str(raw.get("severity", "medium"))
        html_url = str(raw.get("html_url", ""))

        # Extraer ecosistema de paquete si existe
        ecosystem = ""
        vulnerabilities = raw.get("vulnerabilities")
        if isinstance(vulnerabilities, list) and len(vulnerabilities) > 0:
            first = vulnerabilities[0]
            if isinstance(first, dict):
                package = first.get("package")
                if isinstance(package, dict):
                    ecosystem = str(package.get("ecosystem", ""))

        content_for_hash = f"{ghsa_id}:{summary}:{ecosystem}"
        fingerprint = hashlib.sha3_256(content_for_hash.encode("utf-8")).hexdigest()

        if not self._filter.is_novel(fingerprint):
            return None

        domain = self._filter.classify_domain(summary, description, ecosystem)

        return BountyAdvisory(
            advisory_id=ghsa_id,
            source="github_advisories",
            title=summary.strip(),
            target_ecosystem=ecosystem,
            domain=domain,
            severity=severity,
            reference_url=html_url,
            payload_summary=description[:512],
            raw_fingerprint=fingerprint,
        )

    def normalize_contest_repository(
        self, repo_name: str, repo_url: str, description: str, source: str = "code4rena"
    ) -> Optional[BountyAdvisory]:
        """Normaliza un repositorio público de concurso de auditoría."""
        fingerprint = hashlib.sha3_256(f"{source}:{repo_name}".encode("utf-8")).hexdigest()

        if not self._filter.is_novel(fingerprint):
            return None

        domain = self._filter.classify_domain(repo_name, description, "crypto/smart-contracts")

        return BountyAdvisory(
            advisory_id=f"{source.upper()}-{repo_name}",
            source=source,
            title=f"Audit Contest: {repo_name}",
            target_ecosystem="solidity/evm",
            domain=domain,
            severity="high",
            reference_url=repo_url,
            payload_summary=description[:512] if description else repo_name,
            raw_fingerprint=fingerprint,
        )

    def pack_advisory_to_b60ipc(self, advisory: BountyAdvisory, recipient: str = "bounty_ring_dispatcher") -> bytes:
        """Empaqueta el advisory en una trama binaria compacta B60IPC."""
        self._lamport_clock += 1
        return pack_agent_message(
            sender="bounty_feed_transducer",
            recipient=recipient,
            payload=advisory.to_dict(),
            lamport_t=self._lamport_clock,
        )

    def ingest_raw_advisories(
        self, raw_items: Sequence[Mapping[str, object]], recipient: str = "bounty_ring_dispatcher"
    ) -> List[bytes]:
        """Procesa una secuencia de registros crudos y genera tramas B60IPC filtradas."""
        frames: List[bytes] = []
        for item in raw_items:
            advisory = self.normalize_github_advisory(item)
            if advisory is not None:
                frame = self.pack_advisory_to_b60ipc(advisory, recipient=recipient)
                frames.append(frame)
        return frames

    async def poll_github_advisories(self, client: httpx.AsyncClient, per_page: int = 10) -> List[bytes]:
        """Sondeo asíncrono no bloqueante de la API pública de GitHub Advisories."""
        url = f"https://api.github.com/advisories?per_page={per_page}"
        headers = _get_api_headers()
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    raw_list = cast(List[Mapping[str, object]], data)
                    return self.ingest_raw_advisories(raw_list)
            else:
                logger.warning("Fallo en sondeo GitHub Advisories: HTTP %s", response.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error termodinámico en sondeo de advisories: %s", exc)
        return []

    async def poll_code4rena_repos(
        self, client: httpx.AsyncClient, per_page: int = 10, recipient: str = "bounty_ring_dispatcher"
    ) -> List[bytes]:
        """Sondeo asíncrono de repositorios de auditoría competitiva de Code4rena."""
        url = f"https://api.github.com/orgs/code-423n4/repos?sort=created&per_page={per_page}"
        headers = _get_api_headers()
        frames: List[bytes] = []
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                logger.warning("Fallo en sondeo Code4rena: HTTP %s", response.status_code)
                return frames

            data = response.json()
            if not isinstance(data, list):
                return frames

            for item in data:
                if not isinstance(item, dict):
                    continue
                repo_name = str(item.get("name", ""))
                repo_url = str(item.get("html_url", ""))
                desc = str(item.get("description", "")) if item.get("description") else ""
                advisory = self.normalize_contest_repository(
                    repo_name=repo_name, repo_url=repo_url, description=desc, source="code4rena"
                )
                if advisory is not None:
                    frames.append(self.pack_advisory_to_b60ipc(advisory, recipient=recipient))
        except Exception as exc:  # noqa: BLE001
            logger.error("Error termodinámico en sondeo de Code4rena: %s", exc)
        return frames

    async def poll_live_network(
        self, client: httpx.AsyncClient, per_page: int = 10, recipient: str = "bounty_ring_dispatcher"
    ) -> List[bytes]:
        """Agrega de forma simultánea el sondeo de múltiples feeds públicos sin bloqueo."""
        import asyncio

        gh_task = self.poll_github_advisories(client, per_page=per_page)
        c4_task = self.poll_code4rena_repos(client, per_page=per_page, recipient=recipient)
        results = await asyncio.gather(gh_task, c4_task, return_exceptions=True)

        merged: List[bytes] = []
        for res in results:
            if isinstance(res, list):
                merged.extend(res)
            elif isinstance(res, Exception):
                logger.error("Excepción en ingestión paralela: %s", res)
        return merged
