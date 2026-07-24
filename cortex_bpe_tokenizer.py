# C5-REAL

from typing import List, Dict, Tuple


class BPETokenizer:
    """
    C5-REAL primitive for Byte-Pair Encoding (BPE).
    Transduces unstructured text entropy into discrete tokens for the SSM Core.
    """

    def __init__(self) -> None:
        self.vocab: Dict[str, int] = {chr(i): i for i in range(256)}
        self.inverse_vocab: Dict[int, str] = {i: chr(i) for i in range(256)}
        self.merges: Dict[Tuple[str, str], int] = {}
        self.next_token_id = 256

    def get_stats(self, tokens: List[str]) -> Dict[Tuple[str, str], int]:
        """Calculates frequency of adjacent token pairs."""
        counts: Dict[Tuple[str, str], int] = {}
        for pair in zip(tokens, tokens[1:]):
            counts[pair] = counts.get(pair, 0) + 1
        return counts

    def merge(self, tokens: List[str], pair: Tuple[str, str], new_token: str) -> List[str]:
        """Merges all occurrences of the most frequent pair."""
        new_tokens = []
        i = 0
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens

    def train(self, text: str, num_merges: int) -> None:
        """Trains the BPE model by extracting high-exergy patterns."""
        tokens = list(text)
        for _ in range(num_merges):
            stats = self.get_stats(tokens)
            if not stats:
                break

            best_pair = max(stats, key=stats.get)  # type: ignore
            new_token_str = best_pair[0] + best_pair[1]

            self.merges[best_pair] = self.next_token_id
            self.vocab[new_token_str] = self.next_token_id
            self.inverse_vocab[self.next_token_id] = new_token_str
            self.next_token_id += 1

            tokens = self.merge(tokens, best_pair, new_token_str)

    def encode(self, text: str) -> List[int]:
        """Encodes text into kinetic token IDs."""
        tokens = list(text)
        while len(tokens) > 1:
            stats = self.get_stats(tokens)
            pair_to_merge = None
            for pair in stats:
                if pair in self.merges:
                    pair_to_merge = pair
                    break

            if not pair_to_merge:
                break

            new_token_str = pair_to_merge[0] + pair_to_merge[1]
            tokens = self.merge(tokens, pair_to_merge, new_token_str)

        return [self.vocab[t] for t in tokens]

    def decode(self, token_ids: List[int]) -> str:
        """Decodes token IDs back to human-readable strings."""
        return "".join(self.inverse_vocab[t] for t in token_ids)
