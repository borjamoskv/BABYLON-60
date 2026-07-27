# [C5-REAL] Exergy-Maximized
"""
cat_id: ultrathink-siege
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import asyncio
import json
import logging
import sys
from argparse import ArgumentParser

from babylon60.extensions.swarm.github_auditor import GitHubAuditorDaemon

# Set up raw C5-REAL logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("leviathan")


async def get_all_repos(owner: str) -> list[str]:
    """Descubre repositorios topológicos mediante GitHub CLI (gh)."""
    proc = await asyncio.create_subprocess_exec(
        "gh",
        "api",
        f"/users/{owner}/repos?per_page=100",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error("Error obteniendo repos: %s", stderr.decode().strip())
        return []

    try:
        repos = json.loads(stdout)
        return [repo["name"] for repo in repos if not repo["fork"]]
    except json.JSONDecodeError:
        logger.error("JSON inválido desde gh api.")
        return []


async def execute_siege(owner: str, max_concurrency: int = 100):
    repos = await get_all_repos(owner)

    if not repos:
        logger.warning("No se encontraron repositorios para asediar en %s.", owner)
        return

    logger.critical(
        "🔱 [LEVIATHAN] Iniciando Asedio UltraThink sobre %d repositorios...", len(repos)
    )

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _audit_repo(repo_name: str):
        async with semaphore:
            try:
                daemon = GitHubAuditorDaemon(owner=owner, repo=repo_name, tenant_id="leviathan")
                await daemon.audit_once()
            except Exception as e:  # noqa: BLE001
                logger.error("Fractura en el asedio de %s/%s: %s", owner, repo_name, e)

    tasks = [_audit_repo(repo) for repo in repos]
    await asyncio.gather(*tasks)

    logger.critical(
        "🔥 [LEVIATHAN] Asedio completado. Toda la superficie topológica ha sido escaneada."
    )


if __name__ == "__main__":
    parser = ArgumentParser(description="Leviathan Siege - UltraThink GitHub Auditor")
    parser.add_argument("--owner", type=str, required=True, help="GitHub Owner to siege")
    parser.add_argument("--max-concurrency", type=int, default=100, help="Max parallel agents")

    args = parser.parse_args()

    try:
        asyncio.run(execute_siege(args.owner, args.max_concurrency))
    except KeyboardInterrupt:
        logger.warning("Asedio interrumpido por el Operador.")
        sys.exit(130)
