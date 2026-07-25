import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

_SLOP_PATTERNS: list[tuple[str, float]] = [('Aquí tienes el código', 1.0), ('Espero que esto ayude', 1.0), ('Por supuesto[,.]?', 0.8), ('Entendido[,.]?', 0.6), ('Como modelo de lenguaje', 1.0), ('Here is the code', 1.0), ('I hope this helps', 1.0), ('Of course[,.]?', 0.8), ('Understood[,.]?', 0.6), ('As an AI language model', 1.0), ('Claro[,.]?\\s+aquí tienes', 0.9), ('No dudes en preguntar', 0.9), ('Feel free to ask', 0.9), ('Es importante (tener en cuenta|notar|recordar)', 0.8), ("It('s| is) important to (note|remember)", 0.8), ('Cabe destacar que', 0.7), ('¡(Claro|Por supuesto|Excelente)!', 0.8), ("Great[,!]?\\s+(let('s| us)|I('ll| will))", 0.7), ("I'd be happy to", 0.9), ("I('m| am) here to help", 0.9), ('Certainly[,!]?', 0.7), ('Absolutely[,!]?', 0.7), ('Definitivamente[,!]?', 0.6), ('Sin lugar a dudas[,!]?', 0.7), ('A continuación[,:]', 0.5), ("Below you('ll| will) find", 0.5), ('Espero que.*útil', 0.9), ('I hope.*helpful', 0.9)]

def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall('[a-zA-Z0-9áéíóúñüÁÉÍÓÚÑÜ]+', text)]

def _sentences(text: str) -> list[str]:
    parts = re.split('(?<=[.!?¿¡])\\s+', text.strip())
    return [s for s in parts if s]

@dataclass
class LinguisticEntropyReport:
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    unique_words: int = 0
    char_entropy: float = 0.0
    word_entropy: float = 0.0
    bigram_entropy: float = 0.0
    trigram_entropy: float = 0.0
    ttr: float = 0.0
    mattr: float = 0.0
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    burstiness: float = 0.0
    context_rot_score: float = 0.0
    slop_weight_total: float = 0.0
    slop_instances: list[dict[str, Any]] = field(default_factory=list)
    slop_density: float = 0.0
    exergy_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, int):
                d[k] = round(v, 4)
        d['slop_instances_count'] = len(self.slop_instances)
        return d

class LinguisticEntropyDetector:

    def __init__(self) -> None:
        self._compiled_slop: list[tuple[re.Pattern[str], float]] = [(re.compile(pattern, re.IGNORECASE), weight) for pattern, weight in _SLOP_PATTERNS]

    @staticmethod
    def _shannon(items: list[str]) -> float:
        from babylon60.extensions.security.utils import calculate_distribution_entropy
        return calculate_distribution_entropy(Counter(items))

    def calculate_char_entropy(self, text: str) -> float:
        return round(self._shannon(list(text)), 4)

    def calculate_word_entropy(self, text: str) -> float:
        return round(self._shannon(_tokenize(text)), 4)

    def calculate_bigram_entropy(self, text: str) -> float:
        words = _tokenize(text)
        bigrams = [f'{words[i]} {words[i + 1]}' for i in range(len(words) - 1)]
        return round(self._shannon(bigrams), 4)

    def calculate_trigram_entropy(self, text: str) -> float:
        words = _tokenize(text)
        trigrams = [f'{words[i]} {words[i + 1]} {words[i + 2]}' for i in range(len(words) - 2)]
        return round(self._shannon(trigrams), 4)

    @staticmethod
    def calculate_ttr(words: list[str]) -> float:
        if not words:
            return 0.0
        return round(len(set(words)) / len(words), 4)

    @staticmethod
    def calculate_mattr(words: list[str], window: int=50) -> float:
        if len(words) < window:
            if not words:
                return 0.0
            return round(len(set(words)) / len(words), 4)
        ttrs = [len(set(words[i:i + window])) / window for i in range(len(words) - window + 1)]
        return round(sum(ttrs) / len(ttrs), 4)

    @staticmethod
    def _sentence_metrics(text: str) -> tuple[int, float]:
        sents = _sentences(text)
        if not sents:
            return (0.0, 0.0)
        lengths = [len(_tokenize(s)) for s in sents]
        avg = statistics.mean(lengths)
        var = statistics.pvariance(lengths) if len(lengths) > 1 else 0.0
        return (round(avg, 4), round(var, 4))

    @staticmethod
    def _burstiness(words: list[str]) -> float:
        if len(words) < 4:
            return 0.0
        positions: dict[str, list[int]] = {}
        for i, w in enumerate(words):
            positions.setdefault(w, []).append(i)
        gaps: list[float] = []
        for pos_list in positions.values():
            if len(pos_list) > 1:
                for j in range(len(pos_list) - 1):
                    gaps.append(float(pos_list[j + 1] - pos_list[j]))
        if len(gaps) < 2:
            return 0.0
        mu = statistics.mean(gaps)
        sigma = statistics.pstdev(gaps)
        if sigma + mu == 0:
            return 0.0
        return round((sigma - mu) / (sigma + mu), 4)

    @staticmethod
    def _context_rot(text: str, window_size: int=100) -> float:
        words = _tokenize(text)
        if len(words) < window_size * 2:
            return 0.0
        windows: list[float] = []
        for i in range(0, len(words) - window_size, window_size // 2):
            chunk = words[i:i + window_size]
            counts = Counter(chunk)
            from babylon60.extensions.security.utils import calculate_distribution_entropy
            h = calculate_distribution_entropy(counts)
            windows.append(h)
        if len(windows) < 2:
            return 0.0
        first_half = windows[:len(windows) // 2]
        second_half = windows[len(windows) // 2:]
        h_first = sum(first_half) / len(first_half)
        h_second = sum(second_half) / len(second_half)
        if h_first == 0:
            return 0.0
        decay = max(0.0, (h_first - h_second) / h_first)
        return round(min(decay, 1.0), 4)

    def detect_slop(self, text: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for pattern, weight in self._compiled_slop:
            for match in pattern.finditer(text):
                results.append({'pattern': pattern.pattern, 'matched_text': match.group(), 'start': match.start(), 'end': match.end(), 'severity_weight': weight})
        return results

    def analyze(self, text: str) -> LinguisticEntropyReport:
        words = _tokenize(text)
        sents = _sentences(text)
        slop_instances = self.detect_slop(text)
        slop_weight_total = sum(s['severity_weight'] for s in slop_instances)
        slop_density = round(slop_weight_total / max(len(words), 1), 4)
        avg_sl, var_sl = self._sentence_metrics(text)
        report = LinguisticEntropyReport(char_count=len(text), word_count=len(words), sentence_count=len(sents), unique_words=len(set(words)), char_entropy=self.calculate_char_entropy(text), word_entropy=self.calculate_word_entropy(text), bigram_entropy=self.calculate_bigram_entropy(text), trigram_entropy=self.calculate_trigram_entropy(text), ttr=self.calculate_ttr(words), mattr=self.calculate_mattr(words), avg_sentence_length=avg_sl, sentence_length_variance=var_sl, burstiness=self._burstiness(words), context_rot_score=self._context_rot(text), slop_weight_total=round(slop_weight_total, 4), slop_instances=slop_instances, slop_density=slop_density)
        report.exergy_score = self._compute_exergy(report)
        return report

    @staticmethod
    def _compute_exergy(r: LinguisticEntropyReport) -> float:
        exergy: float = 1.0
        exergy -= min(r.slop_density * 4.0, 0.4)
        if r.word_count >= 30:
            if r.word_entropy < 3.0:
                exergy -= 0.2
            elif r.word_entropy < 4.0:
                exergy -= 0.12
            elif r.word_entropy < 4.5:
                exergy -= 0.06
        if r.burstiness < -0.5:
            exergy -= 0.15
        elif r.burstiness < -0.2:
            exergy -= 0.08
        exergy -= r.context_rot_score * 0.15
        if r.word_count > 100 and r.mattr < 0.4:
            exergy -= 0.1
        elif r.word_count > 50 and r.mattr < 0.5:
            exergy -= 0.05
        return round(max(0.0, min(1.0, exergy)), 4)