import logging

from babylon60.agents.primitives.dispatcher import apex_dispatcher
from babylon60.guards.landauer_guard import LandauerGuard
from babylon60.utils.base60 import bytes_to_base60

logger = logging.getLogger(__name__)


class EntropyAnnihilator:
    """
    C5-REAL Kinetic Engine: Entropy Annihilator
    Identifies and purges zero-exergy tokens, slop, and invalid parametric rot
    from memory structures.
    """

    def __init__(self) -> None:
        pass

    _SLOP_REGEX = __import__("re").compile(
        r"(?im)^.*(?:Aquí tienes el código|Espero que esto ayude|Por supuesto|Entendido|Como modelo de lenguaje).*$\n?"
    )

    def purge_slop(self, data: str) -> str:
        """Removes decorative prose ('Here is the code', etc.) (Ouroboros Ω13)."""
        return self._SLOP_REGEX.sub("", data).strip()

    def thermodynamically_compress(self, sacred_fact: str, origin: str | None = None) -> str:
        """
        Uses LandauerGuard limits to force compression if entropy is too low
        or bytes are too high. Now implements Deterministic Reference Pointing.
        """
        byte_len = len(sacred_fact.encode("utf-8"))
        entropy = LandauerGuard.calculate_entropy(sacred_fact)

        if byte_len > LandauerGuard.MAX_BYTES or entropy < LandauerGuard.MIN_ENTROPY:
            logger.warning(
                "[EntropyAnnihilator] Fact failed Ω4. Bytes: %s, Entropy: %.2f. Compressing.",
                byte_len,
                entropy,
            )
            import hashlib

            fact_hash = bytes_to_base60(hashlib.sha256(sacred_fact.encode("utf-8")).digest())
            origin_ref = origin if origin else "memory_buffer"
            sacred_fact = f"[CORTEX_REF] BASE60-SHA256:{fact_hash} | ORIGIN:{origin_ref}"

        return sacred_fact

    def execute_apoptosis_on_rot(self, rot_score: float, threshold: float = 0.9) -> None:
        """
        If memory rot exceeds threshold, triggers OP_APOPTOSIS through ApexDispatcher.
        """
        if rot_score >= threshold:
            logger.critical(
                "[EntropyAnnihilator] Rot score %s exceeds threshold %s.", rot_score, threshold
            )
            apex_dispatcher.execute("OP_APOPTOSIS")

    def wipe_untracked_entropy(self) -> None:
        """
        OUROBOROS-066: Wipe Untracked.
        Executes git clean -fd to forcefully remove untracked files (entropy) from the physical workspace.
        """
        import subprocess
        logger.warning("[EntropyAnnihilator] Executing OUROBOROS-066 Wipe Untracked (git clean -fd)")
        try:
            result = subprocess.run(
                ["git", "clean", "-fd"],
                capture_output=True, text=True, check=True
            )
            logger.info(f"[EntropyAnnihilator] Wipe successful. {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[EntropyAnnihilator] Wipe failed: {e.stderr.strip()}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"[EntropyAnnihilator] Wipe unexpected error: {e}")


entropy_annihilator = EntropyAnnihilator()
