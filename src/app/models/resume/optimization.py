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


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class FindingCategory(str, Enum):
    STYLE = "style"
    ATS = "ats"
    CONTENT = "content"
    EVIDENCE = "evidence"
    STRUCTURE = "structure"


class ChangeType(str, Enum):
    REWRITE = "rewrite"
    NORMALIZE = "normalize"
    REORDER = "reorder"


class OptimizationGuideline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    enabled: bool = True
    applies_to: list[ResumeSection] = Field(default_factory=list)


class OptimizationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guideline_id: str
    category: FindingCategory = FindingCategory.CONTENT
    severity: FindingSeverity
    description: str
    original_text: str = ""


class OptimizationChange(BaseModel):
    """
    A proposed mutation to an existing ResumeAST field.

    The LLM does not reconstruct the containing AST object.
    It only proposes a text replacement.
    """

    model_config = ConfigDict(extra="forbid")

    record_id: str
    field: str

    change_type: ChangeType = ChangeType.REWRITE

    optimized_text: str

    guideline_id: str
    reason: str


class SectionOptimizationLLMResult(BaseModel):
    """
    Provider-neutral structured response from an LLM.

    IMPORTANT:
    This contains proposals only.
    It does not contain ResumeAST objects.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection
    optimized: bool = False

    findings: list[OptimizationFinding] = Field(
        default_factory=list
    )

    changes: list[OptimizationChange] = Field(
        default_factory=list
    )


class SectionOptimizationResult(BaseModel):
    """
    Application-level result after Python has validated/applied
    the LLM proposals.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection
    optimized: bool = False

    findings: list[OptimizationFinding] = Field(
        default_factory=list
    )

    changes: list[OptimizationChange] = Field(
        default_factory=list
    )

    applied_changes: int = 0

    validation_passed: bool = True

    validation_errors: list[str] = Field(
        default_factory=list
    )


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

    guidelines: list[OptimizationGuideline] = Field(
        default_factory=list
    )

    job_description: str | None = None


class ResumeOptimizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: OptimizationMode

    original_resume: dict[str, Any]
    optimized_resume: dict[str, Any]

    sections: list[SectionOptimizationResult] = Field(
        default_factory=list
    )

    validation_passed: bool = True

    validation_errors: list[str] = Field(
        default_factory=list
    )