from pydantic import BaseModel


class DetectorResult(BaseModel):
    score: float        # 0–10; higher = more suspicious
    label: str
    details: dict
    flags: list[str] = []
    confidence: str = "medium"   # low | medium | high
