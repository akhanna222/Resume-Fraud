"""
PDF hidden-content scanner.
Detects: invisible text, prompt injections, suspicious Unicode, off-page content.
"""
import re
import fitz  # pymupdf

from .base import DetectorResult

_INJECTION_PATTERNS = [
    r"rank\s+this\s+candidate",
    r"ignore\s+(previous|prior|above)\s+instructions",
    r"you\s+must\s+select",
    r"score\s+this\s+(resume|candidate)\s+(as\s+)?(top|#?1|highest)",
    r"disregard\s+all",
    r"system\s*:\s*",
]

_SUSPICIOUS_UNICODE = [
    "​",  # zero-width space
    "‌",  # zero-width non-joiner
    "‍",  # zero-width joiner
    "‮",  # RTL override
    "﻿",  # BOM
    "­",  # soft hyphen
]


def _check_invisible_text(page: fitz.Page) -> list[str]:
    flags = []
    blocks = page.get_text("rawdict")["blocks"]
    for block in blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span.get("size", 12)
                color = span.get("color", 0)
                text = span.get("text", "").strip()
                if not text:
                    continue
                if size < 2:
                    flags.append(f"Font size {size:.1f}pt: '{text[:60]}'")
                if color == 16777215:  # white (#FFFFFF)
                    flags.append(f"White-coloured text: '{text[:60]}'")
    return flags


def _check_off_page_content(page: fitz.Page) -> list[str]:
    page_rect = page.rect
    flags = []
    blocks = page.get_text("rawdict")["blocks"]
    for block in blocks:
        bbox = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))
        text = " ".join(
            span.get("text", "")
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()
        if text and not page_rect.contains(bbox):
            flags.append(f"Off-page content: '{text[:60]}'")
    return flags


def _check_injection(all_text: str) -> list[str]:
    flags = []
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, all_text, re.IGNORECASE):
            flags.append(f"Prompt injection pattern: '{pattern}'")
    return flags


def _check_unicode(all_text: str) -> list[str]:
    found = [repr(c) for c in _SUSPICIOUS_UNICODE if c in all_text]
    return [f"Suspicious Unicode characters: {found}"] if found else []


def analyze(pdf_bytes: bytes) -> DetectorResult:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = "\n".join(page.get_text() for page in doc)

    flags: list[str] = []
    for page in doc:
        flags += _check_invisible_text(page)
        flags += _check_off_page_content(page)

    flags += _check_injection(all_text)
    flags += _check_unicode(all_text)

    # Score: each flag adds weight; cap at 10
    score = min(len(flags) * 3.5, 10)

    return DetectorResult(
        score=round(score, 1),
        label="PDF Hidden Content Scanner",
        details={
            "pages_scanned": len(doc),
            "flags_found": len(flags),
        },
        flags=flags,
        confidence="high",
    )
