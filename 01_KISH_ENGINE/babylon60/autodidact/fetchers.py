# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | PRIMARY LITERATURE FETCHERS | STATE: C5-REAL
# ============================================================================
"""
Módulo de Adquisición de Literatura Científica Primaria.
Extrae metadatos, resúmenes y claims desde arXiv API y repositorios locales
sin incurrir en la anergía de descarga masiva de archivos binarios pesados.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List

from babylon60.autodidact.types import EvidenceSource, RawEvidence

logger = logging.getLogger("babylon60.autodidact.fetchers")

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


class ArxivFetcher:
    """
    Fetcher de ultra-bajo coste para arXiv API.
    Parsea respuestas Atom XML nativamente sin dependencias externas.
    """

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout

    def parse_atom_xml(self, xml_content: str | bytes) -> List[RawEvidence]:
        """
        Parsea contenido Atom XML de arXiv y retorna una lista de RawEvidence estructurados.
        """
        if isinstance(xml_content, str):
            xml_bytes = xml_content.encode("utf-8")
        else:
            xml_bytes = xml_content

        results: List[RawEvidence] = []
        try:
            root = ET.fromstring(xml_bytes)
            for entry in root.findall(f"{ATOM_NS}entry"):
                id_elem = entry.find(f"{ATOM_NS}id")
                title_elem = entry.find(f"{ATOM_NS}title")
                summary_elem = entry.find(f"{ATOM_NS}summary")
                published_elem = entry.find(f"{ATOM_NS}published")

                arxiv_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else ""
                summary = (
                    summary_elem.text.strip().replace("\n", " ")
                    if summary_elem is not None and summary_elem.text
                    else ""
                )
                published = published_elem.text.strip() if published_elem is not None and published_elem.text else ""

                authors = []
                for author in entry.findall(f"{ATOM_NS}author"):
                    name_elem = author.find(f"{ATOM_NS}name")
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                payload_dict = {
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "published": published,
                }
                payload_str = json.dumps(payload_dict, sort_keys=True)
                digest = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

                ev = RawEvidence(
                    source=EvidenceSource.ARXIV_PAPER,
                    raw_payload=payload_dict,
                    digest_sha256=digest,
                )
                results.append(ev)
        except Exception as ex:
            logger.warning(f"Error parseando Atom XML de arXiv: {ex}")

        return results

    def fetch_papers(self, query: str, max_results: int = 5) -> List[RawEvidence]:
        """
        Consulta la API pública de arXiv.
        Si la conexión falla o el endpoint no responde, retorna lista vacía de forma fail-safe.
        """
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BABYLON-60-Autodidact/2.0 (research@babylon60.com)"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                xml_data = resp.read()
                return self.parse_atom_xml(xml_data)
        except Exception as ex:
            logger.debug(f"Aviso de red al consultar arXiv ({url}): {ex}")
            return []


class LocalCorpusFetcher:
    """
    Escanea directorios locales (ej. papers/) y extrae RawEvidence
    desde archivos de texto, markdown o metadatos JSON.
    """

    def __init__(self, base_dir: str = "papers"):
        self.base_dir = base_dir

    def scan_corpus(self) -> List[RawEvidence]:
        """
        Escanea archivos legibles en base_dir y emite RawEvidence con digest SHA-256.
        """
        results: List[RawEvidence] = []
        if not os.path.exists(self.base_dir):
            return results

        for root, _, files in os.walk(self.base_dir):
            for fname in files:
                if fname.startswith("."):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    # Si es texto o markdown
                    if fname.endswith((".txt", ".md", ".json")):
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        results.append(
                            RawEvidence(
                                source=EvidenceSource.FILESYSTEM,
                                raw_payload={"path": fpath, "content": content[:4096]},
                                digest_sha256=digest,
                            )
                        )
                    # Si es PDF, registramos metadatos de archivo sin cargar bytes
                    elif fname.endswith(".pdf"):
                        stat = os.stat(fpath)
                        h = hashlib.sha256()
                        h.update(f"{fname}:{stat.st_size}".encode("utf-8"))
                        results.append(
                            RawEvidence(
                                source=EvidenceSource.FILESYSTEM,
                                raw_payload={"path": fpath, "size_bytes": stat.st_size},
                                digest_sha256=h.hexdigest(),
                            )
                        )
                except Exception as ex:
                    logger.debug(f"Error escaneando archivo {fpath}: {ex}")

        return results
