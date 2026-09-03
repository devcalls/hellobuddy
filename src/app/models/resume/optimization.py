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

    # Keep this as a string rather than Any.
    original_text: str = ""


class OptimizationChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_type: ChangeType
    guideline_id: str

    # Avoid nullable fields in the Gemini response schema.
    original_text: str = ""
    optimized_text: str = ""

    reason: str


class SectionOptimizationLLMResult(BaseModel):
    """
    Gemini-facing response model.

    IMPORTANT:
    This model intentionally does NOT contain Any fields.

    optimized_content_json contains the optimized section serialized
    as a JSON string. ResumeOptimizerService is responsible for:

        1. Parsing optimized_content_json.
        2. Validating it against the correct ResumeAST nested model.
        3. Applying it only if validation succeeds.
    """

    model_config = ConfigDict(extra="forbid")

    section: ResumeSection

    optimized: bool = False

    optimized_content_json: str = ""

    findings: list[OptimizationFinding] = Field(default_factory=list)

    changes: list[OptimizationChange] = Field(default_factory=list)


class SectionOptimizationResult(BaseModel):
    """
    Application-level result for optimizing one ResumeAST section.

    This is NOT used directly as the Gemini response schema.

    original_content and optimized_content are allowed to be heterogeneous
    because different ResumeAST sections have different Pydantic types.
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
