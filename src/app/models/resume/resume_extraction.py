"""
LLM-facing resume extraction models.

These models describe semantic facts extracted from the source document.
They intentionally do not contain application-owned IDs or metadata.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(
        description="Exact or near-exact source text supporting the fact."
    )
    source_section: str | None = Field(default=None)
    quality: Literal["high", "medium", "low"] = Field(default="high")
    reason: str | None = Field(default=None)


class ExtractedDateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = Field(
        default=None,
        description="Normalized start date. Use the first day of the month/year when precision is unavailable.",
    )
    end_date: date | None = Field(
        default=None,
        description="Normalized end date. Null when the range is current/present.",
    )
    current: bool = Field(
        default=False,
        description="True when the source explicitly indicates Present/Till Date/Current/Ongoing.",
    )
    source_text: str | None = Field(
        default=None,
        description="Original date expression from the resume.",
    )
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedContactInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedAchievement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        description="Original or minimally normalized achievement/responsibility text."
    )
    action: str | None = None
    technologies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    impact: str | None = None

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedExperience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    title: str

    date_range: ExtractedDateRange

    location: str | None = None
    description: str | None = None

    achievements: list[ExtractedAchievement] = Field(
        default_factory=list
    )

    project_names: list[str] = Field(
        default_factory=list,
        description="Names of projects explicitly belonging to this employment record.",
    )

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedEducation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: str
    degree: str | None = None
    field_of_study: str | None = None

    date_range: ExtractedDateRange

    location: str | None = None

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedSkill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str | None = None
    proficiency: str | None = None

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedCertification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    issuer: str | None = None
    date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ExtractedProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    achievements: list[ExtractedAchievement] = Field(default_factory=list)

    company: str | None = Field(
        default=None,
        description="Employer/company under which the project is presented, when explicitly established by document structure.",
    )

    source_text: str | None = None
    evidence: list[ExtractedEvidence] = Field(default_factory=list)


class ResumeExtraction(BaseModel):
    """
    Semantic extraction returned by the LLM.

    IDs are intentionally absent. ResumeASTBuilder owns canonical IDs.
    """

    model_config = ConfigDict(extra="forbid")

    contact: ExtractedContactInformation = Field(
        default_factory=ExtractedContactInformation
    )

    summary: str | None = None

    experience: list[ExtractedExperience] = Field(
        default_factory=list
    )

    education: list[ExtractedEducation] = Field(
        default_factory=list
    )

    skills: list[ExtractedSkill] = Field(
        default_factory=list
    )

    certifications: list[ExtractedCertification] = Field(
        default_factory=list
    )

    projects: list[ExtractedProject] = Field(
        default_factory=list
    )
