"""
Cross-resume similarity engine — two layers:

1. Semantic (OpenAI embeddings): cosine similarity between resume and JD embeddings.
   Catches paraphrasing and synonym substitution that TF-IDF misses.
   Flags resumes that mirror the JD meaning even with different words.

2. Cross-resume (TF-IDF): cosine similarity against all prior resumes submitted
   for the same role. Flags near-duplicate submissions (bot farms, shared templates).

Final score = semantic_jd_score (60%) + cross_resume_score (40%).
Falls back to cross-resume only when OpenAI key is absent.
"""
import hashlib
import os

import numpy as np
from openai import AsyncOpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import DetectorResult

# In-memory store: jd_hash -> {"texts": [...], "embeddings": [...]}
_store: dict[str, dict] = {}

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-your"):
        return None
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=key)
    return _client


def _jd_key(jd_text: str) -> str:
    return hashlib.md5(jd_text.strip().lower().encode()).hexdigest()


async def _embed(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    if client is None:
        return []
    resp = await client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [item.embedding for item in resp.data]


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


# ── Cross-resume TF-IDF ───────────────────────────────────────────────────────

def _cross_resume_score(key: str, resume_text: str) -> tuple[float, int]:
    prior_texts = _store.get(key, {}).get("texts", [])
    if not prior_texts:
        return 0.0, -1
    corpus = prior_texts + [resume_text]
    tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(corpus)
    sims = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
    return float(sims.max()), int(sims.argmax())


# ── Semantic JD similarity ────────────────────────────────────────────────────

async def _semantic_jd_score(resume_text: str, jd_text: str) -> float | None:
    embeddings = await _embed([resume_text, jd_text])
    if len(embeddings) < 2:
        return None
    return _cosine(embeddings[0], embeddings[1])


# ── Public interface ──────────────────────────────────────────────────────────

async def analyze(resume_text: str, jd_text: str) -> DetectorResult:
    key = _jd_key(jd_text)
    prior_count = len(_store.get(key, {}).get("texts", []))

    # Run both layers
    cross_sim, similar_idx = _cross_resume_score(key, resume_text)
    jd_sim = await _semantic_jd_score(resume_text, jd_text)

    # Register resume for future comparisons
    bucket = _store.setdefault(key, {"texts": [], "embeddings": []})
    bucket["texts"].append(resume_text)

    # Scoring
    cross_score = min(max((cross_sim - 0.40) / 0.45 * 10, 0), 10)

    flags: list[str] = []

    if cross_sim >= 0.85:
        flags.append(f"Near-duplicate of resume #{similar_idx + 1} for this role (TF-IDF {cross_sim:.0%})")
    elif cross_sim >= 0.65:
        flags.append(f"High similarity to resume #{similar_idx + 1} (TF-IDF {cross_sim:.0%})")

    if jd_sim is not None:
        # High semantic overlap with JD = candidate may have mirrored JD language
        # >0.88 is suspicious; most honest resumes sit ~0.70-0.82
        jd_score = min(max((jd_sim - 0.82) / 0.12 * 10, 0), 10)
        final_score = jd_score * 0.60 + cross_score * 0.40
        if jd_sim >= 0.90:
            flags.append(f"Resume semantically mirrors JD (embedding similarity {jd_sim:.2f}) — possible LLM tailoring")
        elif jd_sim >= 0.86:
            flags.append(f"High semantic overlap with JD ({jd_sim:.2f}) — review for verbatim mirroring")
        details = {
            "semantic_jd_similarity": round(jd_sim, 3),
            "cross_resume_tfidf_similarity": round(cross_sim, 3),
            "resumes_on_file_for_role": prior_count,
            "method": "embeddings + TF-IDF",
        }
        confidence = "high"
    else:
        final_score = cross_score
        details = {
            "cross_resume_tfidf_similarity": round(cross_sim, 3),
            "resumes_on_file_for_role": prior_count,
            "method": "TF-IDF only (no OpenAI key)",
        }
        confidence = "high" if prior_count > 0 else "low"

    return DetectorResult(
        score=round(min(final_score, 10), 1),
        label="Resume–JD Similarity & Cross-Resume",
        details=details,
        flags=flags,
        confidence=confidence,
    )
