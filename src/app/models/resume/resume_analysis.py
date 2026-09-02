from typing import Optional

from pydantic import BaseModel, Field

## What we discovered about the resume.

class KeywordMatch(BaseModel):
    keyword: str
    matched: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None


class SkillGap(BaseModel):
    skill: str
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None


class FormattingIssue(BaseModel):
    category: str
    severity: str
    message: str


class AtsAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)

    keyword_score: float
    formatting_score: float
    structure_score: float

    keyword_matches: list[KeywordMatch] = Field(
        default_factory=list
    )

    skill_gaps: list[SkillGap] = Field(
        default_factory=list
    )

    formatting_issues: list[FormattingIssue] = Field(
        default_factory=list
    )