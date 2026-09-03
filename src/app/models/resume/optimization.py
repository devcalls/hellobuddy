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


class FindingCategory(str, Enum):
    STYLE = "style"
    ATS = "ats"
    CONTENT = "content"
    EVIDENCE = "evidence"
    STRUCTURE = "structure"


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
    model_config = ConfigDict(extra="forbid")

    change_type: ChangeType
    guideline_id: str
    original_text: str = ""
    optimized_text: str = ""
    reason: str


class SectionOptimizationLLMResult(BaseModel):
    """
    Strict schema exposed to Gemini.

    Important:
    optimized_content_json deliberately remains a string.

    Gemini generates:
        outer JSON
            |
            +-- optimized_content_json
                    |
                    +-- JSON representation of actual AST section

    Python subsequently parses and validates that inner JSON against
    the canonical ResumeAST models.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection
    optimized: bool = False

    optimized_content_json: str = ""

    findings: list[OptimizationFinding] = Field(
        default_factory=list
    )

    changes: list[OptimizationChange] = Field(
        default_factory=list
    )


class SectionOptimizationResult(BaseModel):
    """
    Application-level result.

    This model is NOT sent to Gemini because it contains heterogeneous
    Any fields.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection

    optimized: bool = False

    original_content: Any
    optimized_content: Any

    findings: list[OptimizationFinding] = Field(
        default_factory=list
    )

    changes: list[OptimizationChange] = Field(
        default_factory=list
    )

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