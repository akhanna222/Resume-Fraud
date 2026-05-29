"""
LLM-generated text detector.
Signals: keyword overlap with JD, sentence burstiness, lexical diversity.
"""
import math
import re
from collections import Counter

from .base import DetectorResult

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "i", "we", "you", "he", "she", "they", "it",
    "my", "our", "your", "his", "her", "their", "its", "this", "that",
}


def _keywords(text: str) -> list[str]:
    return [
        w for w in re.findall(r"\b[a-z]{3,}\b", text.lower())
        if w not in _STOPWORDS
    ]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]


def _keyword_overlap(resume: str, jd: str) -> float:
    jd_keys = set(_keywords(jd))
    resume_keys = set(_keywords(resume))
    return len(resume_keys & jd_keys) / len(jd_keys) if jd_keys else 0.0


def _burstiness(text: str) -> float:
    """Coefficient of variation of sentence lengths. LLM text: ~0.2–0.4; human: ~0.5–1.0."""
    lengths = [len(s.split()) for s in _sentences(text)]
    if len(lengths) < 3:
        return 1.0
    mean = sum(lengths) / len(lengths)
    std = math.sqrt(sum((l - mean) ** 2 for l in lengths) / len(lengths))
    return std / mean if mean else 1.0


def _lexical_diversity(text: str) -> float:
    """Type-token ratio. Lower = more repetitive = more LLM-like."""
    tokens = _keywords(text)
    return len(set(tokens)) / len(tokens) if tokens else 1.0


def analyze(resume_text: str, jd_text: str) -> DetectorResult:
    overlap = _keyword_overlap(resume_text, jd_text)
    burstiness = _burstiness(resume_text)
    diversity = _lexical_diversity(resume_text)

    # Each sub-score: 0–10 where 10 = most suspicious
    overlap_score = min(max((overlap - 0.45) / 0.40 * 10, 0), 10)   # flags >45% overlap
    burstiness_score = min(max((0.50 - burstiness) / 0.30 * 10, 0), 10)  # flags CV<0.50
    diversity_score = min(max((0.55 - diversity) / 0.20 * 10, 0), 10)    # flags TTR<0.55

    score = overlap_score * 0.50 + burstiness_score * 0.30 + diversity_score * 0.20

    flags = []
    if overlap >= 0.70:
        flags.append(f"Keyword overlap with JD is very high ({overlap:.0%})")
    if burstiness < 0.30:
        flags.append(f"Sentence length uniformity suggests LLM authorship (CV={burstiness:.2f})")
    if diversity < 0.45:
        flags.append(f"Low lexical diversity (TTR={diversity:.2f})")

    return DetectorResult(
        score=round(min(score, 10), 1),
        label="LLM Text Detection",
        details={
            "keyword_overlap_pct": round(overlap * 100, 1),
            "sentence_burstiness_cv": round(burstiness, 3),
            "lexical_diversity_ttr": round(diversity, 3),
        },
        flags=flags,
        confidence="medium",
    )
