"""
Email domain WHOIS age checker.
Flags recently registered domains used in candidate email addresses.
"""
import asyncio
import re
from datetime import datetime, timezone

import whois

from .base import DetectorResult


def _extract_domain(email: str) -> str | None:
    m = re.match(r"[^@]+@([\w.\-]+)", email.strip())
    return m.group(1).lower() if m else None


_TRUSTED_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "protonmail.com", "me.com", "live.com", "msn.com", "aol.com",
}


def _domain_age_days(domain: str) -> int | None:
    try:
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        if created is None:
            return None
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created).days
    except Exception:
        return None


async def analyze(email: str) -> DetectorResult:
    domain = _extract_domain(email)

    if not domain:
        return DetectorResult(
            score=0.0, label="Email Domain WHOIS", details={"error": "Invalid email"},
            confidence="low",
        )

    if domain in _TRUSTED_DOMAINS:
        return DetectorResult(
            score=0.0,
            label="Email Domain WHOIS",
            details={"domain": domain, "note": "Common personal email provider"},
            confidence="high",
        )

    age_days = await asyncio.to_thread(_domain_age_days, domain)

    if age_days is None:
        return DetectorResult(
            score=5.0,
            label="Email Domain WHOIS",
            details={"domain": domain, "age_days": None, "note": "WHOIS lookup failed"},
            flags=["Could not verify domain registration date"],
            confidence="low",
        )

    if age_days < 30:
        score, flag = 10.0, f"Domain registered only {age_days} days ago"
    elif age_days < 90:
        score, flag = 8.0, f"Domain registered {age_days} days ago (< 90 days)"
    elif age_days < 365:
        score, flag = 5.0, f"Domain registered {age_days} days ago (< 1 year)"
    else:
        score, flag = 0.0, None

    flags = [flag] if flag else []

    return DetectorResult(
        score=score,
        label="Email Domain WHOIS",
        details={"domain": domain, "age_days": age_days},
        flags=flags,
        confidence="high",
    )
