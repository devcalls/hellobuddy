from enum import Enum

from pydantic import BaseModel, Field
from app.models.resume.resume_ast import ResumeAST

class ConfidenceLevel(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    GOOD = "GOOD"
    HIGH = "HIGH"


class ConfidenceScore(BaseModel):
    """
    Application-calculated confidence for resume extraction.

    All scores are percentages from 0 to 100.
    """

    score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall extraction confidence."
    )

    level: ConfidenceLevel = Field(
        description="Qualitative interpretation of the overall score."
    )

    evidence_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Confidence based on extraction evidence."
    )

    completeness_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Confidence based on completeness of extracted sections."
    )

    normalization_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Confidence based on successful normalization of dates and other structured values."
    )
    
class ResumeAnalysis(BaseModel):
    """
    Result of analyzing a parsed resume.
    """

    resume: ResumeAST

    confidence: ConfidenceScore