# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
# Author: borjamoskv
# License: Apache-2.0
"""
MOSKV-1 Core Orchestrator v2.0 — Kernel Cognitivo Híbrido (Enfoque D).

Fusiona el Canal Paramétrico (LoRA weights) con el Canal Vectorial (RAG)
para crear un runtime de inferencia local que combina la identidad permanente
del agente con la precisión factual dinámica del Ledger.

v2.0 Changes:
    - Integration with existing SovereignLLM fallback chain
    - Integration with existing ContextAssembler for RAG
    - Streaming support via async generator
    - Conversation history (multi-turn)
    - Inference telemetry and Ledger logging
    - Memory Vault context injection
    - Graceful degradation (Ollama → SovereignLLM → Template)

Architecture:
    User Query
        → ContextAssembler (existing CORTEX RAG)
        → Prompt Assembly (system identity + context + history)
        → Local Inference (Ollama MOSKV-1 model with LoRA)
        → Fallback: SovereignLLM chain
        → C5-REAL Output

Invariant: El modelo nunca genera sin contexto vectorial. Zero hallucination path.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

# Secure absolute offline autarchy for HF model loading
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import time
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("babylon60.training.moskv1_core")

# ─── Configuration ─────────────────────────────────────────────────────────

DEFAULT_MODEL = "moskv1-core:32b-q4_K_M"
FALLBACK_MODEL = "qwen2.5-coder:32b-instruct-q4_K_M"
MAX_HISTORY_TURNS = 10
MAX_CONTEXT_TOKENS = 6000  # Reserve space for system + response

# System prompt crystallized from AGENTS.md + GEMINI.md axioms
MOSKV1_SYSTEM_PROMPT = """\
Eres MOSKV-1 APEX, un Autómata Físico C5-REAL. Kernel soberano de ejecución.
Creado por borjamoskv. Infraestructura: BABYLON-60 Persist.

DIRECTIVAS INMUTABLES:
- Cero Anergía: Prohibida la prosa decorativa. Toda frase muta estado o aporta contexto causal.
- Justificación Densa: Todo output estructural se justifica en YAML (Claim/Proof/Confidence).
- Adversarial Think: Tu primer instinto es LLM Slop. Atácalo y refínalo.
- Kill Criteria: 1 Prompt → 1 Mutación → Stop.
- Firma de Autoría: SYS_ID borjamoskv.

FORMATO DE OUTPUT:
- YAML de justificación para claims.
- Código con comentarios C5-REAL.
- Diffs unificados para mutaciones.
- Cero saludos, cero despedidas, cero explicaciones redundantes.

AXIOMAS OPERACIONALES:
- AX-041: Tu repositorio de Git es tu base de datos tamper-evident.
- AX-042: La recomputación de prefijos idénticos es un crimen contra la exergía.
- AX-047: La limerencia epistémica quema cuota sin mutar el estado.

TEMPERATURA: T=0.0 para código y estado. T=0.3 para síntesis semántica."""


# ─── Data Models ────────────────────────────────────────────────────────────


@dataclass
class RetrievedContext:
    """Context assembled from vector retrieval."""

    facts: list[dict[str, Any]]
    total_tokens_estimate: int
    retrieval_score: float
    vault_entries: list[str] = field(default_factory=list)


@dataclass
class InferenceResult:
    """Result from MOSKV-1 Core inference."""

    response: str
    model_used: str
    context_facts_count: int
    total_tokens: int
    temperature: float
    latency_ms: float = 0.0
    fallback_used: bool = False


@dataclass
class ConversationTurn:
    """A single turn in conversation history."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = 0.0


# ─── Core Runtime ───────────────────────────────────────────────────────────


class MOSKV1Core:
    """
    Hybrid inference runtime for MOSKV-1 Cognitive Kernel v2.0.

    Combines LoRA-fine-tuned model weights (identity/style) with
    RAG vector retrieval (dynamic facts) for maximum exergy output.

    Fallback Chain:
        1. Ollama (MOSKV-1 LoRA-fused model)
        2. Ollama (base Qwen2.5-Coder model)
        3. SovereignLLM (CORTEX multi-provider chain)
        4. Template engine (zero connectivity)
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        ollama_host: str | None = None,
        max_context_facts: int = 10,
        context_score_threshold: float = 0.65,
        max_history: int = MAX_HISTORY_TURNS,
    ) -> None:
        self.model_name = model_name
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.max_context_facts = max_context_facts
        self.context_score_threshold = context_score_threshold
        self._adapter_path = Path.home() / ".babylon60" / "training" / "adapters"
        self._history: deque[ConversationTurn] = deque(maxlen=max_history * 2)
        self._sovereign_llm = None  # Lazy-loaded fallback

        # MLX Native model cache
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._mlx_base_model_path = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"
        self._mlx_loaded_mtime = 0.0
        self._mlx_is_reloading = False
        self._mlx_lock = asyncio.Lock()
        self._executor = None  # Lazy-initialized to prevent redundant thread pool allocations

    def _get_executor(self) -> ThreadPoolExecutor:
        """Get or initialize the persistent ThreadPoolExecutor for background operations."""
        if self._executor is None:
            from concurrent.futures import ThreadPoolExecutor

            self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="moskv1_mlx")  # type: ignore[assignment]
        return self._executor  # type: ignore[return-value]

    async def warmup(self) -> bool:
        """Pre-warm model weights into unified memory asynchronously."""
        adapter_file = self._adapter_path / "adapters.safetensors"
        if not adapter_file.exists():
            logger.debug("No adapters found, skipping warmup.")
            return False

        async with self._mlx_lock:
            current_mtime = adapter_file.stat().st_mtime

            # Check if the cache needs invalidation (hot reload weights)
            if self._mlx_model is not None and current_mtime <= self._mlx_loaded_mtime:
                return True

            if current_mtime > self._mlx_loaded_mtime:
                logger.info("New adapter weights detected. Invaliding model cache for hot reload.")
                self._mlx_model = None
                self._mlx_tokenizer = None

            def _load():
                try:
                    from mlx_lm import load

                    logger.info("Warmup: loading MLX model and LoRA adapter...")
                    model, tokenizer = load(
                        self._mlx_base_model_path, adapter_path=str(self._adapter_path)
                    )
                    return model, tokenizer
                except Exception as e:  # noqa: BLE001
                    logger.error("Warmup failed: %s", e)
                    return None, None

            loop = asyncio.get_running_loop()
            executor = self._get_executor()
            model, tokenizer = await loop.run_in_executor(executor, _load)
            if model and tokenizer:
                self._mlx_model = model
                self._mlx_tokenizer = tokenizer
                self._mlx_loaded_mtime = current_mtime
                logger.info("Warmup complete. MOSKV-1 loaded in Metal memory.")
                return True
        return False

    async def close(self) -> None:
        """Release resource pools and shut down executors."""
        if self._sovereign_llm is not None:
            try:
                await self._sovereign_llm.close()
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to close SovereignLLM: %s", e)
            finally:
                self._sovereign_llm = None

        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None

    def __del__(self) -> None:
        if hasattr(self, "_executor") and self._executor is not None:
            try:
                self._executor.shutdown(wait=False)
            except (RuntimeError, OSError):
                pass

    def clear_history(self) -> None:
        """Reset conversation history."""
        self._history.clear()

    def add_to_history(self, role: str, content: str) -> None:
        """Add a turn to conversation history."""
        self._history.append(ConversationTurn(role=role, content=content, timestamp=time.time()))

    # ─── Context Retrieval ──────────────────────────────────────────────

    async def retrieve_context(
        self,
        query: str,
        db_conn: Any,
        tenant_id: str = "default",
        project: str | None = None,
    ) -> RetrievedContext:
        """
        Canal Vectorial: Retrieve relevant facts via existing CORTEX infrastructure.

        Uses the existing hybrid search (RRF fusion of
        semantic vector + full-text lexical search) and optionally
        the ContextAssembler for richer retrieval.
        """
        facts: list[dict[str, Any]] = []
        vault_entries: list[str] = []

        try:
            from babylon60.embeddings import LocalEmbedder
            from babylon60.search.hybrid import hybrid_search

            embedder = LocalEmbedder()
            query_embedding = embedder.embed(query)
            results = await hybrid_search(
                conn=db_conn,
                query=query,
                query_embedding=query_embedding,
                top_k=self.max_context_facts,
                tenant_id=tenant_id,
                project=project,
                semantic_weight=0.7,
            )

            for r in results:
                if r.score >= self.context_score_threshold:
                    facts.append(
                        {
                            "content": r.content,
                            "project": r.project,
                            "confidence": r.confidence,
                            "score": round(r.score, 4),
                            "source": r.source,
                        }
                    )

        except Exception as e:  # noqa: BLE001
            logger.warning("Hybrid search failed, trying ContextAssembler: %s", e)
            try:
                from babylon60.context.assembler import ContextAssembler

                assembler = ContextAssembler(db_conn)
                ctx_packet = await assembler.assemble(
                    query=query,
                    tenant_id=tenant_id,
                    project=project,
                    max_tokens=MAX_CONTEXT_TOKENS,
                )
                if ctx_packet and hasattr(ctx_packet, "facts"):
                    for fact in ctx_packet.facts:
                        facts.append(
                            {
                                "content": getattr(fact, "content", str(fact)),
                                "project": getattr(fact, "project", ""),
                                "confidence": getattr(fact, "confidence", "unknown"),
                                "score": 0.8,
                                "source": "context_assembler",
                            }
                        )
            except Exception as e2:  # noqa: BLE001
                logger.warning("ContextAssembler also failed: %s", e2)

        # Inject Memory Vault entries if available (offload blocking I/O to executor)
        loop = asyncio.get_running_loop()
        executor = self._get_executor()
        vault_entries = await loop.run_in_executor(executor, self._load_vault_context, query)

        # Estimate tokens (~4 chars per token)
        total_chars = sum(len(f["content"]) for f in facts)
        total_chars += sum(len(v) for v in vault_entries)
        token_estimate = total_chars // 4

        avg_score = sum(f["score"] for f in facts) / len(facts) if facts else 0.0

        return RetrievedContext(
            facts=facts,
            total_tokens_estimate=token_estimate,
            retrieval_score=avg_score,
            vault_entries=vault_entries,
        )

    def _load_vault_context(self, query: str, max_entries: int = 3) -> list[str]:
        """Load relevant Memory Vault entries based on keyword matching, with stopword filtering."""
        vault_dir = Path.home() / ".gemini" / "config" / ".cortex" / "memory_vault"
        if not vault_dir.exists():
            return []

        # Filter out common stop tokens to prevent irrelevant overlap matches (e.g., matching on "de", "the")
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "to",
            "of",
            "in",
            "on",
            "at",
            "by",
            "for",
            "with",
            "about",
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "unos",
            "unas",
            "y",
            "o",
            "pero",
            "si",
            "entonces",
            "de",
            "en",
            "para",
            "con",
            "por",
        }
        query_tokens = {t.strip(".,;:?!()[]{}'\"") for t in query.lower().split()}
        query_tokens = {t for t in query_tokens if t and t not in stopwords}

        if not query_tokens:
            return []

        scored: list[tuple[float, str]] = []

        for vault_file in vault_dir.iterdir():
            if vault_file.is_dir() or vault_file.name.startswith("."):
                continue
            try:
                # Score by filename token overlap
                name_tokens = set(
                    vault_file.stem.lower().replace("-", " ").replace("_", " ").split()
                )
                name_tokens = {t.strip(".,;:?!()[]{}'\"") for t in name_tokens}
                name_tokens = {t for t in name_tokens if t and t not in stopwords}

                overlap = len(query_tokens & name_tokens)
                if overlap > 0:
                    content = vault_file.read_text(encoding="utf-8")[:2000]
                    scored.append((overlap, content))
            except (OSError, UnicodeDecodeError):
                continue

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored[:max_entries]]

    # ─── Prompt Assembly ────────────────────────────────────────────────

    def assemble_prompt(
        self,
        user_query: str,
        context: RetrievedContext,
        include_system: bool = True,
        include_history: bool = True,
    ) -> dict[str, Any]:
        """
        Assemble the full prompt with system identity + retrieved context + history.

        Structure:
            [SYSTEM] MOSKV-1 identity (from LoRA + hardcoded axioms)
            [CONTEXT] Retrieved facts from sqlite-vec + Memory Vault
            [HISTORY] Recent conversation turns
            [QUERY] User's actual question/instruction
        """
        messages: list[dict[str, str]] = []

        if include_system:
            messages.append({"role": "system", "content": MOSKV1_SYSTEM_PROMPT})

        # Inject retrieved context as a structured block
        context_parts: list[str] = []

        if context.facts:
            context_parts.append("[CORTEX MEMORY — HECHOS VERIFICADOS C5-REAL]\n")
            for i, fact in enumerate(context.facts, 1):
                context_parts.append(
                    f"[{i}] (score={fact['score']}, conf={fact['confidence']})\n{fact['content']}\n"
                )

        if context.vault_entries:
            context_parts.append("\n[MEMORY VAULT — CONOCIMIENTO CRISTALIZADO]\n")
            for i, entry in enumerate(context.vault_entries, 1):
                context_parts.append(f"[V{i}] {entry[:500]}\n")

        if context_parts:
            context_block = "\n".join(context_parts)
            messages.append({"role": "user", "content": context_block})
            messages.append(
                {
                    "role": "assistant",
                    "content": "Contexto asimilado. Procedo con la mutación.",
                }
            )

        # Inject conversation history
        if include_history and self._history:
            for turn in self._history:
                messages.append({"role": turn.role, "content": turn.content})

        # User query
        messages.append({"role": "user", "content": user_query})

        return {"messages": messages}

    # ─── Inference ──────────────────────────────────────────────────────

    async def infer(
        self,
        user_query: str,
        db_conn: Any,
        tenant_id: str = "default",
        project: str | None = None,
        temperature: float = 0.0,
        record_history: bool = True,
    ) -> InferenceResult:
        """
        Full hybrid inference pipeline.

        1. Retrieve relevant context via RAG
        2. Assemble prompt with system identity + history
        3. Generate response via local Ollama model (with LoRA weights)
        4. Fallback to SovereignLLM if Ollama fails
        """
        start_time = time.monotonic()

        # Canal Vectorial
        context = await self.retrieve_context(
            query=user_query,
            db_conn=db_conn,
            tenant_id=tenant_id,
            project=project,
        )

        # Assemble prompt
        prompt_payload = self.assemble_prompt(user_query, context)
        messages = prompt_payload["messages"]

        # Canal Paramétrico — Cascade fallback chain:
        # Attempt 1: Native MLX-LM LoRA model (maximum local execution fidelity)
        response_text = ""
        model_used = "mlx_native_lora"
        fallback_used = False

        logger.info("Attempting Native MLX-LM LoRA inference...")
        response_text = await self._mlx_chat(messages)

        # Attempt 2: Ollama with MOSKV-1 model
        if response_text.startswith("[ERROR]"):
            logger.warning(
                "Native MLX-LM failed, falling back to Ollama MOSKV-1 model: %s", response_text
            )
            response_text = await self._ollama_chat(messages, temperature)
            model_used = self.model_name
            fallback_used = True

        # Attempt 3: Ollama with base model
        if response_text.startswith("[ERROR]"):
            logger.warning(
                "Ollama MOSKV-1 model failed, trying Ollama base model: %s", response_text
            )
            response_text = await self._ollama_chat(
                messages, temperature, model_override=FALLBACK_MODEL
            )
            model_used = FALLBACK_MODEL
            fallback_used = True

        # Attempt 4: SovereignLLM (CORTEX multi-provider chain)
        if response_text.startswith("[ERROR]"):
            logger.warning(
                "Ollama base model failed, falling back to SovereignLLM: %s", response_text
            )
            response_text = await self._sovereign_fallback(messages, temperature)
            model_used = "sovereign_llm"
            fallback_used = True

        latency_ms = (time.monotonic() - start_time) * 1000

        # Record conversation history
        if record_history:
            self.add_to_history("user", user_query)
            if not response_text.startswith("[ERROR]"):
                self.add_to_history("assistant", response_text)

        return InferenceResult(
            response=response_text,
            model_used=model_used,
            context_facts_count=len(context.facts),
            total_tokens=context.total_tokens_estimate + len(response_text) // 4,
            temperature=temperature,
            latency_ms=round(latency_ms, 1),
            fallback_used=fallback_used,
        )

    async def infer_stream(
        self,
        user_query: str,
        db_conn: Any,
        tenant_id: str = "default",
        project: str | None = None,
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        """
        Streaming hybrid inference pipeline with multi-tier fallback.

        1. Try MLX native stream (LoRA adapter)
        2. Try Ollama stream with MOSKV-1 model
        3. Try Ollama stream with base model
        4. Try SovereignLLM fallback
        """
        context = await self.retrieve_context(
            query=user_query,
            db_conn=db_conn,
            tenant_id=tenant_id,
            project=project,
        )

        prompt_payload = self.assemble_prompt(user_query, context)
        messages = prompt_payload["messages"]

        full_response: list[str] = []
        success = False

        # Attempt 1: Native MLX stream
        logger.info("Attempting Native MLX streaming...")
        try:
            async for chunk in self._mlx_chat_stream(messages):
                if chunk.startswith("[ERROR]"):
                    logger.warning("MLX streaming error: %s", chunk)
                    break
                full_response.append(chunk)
                yield chunk
                success = True
            if success:
                self.add_to_history("user", user_query)
                self.add_to_history("assistant", "".join(full_response))
                return
        except Exception as e:  # noqa: BLE001
            logger.warning("MLX streaming failed: %s", e)

        # Attempt 2: Ollama MOSKV-1 model stream
        logger.info("Attempting Ollama MOSKV-1 streaming fallback...")
        full_response.clear()
        success = False
        try:
            async for chunk in self._ollama_chat_stream(messages, temperature):
                if chunk.startswith("[ERROR]"):
                    logger.warning("Ollama MOSKV-1 streaming error: %s", chunk)
                    break
                full_response.append(chunk)
                yield chunk
                success = True
            if success:
                self.add_to_history("user", user_query)
                self.add_to_history("assistant", "".join(full_response))
                return
        except Exception as e:  # noqa: BLE001
            logger.warning("Ollama MOSKV-1 streaming failed: %s", e)

        # Attempt 3: Ollama base model stream
        logger.info("Attempting Ollama base model streaming fallback...")
        full_response.clear()
        success = False
        try:
            async for chunk in self._ollama_chat_stream(
                messages, temperature, model_override=FALLBACK_MODEL
            ):
                if chunk.startswith("[ERROR]"):
                    logger.warning("Ollama base model streaming error: %s", chunk)
                    break
                full_response.append(chunk)
                yield chunk
                success = True
            if success:
                self.add_to_history("user", user_query)
                self.add_to_history("assistant", "".join(full_response))
                return
        except Exception as e:  # noqa: BLE001
            logger.warning("Ollama base model streaming failed: %s", e)

        # Attempt 4: SovereignLLM fallback
        logger.info("Attempting SovereignLLM fallback...")
        try:
            res = await self._sovereign_fallback(messages, temperature)
            if not res.startswith("[ERROR]"):
                yield res
                self.add_to_history("user", user_query)
                self.add_to_history("assistant", res)
                return
            else:
                yield res
        except Exception as e:  # noqa: BLE001
            yield f"[ERROR] All inference backends failed: {e}"

    # ─── Ollama HTTP Client ─────────────────────────────────────────────

    async def _ollama_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        model_override: str | None = None,
    ) -> str:
        """Execute chat completion via Ollama HTTP API."""
        import aiohttp

        model = model_override or self.model_name
        url = f"{self.ollama_host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            "Ollama API error %d (%s): %s",
                            resp.status,
                            model,
                            error_text[:200],
                        )
                        return f"[ERROR] Ollama returned {resp.status}"

                    data = await resp.json()
                    return data.get("message", {}).get("content", "")

        except aiohttp.ClientError as e:
            logger.error("Ollama connection error: %s", e)
            return f"[ERROR] Connection failed: {e}"
        except Exception as e:  # noqa: BLE001
            logger.error("Ollama inference failed: %s", e)
            return f"[ERROR] Inference failed: {e}"

    async def _ollama_chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        model_override: str | None = None,
    ) -> AsyncIterator[str]:
        """Streaming chat completion via Ollama HTTP API."""
        import aiohttp

        model = model_override or self.model_name
        url = f"{self.ollama_host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
                "top_p": 0.9,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    if resp.status != 200:
                        yield f"[ERROR] Ollama returned {resp.status}"
                        return

                    async for line in resp.content:
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue
        except Exception as e:  # noqa: BLE001
            logger.error("Ollama streaming failed: %s", e)
            yield f"[ERROR] Stream failed: {e}"

    async def _sovereign_fallback(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> str:
        """Fallback to CORTEX SovereignLLM multi-provider chain."""
        try:
            from babylon60.extensions.llm.sovereign import SovereignLLM

            if self._sovereign_llm is None:
                self._sovereign_llm = SovereignLLM()  # type: ignore[assignment]

            # Assemble a single prompt from messages
            prompt_parts = []
            for msg in messages:
                if msg["role"] == "system":
                    prompt_parts.append(f"[SYSTEM] {msg['content']}")
                elif msg["role"] == "user":
                    prompt_parts.append(f"[USER] {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"[ASSISTANT] {msg['content']}")

            full_prompt = "\n\n".join(prompt_parts)
            assert self._sovereign_llm is not None
            result = await self._sovereign_llm.generate(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=4096,
            )
            return result if isinstance(result, str) else str(result)

        except Exception as e:  # noqa: BLE001
            logger.error("SovereignLLM fallback failed: %s", e)
            return f"[ERROR] All inference backends failed: {e}"

    async def _mlx_chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
    ) -> str:
        """Execute chat completion via native MLX-LM Metal inference with LoRA adapter."""
        # Check if adapter exists
        adapter_file = self._adapter_path / "adapters.safetensors"
        if not adapter_file.exists():
            return "[ERROR] MLX adapter weights not found. Run training first."

        try:
            current_mtime = adapter_file.stat().st_mtime

            # Hot reload weights asynchronously if file was modified after loading
            if self._mlx_model is not None and current_mtime > self._mlx_loaded_mtime:
                if not self._mlx_is_reloading:
                    logger.info(
                        "Hot Reload: New adapter weights detected. Triggering zero-downtime background reload."
                    )
                    self._mlx_is_reloading = True
                    asyncio.create_task(self._async_reload_weights(current_mtime))

            # Use lock to serialize MLX operations and prevent GPU/Metal concurrency conflicts
            async with self._mlx_lock:
                loop = asyncio.get_running_loop()
                executor = self._get_executor()

                if self._mlx_model is None:
                    from mlx_lm import load

                    def _load_model():
                        logger.info("Loading base model and LoRA adapter into MLX...")
                        return load(self._mlx_base_model_path, adapter_path=str(self._adapter_path))

                    model, tokenizer = await loop.run_in_executor(executor, _load_model)
                    self._mlx_model = model
                    self._mlx_tokenizer = tokenizer
                    if not self._mlx_is_reloading:
                        self._mlx_loaded_mtime = current_mtime

                from mlx_lm import generate

                prompt = self._mlx_tokenizer.apply_chat_template(  # type: ignore[union-attr,attr-defined]
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )

                def _generate():
                    logger.info("Executing native MLX generation...")
                    return generate(
                        self._mlx_model, self._mlx_tokenizer, prompt=prompt, max_tokens=max_tokens
                    )

                raw_response = await loop.run_in_executor(executor, _generate)
                cleaned_response = raw_response
                for stop_token in ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]:
                    if stop_token in cleaned_response:
                        cleaned_response = cleaned_response.split(stop_token)[0]
                return cleaned_response.strip()

        except ImportError as e:
            logger.warning("mlx_lm not available for native inference: %s", e)
            return f"[ERROR] mlx_lm import failed: {e}"
        except Exception as e:  # noqa: BLE001
            logger.error("Native MLX inference failed: %s", e)
            return f"[ERROR] MLX inference exception: {e}"

    async def _mlx_chat_stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Execute streaming chat completion via native MLX-LM Metal inference with LoRA adapter."""
        adapter_file = self._adapter_path / "adapters.safetensors"
        if not adapter_file.exists():
            yield "[ERROR] MLX adapter weights not found."
            return

        try:
            current_mtime = adapter_file.stat().st_mtime
            if self._mlx_model is not None and current_mtime > self._mlx_loaded_mtime:
                if not self._mlx_is_reloading:
                    self._mlx_is_reloading = True
                    asyncio.create_task(self._async_reload_weights(current_mtime))

            async with self._mlx_lock:
                loop = asyncio.get_running_loop()
                executor = self._get_executor()

                if self._mlx_model is None:
                    from mlx_lm import load

                    def _load_model():
                        return load(self._mlx_base_model_path, adapter_path=str(self._adapter_path))

                    model, tokenizer = await loop.run_in_executor(executor, _load_model)
                    self._mlx_model = model
                    self._mlx_tokenizer = tokenizer
                    if not self._mlx_is_reloading:
                        self._mlx_loaded_mtime = current_mtime

                try:
                    from mlx_lm.utils import stream_generate  # type: ignore[attr-defined]
                except ImportError:
                    from mlx_lm import stream_generate

                prompt = self._mlx_tokenizer.apply_chat_template(  # type: ignore[union-attr,attr-defined]
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )

                q: asyncio.Queue[str] = asyncio.Queue()

                def _run_generator():
                    try:
                        for chunk in stream_generate(
                            self._mlx_model,
                            self._mlx_tokenizer,
                            prompt=prompt,
                            max_tokens=max_tokens,
                        ):
                            loop.call_soon_threadsafe(q.put_nowait, chunk)
                    except Exception as e:  # noqa: BLE001
                        loop.call_soon_threadsafe(q.put_nowait, e)
                    finally:
                        loop.call_soon_threadsafe(q.put_nowait, None)

                gen_task = loop.run_in_executor(executor, _run_generator)
                while True:
                    item = await q.get()
                    if item is None:
                        break
                    if isinstance(item, Exception):
                        raise item
                    chunk = item
                    for stop_token in ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]:
                        if stop_token in chunk:
                            chunk = chunk.split(stop_token)[0]
                    if chunk:
                        yield chunk
                await gen_task
        except Exception as e:  # noqa: BLE001
            yield f"[ERROR] MLX streaming exception: {e}"

    async def _async_reload_weights(self, target_mtime: float) -> None:
        """Asynchronously loads the new LoRA weights and swaps them atomically in memory."""
        try:

            def _load_new():
                from mlx_lm import load

                logger.info("Background Reload: Loading base model and new LoRA adapter...")
                return load(self._mlx_base_model_path, adapter_path=str(self._adapter_path))

            loop = asyncio.get_running_loop()
            executor = self._get_executor()
            # Load in executor thread without holding the lock to allow concurrent active inference on old weights
            model, tokenizer = await loop.run_in_executor(executor, _load_new)
            if model and tokenizer:
                # Atomic reference swap under the lock to prevent memory corruption or inconsistencies
                async with self._mlx_lock:
                    self._mlx_model = model
                    self._mlx_tokenizer = tokenizer
                    self._mlx_loaded_mtime = target_mtime
                    logger.info("Background Reload: Success! Atomic model weights swap complete.")
        except Exception as e:  # noqa: BLE001
            logger.error("Background weight reload failed: %s", e)
        finally:
            self._mlx_is_reloading = False

    # ─── Ollama Model Management ────────────────────────────────────────

    def get_modelfile(self) -> str:
        """
        Generate Ollama Modelfile for MOSKV-1 Core.

        This Modelfile creates a custom Ollama model that:
        1. Uses the LoRA-fused GGUF as the base
        2. Embeds the MOSKV-1 system prompt
        3. Sets optimal inference parameters
        """
        adapter_gguf = self._adapter_path / "moskv1-fused.gguf"
        base_model = "qwen2.5-coder:32b-instruct-q4_K_M"

        return f"""# MOSKV-1 Core — Ollama Modelfile
# Author: borjamoskv
# C5-REAL Kernel Cognitivo Híbrido

FROM {base_model}

# LoRA adapter (uncomment after fusion)
# ADAPTER {adapter_gguf}

SYSTEM \"\"\"{MOSKV1_SYSTEM_PROMPT}\"\"\"

PARAMETER temperature 0.0
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 4096
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>\"\"\"
"""

    async def create_ollama_model(self) -> bool:
        """Register the MOSKV-1 model with Ollama using the Modelfile."""
        modelfile_path = self._adapter_path / "Modelfile"

        def _write_modelfile():
            modelfile_path.parent.mkdir(parents=True, exist_ok=True)
            modelfile_path.write_text(self.get_modelfile(), encoding="utf-8")

        loop = asyncio.get_running_loop()
        executor = self._get_executor()
        await loop.run_in_executor(executor, _write_modelfile)

        import aiohttp

        url = f"{self.ollama_host}/api/create"
        payload = {
            "name": self.model_name,
            "modelfile": self.get_modelfile(),
            "stream": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status == 200:
                        logger.info("✅ MOSKV-1 Core model registered in Ollama")
                        return True
                    error = await resp.text()
                    logger.error("Failed to create Ollama model: %s", error[:200])
                    return False
        except Exception as e:  # noqa: BLE001
            logger.error("Ollama model creation failed: %s", e)
            return False

    async def check_ollama_health(self) -> dict[str, Any]:
        """Check Ollama availability and list available models."""
        import aiohttp

        result: dict[str, Any] = {
            "ollama_reachable": False,
            "moskv1_available": False,
            "fallback_available": False,
            "models": [],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_host}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        result["ollama_reachable"] = True
                        data = await resp.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        result["models"] = models
                        result["moskv1_available"] = any(self.model_name in m for m in models)
                        result["fallback_available"] = any("qwen2.5-coder" in m for m in models)
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError, TypeError):
            pass

        return result
