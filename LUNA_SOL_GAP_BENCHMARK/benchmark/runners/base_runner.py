# Base Runner Interface for LUNA_SOL_GAP_BENCHMARK
from abc import ABC, abstractmethod
from typing import Tuple


class BaseRunner(ABC):
    @abstractmethod
    def generate(self, prompt: str, use_think: bool = False) -> Tuple[str, int]:
        """
        Generate candidate response text and return (response_text, token_count).
        """
        pass
