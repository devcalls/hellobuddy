from typing import Optional

from pydantic import BaseModel


class ResumeChange(BaseModel):
    section: str
    location: str

    original: str
    suggested: str

    reason: str

    evidence: list[str] = []

    confidence: float

    accepted: Optional[bool] = None


class ResumeOptimization(BaseModel):
    changes: list[ResumeChange] = []

    overall_summary: Optional[str] = None