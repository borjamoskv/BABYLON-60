# [C5-REAL] Exergy-Maximized
"""GitHub Real-Time Auditor Daemon (CodeQL & Issues).

Pollea asíncronamente el API de GitHub (vía CLI `gh`) para buscar Alertas de Code Scanning
e Issues abiertos. Invoca al Enjambre (MejoraloSwarm) aislando la carga termodinámica,
aplica mutaciones AST y cristaliza (Git Sentinel) cerrando el bucle.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from babylon60.extensions.mejoralo.swarm import MejoraloSwarm

logger = logging.getLogger("babylon60_extensions.swarm.github_auditor")


class GitHubAuditorDaemon:
    """Real-time C5-REAL Daemon for mitigating GitHub Issues & CodeQL alerts."""

    def __init__(
        self, owner: str, repo: str, poll_interval_s: int = 60, tenant_id: str = "default"
    ) -> None:
        self.owner = owner
        self.repo = repo
        self.poll_interval_s = poll_interval_s
        self.tenant_id = tenant_id
        self._stop_event = asyncio.Event()
        self._in_flight_alerts: set[int] = set()

    async def _gh_api(self, endpoint: str) -> list[dict[str, Any]]:
        """Llama al API de GitHub usando `gh` CLI para heredar la sesión."""
        cmd = ["gh", "api", endpoint, "--paginate"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("Error GH API %s: %s", endpoint, stderr.decode().strip())
            return []

        try:
            output = stdout.decode().strip()
            if not output:
                return []
            if output.startswith("[") and "][" in output:
                output = output.replace("][", "],[")
                output = f"[{output[1:-1]}]"
            return json.loads(output)
        except json.JSONDecodeError as e:
            logger.error("Fallo al decodificar GH API %s: %s", endpoint, e)
            return []

    async def _fetch_codeql_alerts(self) -> list[dict[str, Any]]:
        """Extrae CodeQL alerts abiertas."""
        endpoint = f"/repos/{self.owner}/{self.repo}/code-scanning/alerts?state=open"
        return await self._gh_api(endpoint)

    async def _mitigate_codeql_alert(self, alert: dict[str, Any]) -> None:
        """Invoca al Swarm para mitigar una alerta específica."""
        alert_num = alert.get("number")
        if not alert_num or alert_num in self._in_flight_alerts:
            return

        rule = alert.get("rule", {}).get("name", "Unknown Rule")
        instances = alert.get("most_recent_instance", {}).get("location", {})
        file_path_str = instances.get("path")
        start_line = instances.get("start_line")

        if not file_path_str or not start_line:
            logger.warning("CodeQL Alert #%s carece de path o línea.", alert_num)
            return

        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.warning("El path %s no existe físicamente.", file_path)
            return

        self._in_flight_alerts.add(alert_num)
        finding_str = f"{file_path_str}:{start_line} -> {rule}"
        logger.info("🛡️ [AUDITOR] Mitigando CodeQL #%s: %s", alert_num, finding_str)

        try:
            swarm = MejoraloSwarm(level=2)
            result_code = await swarm.refactor_file(file_path=file_path, findings=[finding_str])

            if result_code:
                # Escribimos el AST mutado (C5-REAL)
                file_path.write_text(result_code, encoding="utf-8")
                logger.info("✅ [AUDITOR] AST Mutado para CodeQL #%s.", alert_num)

                commit_msg = f"[bridge] fix(security): resolve CodeQL alert #{alert_num}"
                await self._git_commit(file_path, commit_msg)
            else:
                logger.error(
                    "❌ [AUDITOR] El Enjambre no pudo sintetizar mitigación para CodeQL #%s",
                    alert_num,
                )
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
            logger.error("⚠️ [AUDITOR] Falla asimétrica en #%s: %s", alert_num, e)

    async def _git_commit(self, filepath: Path, message: str) -> None:
        """Sella la mutación en el Ledger (Git)."""
        await asyncio.create_subprocess_exec("git", "add", str(filepath))
        proc = await asyncio.create_subprocess_exec(
            "git",
            "commit",
            "--no-verify",
            "-m",
            message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode == 0:
            logger.info("🔒 [SENTINEL] Mutación anclada en Ledger: %s", message)
        else:
            logger.warning("⚠️ [SENTINEL] No hubo mutación o falló el commit.")

    async def daemon_loop(self) -> None:
        """Bucle en tiempo real C5-REAL."""
        logger.info(
            "👁️‍🗨️ [AUDITOR] Ouroboros Real-Time Auditor activado (%s/%s).", self.owner, self.repo
        )

        while not self._stop_event.is_set():
            logger.info("📡 [AUDITOR] Escaneando vector de entropía (CodeQL)...")
            alerts = await self._fetch_codeql_alerts()

            tasks = []
            for alert in alerts:
                if alert.get("number") not in self._in_flight_alerts:
                    tasks.append(self._mitigate_codeql_alert(alert))

            if tasks:
                chunk_size = 5
                for i in range(0, len(tasks), chunk_size):
                    await asyncio.gather(*tasks[i : i + chunk_size])
            else:
                logger.debug("💤 [AUDITOR] Cero entropía CodeQL. Reposo...")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval_s)
            except asyncio.TimeoutError:
                continue

    async def audit_once(self) -> None:
        """Asedio UltraThink P0 (Una pasada, sin bucle infinito)."""
        logger.info("⚡ [LEVIATHAN] Desplegando agente sobre %s/%s", self.owner, self.repo)
        alerts = await self._fetch_codeql_alerts()

        tasks = []
        for alert in alerts:
            if alert.get("number") not in self._in_flight_alerts:
                tasks.append(self._mitigate_codeql_alert(alert))

        if tasks:
            chunk_size = 5
            for i in range(0, len(tasks), chunk_size):
                await asyncio.gather(*tasks[i : i + chunk_size])
        else:
            logger.debug("💤 [LEVIATHAN] %s/%s - 0 entropía.", self.owner, self.repo)

    def stop(self) -> None:
        self._stop_event.set()
