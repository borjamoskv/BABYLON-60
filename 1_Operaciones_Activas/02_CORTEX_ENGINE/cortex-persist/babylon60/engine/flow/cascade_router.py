#!/usr/bin/env python3
"""
Cascade Router
Tactical routing logic to delegate heavy LLM tasks to local CLI engines:
Gemini (Antigravity), Claude Code, and Codex.
"""

import asyncio
import logging
import os
import sqlite3
import subprocess
from pathlib import Path

from babylon60.crypto.hash_registry import cortex_hash_truncated

logger = logging.getLogger("babylon60_cascade.router")


class CascadeRouter:
    """Tactical router to delegate heavy LLM tasks to CLI engines."""

    def __init__(self):
        pass

    def fallback_response(self, engine: str, prompt: str) -> str:
        """Fallback response when engine is unavailable."""
        try:
            from babylon60.extensions.forensic.circuit_breaker import CircuitBreaker

            cb = CircuitBreaker(f"cascade_router_{engine}")
            cb._on_failure()
        except (ValueError, TypeError, KeyError, OSError, RuntimeError) as cb_err:
            logger.debug("Could not update circuit breaker: %s", cb_err)
        return f"Error: CLI tool '{engine}' not found in PATH. Subprocess execution failed."

    async def route_task(
        self,
        prompt: str,
        task_type: str = "general",
        files: list[str] | None = None,
        task_id: str | None = None,
    ) -> str:
        """
        Routes the task based on heuristics.
        task_type hints: 'architecture', 'refactor', 'snippet', 'test', 'audit'
        """
        engine = self._select_engine(task_type, files)
        logger.info("🧠 [ROUTER] Selected engine: %s for task: %s", engine, task_type)
        return await self._execute(engine, prompt, files, task_id)

    def _select_engine(self, task_type: str, files: list[str] | None) -> str:
        num_files = len(files) if files else 0

        # Heuristics based on engine strengths and context windows
        if task_type in ("architecture", "audit", "deep_analysis") or num_files > 5:
            return "gemini"
        elif task_type in ("refactor", "bugfix", "strict_typing", "general"):
            return "claude"
        elif task_type in ("snippet", "test", "quick"):
            return "codex"
        else:
            return "claude"  # default fallback

    def _get_active_model(self, engine: str, attempt: int) -> str:
        primary_model = "qwen2.5-coder:32b"
        fallback_model = "qwen2.5-coder:7b"

        if attempt == 1:
            if engine in ("gemini", "claude"):
                return primary_model
            elif engine == "codex":
                return "llama3:latest"
            else:
                raise ValueError(f"Unknown engine: {engine}")
        else:
            logger.warning(
                "⚠️ [ROUTER] Graceful Degradation Triggered. Falling back to %s", fallback_model
            )
            return fallback_model

    def _get_child_env(self) -> dict[str, str]:
        return {
            **os.environ,
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "sk-ant-fallback"),
            "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "gemini-fallback"),
            "GEMINI_CLI_HOME": os.environ.get("GEMINI_CLI_HOME", "/tmp/gemini_home"),
        }

    def _log_to_db(
        self, task_id: str | None, engine: str, output_content: str, returncode: int
    ) -> None:
        if not task_id:
            return
        try:
            db_path = Path(os.environ.get("CORTEX_DB_PATH", "~/.babylon60/cortex.db")).expanduser()
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                digest = cortex_hash_truncated(output_content.encode("utf-8"), length=16)
                conn.execute(
                    "INSERT INTO episodes (session_id, event_type, project, content) VALUES (?, ?, ?, ?)",
                    (
                        "cascade-sys",
                        "llm_task_result",
                        "cortex-engine",
                        f"task_id:{task_id} engine:{engine} digest:{digest}\\n{output_content[:500]}",
                    ),
                )
                try:
                    status = "completed" if returncode == 0 else "failed"
                    conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
                except sqlite3.OperationalError:
                    pass
                conn.commit()
                conn.close()
        except (ValueError, TypeError, KeyError, OSError, RuntimeError) as db_e:
            logger.error("⚠️ [ROUTER] DB persistence failed for indexing: %s", db_e)

    async def _execute(
        self, engine: str, prompt: str, files: list[str] | None, task_id: str | None
    ) -> str:  # type: ignore
        import asyncio

        max_retries = 3
        base_delay = 2

        for attempt in range(1, max_retries + 1):
            try:
                active_model = self._get_active_model(engine, attempt)

                cmd = ["ollama", "run", active_model, prompt]
                logger.info(
                    "🚀 [ROUTER] Local-Inference-OMEGA Active. Dispatching to %s (Attempt %s/%s)...",
                    active_model,
                    attempt,
                    max_retries,
                )

                child_env = self._get_child_env()

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=child_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(), timeout=300
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.communicate()
                    logger.error("⏱️ [ROUTER] %s execution timed out (300s).", engine)
                    if attempt < max_retries:
                        delay = base_delay**attempt
                        logger.info("⏳ [ROUTER] Retrying in %s seconds...", delay)
                        await asyncio.sleep(delay)
                        continue
                    return f"Error: {engine} timed out."

                stdout = stdout_bytes.decode("utf-8").strip()
                stderr = stderr_bytes.decode("utf-8").strip()

                output_content = (
                    stdout if process.returncode == 0 else f"ERROR:\\n{stderr}\\n{stdout}"
                )

                if process.returncode != 0:
                    logger.error("❌ [ROUTER] %s failed. STDERR: %s", engine, stderr)
                    if attempt < max_retries:
                        delay = base_delay**attempt
                        logger.info("⏳ [ROUTER] Retrying in %s seconds...", delay)
                        await asyncio.sleep(delay)
                        continue

                self._log_to_db(task_id, engine, output_content, process.returncode)

                if process.returncode != 0:
                    return f"Error ({engine}): {stderr}"

                return stdout

            except FileNotFoundError:
                logger.error("🔌 [ROUTER] CLI not found in PATH. Activating fallback...")
                return self.fallback_response(engine, prompt)
            except (ValueError, TypeError, KeyError, OSError, RuntimeError) as e:
                logger.error("🔥 [ROUTER] Subprocess execution exception: %s", e)
                if attempt < max_retries:
                    delay = base_delay**attempt
                    logger.info("⏳ [ROUTER] Retrying in %s seconds due to exception...", delay)
                    await asyncio.sleep(delay)
                    continue
                return f"Error: {e}"


if __name__ == "__main__":
    import asyncio

    # Test stub
    logging.basicConfig(level=logging.INFO)
    router = CascadeRouter()

    async def run_tests():
        logger.info(
            "Test Routing (Architecture): %s",
            router._select_engine("architecture", ["f1", "f2", "f3", "f4", "f5", "f6"]),
        )
        logger.info("Test Routing (Refactor): %s", router._select_engine("refactor", ["f1"]))
        logger.info("Test Routing (Snippet): %s", router._select_engine("snippet", []))

    asyncio.run(run_tests())
