"""
PDF → text via GPT-4o vision.
Each page is rendered as a base64 PNG and sent to the vision API.
Falls back to PyMuPDF plain-text extraction if the key is missing.
"""
import base64
import os

import fitz
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-your"):
        return None
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=key)
    return _client


def _page_to_base64(page: fitz.Page, dpi: int = 150) -> str:
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return base64.b64encode(pix.tobytes("png")).decode()


async def extract(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    client = _get_client()

    if client is None:
        return "\n".join(page.get_text() for page in doc)

    pages_b64 = [_page_to_base64(p) for p in doc]

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Extract ALL text from this resume PDF exactly as written. "
                        "Preserve section headings, bullet points, dates, and formatting. "
                        "Return plain text only — no commentary."
                    ),
                },
                *[
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
                    }
                    for b64 in pages_b64
                ],
            ],
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
        temperature=0,
    )
    return response.choices[0].message.content or ""
