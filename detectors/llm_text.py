"""
LLM-generated text detector.

Two-layer approach:
  1. Heuristics — keyword overlap with JD, sentence burstiness, lexical diversity.
  2. OpenAI GPT-4o — structured prompt returns an AI-likelihood score 0-10
     with reasoning. Used when OPENAI_API_KEY is present.

Final score = heuristic (40%) + OpenAI (60%) when key available, else heuristic only.
"""
import json
import math
import os
import re

from openai import AsyncOpenAI

from .base import DetectorResult

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "i", "we", "you", "he", "she", "they", "it",
    "my", "our", "your", "his", "her", "their", "its", "this", "that",
}

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-your"):
        return None
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=key)
    return _client


# ── Heuristics ────────────────────────────────────────────────────────────────

def _keywords(text: str) -> list[str]:
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in _STOPWORDS]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]


def _keyword_overlap(resume: str, jd: str) -> float:
    jd_keys = set(_keywords(jd))
    return len(set(_keywords(resume)) & jd_keys) / len(jd_keys) if jd_keys else 0.0


def _burstiness(text: str) -> float:
    """CV of sentence word-counts. LLM ~0.2–0.4; human ~0.5–1.0."""
    lengths = [len(s.split()) for s in _sentences(text)]
    if len(lengths) < 3:
        return 1.0
    mean = sum(lengths) / len(lengths)
    std = math.sqrt(sum((l - mean) ** 2 for l in lengths) / len(lengths))
    return std / mean if mean else 1.0


def _lexical_diversity(text: str) -> float:
    tokens = _keywords(text)
    return len(set(tokens)) / len(tokens) if tokens else 1.0


def _heuristic_score(resume_text: str, jd_text: str) -> tuple[float, dict, list[str]]:
    overlap = _keyword_overlap(resume_text, jd_text)
    burstiness = _burstiness(resume_text)
    diversity = _lexical_diversity(resume_text)

    s_overlap = min(max((overlap - 0.45) / 0.40 * 10, 0), 10)
    s_burst = min(max((0.50 - burstiness) / 0.30 * 10, 0), 10)
    s_div = min(max((0.55 - diversity) / 0.20 * 10, 0), 10)
    score = s_overlap * 0.50 + s_burst * 0.30 + s_div * 0.20

    flags = []
    if overlap >= 0.70:
        flags.append(f"Keyword overlap with JD is very high ({overlap:.0%})")
    if burstiness < 0.30:
        flags.append(f"Unnaturally uniform sentence lengths (CV={burstiness:.2f}) — likely LLM")
    if diversity < 0.45:
        flags.append(f"Low lexical diversity (TTR={diversity:.2f})")

    return round(min(score, 10), 1), {
        "keyword_overlap_pct": round(overlap * 100, 1),
        "sentence_burstiness_cv": round(burstiness, 3),
        "lexical_diversity_ttr": round(diversity, 3),
    }, flags


# ── OpenAI detector ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a senior fraud analyst specialising in AI-generated resume detection.
Analyse the provided resume text against the job description.

Return ONLY valid JSON with this exact schema:
{
  "ai_likelihood_score": <integer 0-10>,
  "confidence": "low" | "medium" | "high",
  "signals": [<short string>, ...],
  "reasoning": "<one sentence>"
}

Scoring guide:
  0-2  Clearly human-written — personal anecdotes, natural imperfections, varied style
  3-4  Mostly human — minor stylistic uniformity
  5-6  Ambiguous — some LLM patterns present
  7-8  Likely AI-generated — templated structure, verbatim JD mirroring, flat prose
  9-10 Almost certainly AI — no authentic voice, perfect keyword match, robotic cadence
"""


async def _openai_score(resume_text: str, jd_text: str) -> tuple[float, list[str], str] | None:
    client = _get_client()
    if client is None:
        return None

    user_msg = f"### JOB DESCRIPTION\n{jd_text}\n\n### RESUME\n{resume_text}"
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_tokens=512,
            temperature=0,
        )
        data = json.loads(resp.choices[0].message.content)
        return (
            float(data.get("ai_likelihood_score", 5)),
            data.get("signals", []),
            data.get("reasoning", ""),
        )
    except Exception as e:
        return None


# ── Public interface ──────────────────────────────────────────────────────────

async def analyze(resume_text: str, jd_text: str) -> DetectorResult:
    h_score, h_details, h_flags = _heuristic_score(resume_text, jd_text)
    openai_result = await _openai_score(resume_text, jd_text)

    if openai_result:
        ai_score, ai_signals, ai_reasoning = openai_result
        final_score = round(h_score * 0.40 + ai_score * 0.60, 1)
        details = {
            **h_details,
            "openai_ai_likelihood": ai_score,
            "openai_reasoning": ai_reasoning,
        }
        flags = h_flags + [f"[GPT-4o] {s}" for s in ai_signals]
        confidence = "high"
        method = "heuristics + GPT-4o"
    else:
        final_score = h_score
        details = {**h_details, "openai_reasoning": "OpenAI key not configured — heuristics only"}
        flags = h_flags
        confidence = "medium"
        method = "heuristics only"

    return DetectorResult(
        score=round(min(final_score, 10), 1),
        label=f"LLM Text Detection ({method})",
        details=details,
        flags=flags,
        confidence=confidence,
    )
