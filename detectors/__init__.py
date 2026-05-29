from utils.pdf_to_text import extract as _pdf_to_text

from .llm_text import analyze as _llm
from .similarity import analyze as _sim
from .pdf_scanner import analyze as _pdf
from .whois_check import analyze as _whois


async def run_all(pdf_bytes: bytes, jd: str, email: str = "") -> dict:
    resume_text = await _pdf_to_text(pdf_bytes)

    results: dict = {}

    # High priority — both async now
    results["llm_detection"] = (await _llm(resume_text, jd)).model_dump()
    results["cross_resume_similarity"] = _sim(resume_text, jd).model_dump()

    # Medium priority
    results["pdf_scanner"] = _pdf(pdf_bytes).model_dump()

    if email.strip():
        results["whois_check"] = (await _whois(email)).model_dump()

    scored = [r["score"] for r in results.values()]
    results["overall_score"] = round(sum(scored) / len(scored), 1)

    return results
