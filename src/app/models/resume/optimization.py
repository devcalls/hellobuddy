from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OptimizationMode(str, Enum):
    GENERAL_ATS = "general_ats"
    TARGETED_JD = "targeted_jd"


class ResumeSection(str, Enum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    PROJECTS = "projects"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"


class ChangeType(str, Enum):
    REWRITE = "rewrite"
    REORDER = "reorder"
    GROUP = "group"
    REMOVE = "remove"
    NORMALIZE = "normalize"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class OptimizationGuideline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    enabled: bool = True
    applies_to: list[ResumeSection] = Field(default_factory=list)


class OptimizationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guideline_id: str
    severity: FindingSeverity
    description: str
    original_text: str | None = None


class OptimizationChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_type: ChangeType
    guideline_id: str
    original_text: str | None = None
    optimized_text: str | None = None
    reason: str


class SectionOptimizationResult(BaseModel):
    """
    Generic LLM response for optimizing one ResumeAST section.

    optimized_content is intentionally Any here.

    ResumeOptimizerService is responsible for converting it into
    the correct ResumeAST/Pydantic type.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection

    optimized: bool = False

    original_content: Any

    optimized_content: Any

    findings: list[OptimizationFinding] = Field(default_factory=list)

    changes: list[OptimizationChange] = Field(default_factory=list)

    validation_passed: bool = True

    validation_errors: list[str] = Field(default_factory=list)


class ResumeOptimizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: OptimizationMode = OptimizationMode.GENERAL_ATS

    sections: list[ResumeSection] = Field(
        default_factory=lambda: [
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.SKILLS,
            ResumeSection.PROJECTS,
            ResumeSection.EDUCATION,
            ResumeSection.CERTIFICATIONS,
        ]
    )

    guidelines: list[OptimizationGuideline] = Field(default_factory=list)


class ResumeOptimizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: OptimizationMode

    original_resume: dict[str, Any]

    optimized_resume: dict[str, Any]

    sections: list[SectionOptimizationResult] = Field(default_factory=list)

    validation_passed: bool = True

    validation_errors: list[str] = Field(default_factory=list)
