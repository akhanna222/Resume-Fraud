import fitz

from .llm_text import analyze as _llm
from .similarity import analyze as _sim
from .pdf_scanner import analyze as _pdf
from .whois_check import analyze as _whois


async def run_all(pdf_bytes: bytes, jd: str, email: str = "") -> dict:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    resume_text = "\n".join(page.get_text() for page in doc)

    results: dict = {}

    # High priority
    results["llm_detection"] = _llm(resume_text, jd).model_dump()
    results["cross_resume_similarity"] = _sim(resume_text, jd).model_dump()

    # Medium priority
    results["pdf_scanner"] = _pdf(pdf_bytes).model_dump()

    if email.strip():
        results["whois_check"] = (await _whois(email)).model_dump()

    scored = [r["score"] for r in results.values()]
    results["overall_score"] = round(sum(scored) / len(scored), 1)

    return results
