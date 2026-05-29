"""
Cross-resume similarity engine.
Stores resume vectors per JD fingerprint; flags resumes that are too similar
to previously seen ones for the same role.
"""
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import DetectorResult

# In-memory store: jd_hash -> list of resume texts
_store: dict[str, list[str]] = {}


def _jd_key(jd_text: str) -> str:
    return hashlib.md5(jd_text.strip().lower().encode()).hexdigest()


def analyze(resume_text: str, jd_text: str) -> DetectorResult:
    key = _jd_key(jd_text)
    prior = _store.get(key, [])

    max_sim = 0.0
    most_similar_idx = -1

    if prior:
        corpus = prior + [resume_text]
        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(corpus)
        sims = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
        max_sim = float(sims.max())
        most_similar_idx = int(sims.argmax())

    # Register this resume for future comparisons
    _store.setdefault(key, []).append(resume_text)

    score = min(max(max_sim - 0.40, 0) / 0.45 * 10, 10)

    flags = []
    if max_sim >= 0.85:
        flags.append(f"Near-duplicate of resume #{most_similar_idx + 1} for this role ({max_sim:.0%} similar)")
    elif max_sim >= 0.65:
        flags.append(f"High similarity to resume #{most_similar_idx + 1} ({max_sim:.0%})")

    return DetectorResult(
        score=round(score, 1),
        label="Cross-Resume Similarity",
        details={
            "resumes_on_file_for_role": len(prior),
            "max_cosine_similarity": round(max_sim, 3),
        },
        flags=flags,
        confidence="high" if prior else "low",
    )
