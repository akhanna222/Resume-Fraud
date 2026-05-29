"""
LLM-generated text detector — three-layer scoring:

  Layer 1 · Heuristics (20%)
    keyword overlap with JD, sentence burstiness CV, lexical diversity TTR

  Layer 2 · Tone analysis (20%)
    LLM buzzword density, passive voice ratio, sentence opener uniformity,
    filler phrase detection — patterns that mark "corporate LLM" prose

  Layer 3 · GPT-4o (60%)
    Structured prompt asks the model to score both AI-likelihood AND tone
    authenticity, returning JSON with per-signal breakdown.

Falls back to layers 1+2 only (50/50) when OpenAI key is absent.
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

# Classic LLM / corporate-resume buzzwords and filler phrases
_LLM_BUZZWORDS = [
    "leveraged", "spearheaded", "pioneered", "orchestrated", "synergized",
    "results-driven", "detail-oriented", "proactive", "self-starter",
    "passionate about", "strong communication skills", "team player",
    "go-getter", "dynamic", "strategic thinker", "thought leader",
    "impactful", "cutting-edge", "best-in-class", "world-class",
    "innovative solutions", "streamlined", "optimized processes",
    "collaborated cross-functionally", "stakeholder", "deliverables",
    "actionable insights", "robust", "scalable solutions", "fast-paced",
    "demonstrated ability", "proven track record", "exceeded expectations",
    "value-add", "synergy", "bandwidth", "circle back", "deep dive",
]

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-your"):
        return None
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=key)
    return _client


# ── Layer 1: Heuristics ───────────────────────────────────────────────────────

def _keywords(text: str) -> list[str]:
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in _STOPWORDS]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]


def _keyword_overlap(resume: str, jd: str) -> float:
    jd_keys = set(_keywords(jd))
    return len(set(_keywords(resume)) & jd_keys) / len(jd_keys) if jd_keys else 0.0


def _burstiness(text: str) -> float:
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
        flags.append(f"Keyword overlap with JD very high ({overlap:.0%})")
    if burstiness < 0.30:
        flags.append(f"Unnaturally uniform sentence lengths (CV={burstiness:.2f})")
    if diversity < 0.45:
        flags.append(f"Low lexical diversity (TTR={diversity:.2f})")

    return round(min(score, 10), 1), {
        "keyword_overlap_pct": round(overlap * 100, 1),
        "sentence_burstiness_cv": round(burstiness, 3),
        "lexical_diversity_ttr": round(diversity, 3),
    }, flags


# ── Layer 2: Tone analysis ────────────────────────────────────────────────────

def _passive_voice_ratio(text: str) -> float:
    """Rough passive-voice detector: 'was/were/been/is/are + past participle'."""
    sentences = _sentences(text)
    if not sentences:
        return 0.0
    passive_re = re.compile(
        r"\b(was|were|been|is|are|be)\s+\w+ed\b", re.IGNORECASE
    )
    passive_count = sum(1 for s in sentences if passive_re.search(s))
    return passive_count / len(sentences)


def _buzzword_density(text: str) -> float:
    """Fraction of buzzwords found per 100 words."""
    lower = text.lower()
    words = lower.split()
    if not words:
        return 0.0
    hits = sum(1 for phrase in _LLM_BUZZWORDS if phrase in lower)
    return hits / (len(words) / 100)


def _opener_uniformity(text: str) -> float:
    """Fraction of sentences starting with the same first word — LLM lists often do."""
    sentences = _sentences(text)
    if len(sentences) < 4:
        return 0.0
    openers = [s.split()[0].lower() for s in sentences if s.split()]
    most_common_count = max(openers.count(w) for w in set(openers))
    return most_common_count / len(sentences)


def _tone_score(resume_text: str) -> tuple[float, dict, list[str]]:
    passive = _passive_voice_ratio(resume_text)
    buzz = _buzzword_density(resume_text)
    opener = _opener_uniformity(resume_text)

    s_passive = min(passive / 0.50 * 10, 10)         # >50% passive = very suspicious
    s_buzz = min(buzz / 3.0 * 10, 10)                # >3 buzzwords/100 words = suspicious
    s_opener = min(max(opener - 0.25, 0) / 0.35 * 10, 10)  # >25% same opener = suspicious

    score = s_passive * 0.30 + s_buzz * 0.50 + s_opener * 0.20

    flags = []
    if passive >= 0.35:
        flags.append(f"High passive voice ratio ({passive:.0%} of sentences)")
    if buzz >= 2.0:
        flags.append(f"LLM buzzword density {buzz:.1f}/100 words")
    if opener >= 0.35:
        flags.append(f"Repetitive sentence openers ({opener:.0%} sentences start the same way)")

    return round(min(score, 10), 1), {
        "passive_voice_ratio": round(passive, 3),
        "buzzword_density_per_100w": round(buzz, 2),
        "opener_uniformity": round(opener, 3),
    }, flags


# ── Layer 3: GPT-4o ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a senior fraud analyst specialising in AI-generated resume detection.
Analyse the resume against the job description, focusing on two dimensions:

1. AI AUTHORSHIP — does the text read like an LLM wrote it?
2. TONE AUTHENTICITY — does the writing feel like a real human professional,
   or does it sound like polished corporate template prose?

Tone red-flags: buzzwords (leveraged, spearheaded, results-driven), no personal
anecdotes, every sentence structured identically, no contractions or colloquial
language, hyper-positive framing with no nuance.

Return ONLY valid JSON with this exact schema:
{
  "ai_likelihood_score": <integer 0-10>,
  "tone_authenticity_score": <integer 0-10>,
  "confidence": "low" | "medium" | "high",
  "tone_signals": [<short string>, ...],
  "authorship_signals": [<short string>, ...],
  "reasoning": "<one sentence overall verdict>"
}

Scoring (both dimensions):
  0-2  Clearly human / authentic tone
  3-4  Mostly human, minor red flags
  5-6  Ambiguous
  7-8  Likely AI / corporate template prose
  9-10 Almost certainly AI / robotic, impersonal tone
"""


async def _openai_score(resume_text: str, jd_text: str) -> dict | None:
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
            max_tokens=600,
            temperature=0,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None


# ── Public interface ──────────────────────────────────────────────────────────

async def analyze(resume_text: str, jd_text: str) -> DetectorResult:
    h_score, h_details, h_flags = _heuristic_score(resume_text, jd_text)
    t_score, t_details, t_flags = _tone_score(resume_text)
    openai_result = await _openai_score(resume_text, jd_text)

    if openai_result:
        ai_score = float(openai_result.get("ai_likelihood_score", 5))
        tone_score = float(openai_result.get("tone_authenticity_score", 5))
        gpt_combined = (ai_score + tone_score) / 2

        final_score = h_score * 0.20 + t_score * 0.20 + gpt_combined * 0.60

        details = {
            **h_details,
            **t_details,
            "gpt4o_ai_likelihood": ai_score,
            "gpt4o_tone_authenticity": tone_score,
            "gpt4o_reasoning": openai_result.get("reasoning", ""),
        }
        flags = (
            h_flags
            + t_flags
            + [f"[tone] {s}" for s in openai_result.get("tone_signals", [])]
            + [f"[authorship] {s}" for s in openai_result.get("authorship_signals", [])]
        )
        confidence = openai_result.get("confidence", "high")
        method = "heuristics + tone + GPT-4o"
    else:
        final_score = h_score * 0.50 + t_score * 0.50
        details = {
            **h_details,
            **t_details,
            "gpt4o_reasoning": "OpenAI key not configured — heuristics + tone only",
        }
        flags = h_flags + t_flags
        confidence = "medium"
        method = "heuristics + tone"

    return DetectorResult(
        score=round(min(final_score, 10), 1),
        label=f"LLM Text & Tone Detection ({method})",
        details=details,
        flags=flags,
        confidence=confidence,
    )
