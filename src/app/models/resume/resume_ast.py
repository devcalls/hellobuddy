"""
Canonical Resume Abstract Syntax Tree (ResumeAST).

The AST is application-owned. The LLM never owns canonical IDs or metadata.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str
    source_section: str | None = None
    quality: Literal["high", "medium", "low"] = "high"
    reason: str | None = None

    # Application-derived fields.
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_review: bool = False
    extraction_method: Literal["llm", "user", "system"] = "llm"


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None
    current: bool = False
    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class ContactInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Achievement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    action: str | None = None
    technologies: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    impact: str | None = None

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    company: str
    title: str
    date_range: DateRange

    location: str | None = None
    description: str | None = None

    achievements: list[Achievement] = Field(default_factory=list)

    # References canonical top-level Project IDs.
    project_ids: list[str] = Field(default_factory=list)

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    category: str | None = None
    proficiency: str | None = None

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    institution: str
    degree: str | None = None
    field_of_study: str | None = None

    date_range: DateRange

    location: str | None = None

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Certification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    issuer: str | None = None
    date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class Project(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str | None = None

    technologies: list[str] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)

    source_text: str | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)


class ResumeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_file: str | None = None
    source_format: str | None = None
    parser_version: str = "3.0-llm"
    raw_text: str | None = None


class ResumeAST(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: ResumeMetadata = Field(default_factory=ResumeMetadata)
    contact: ContactInformation = Field(default_factory=ContactInformation)
    summary: str | None = None

    experience: list[Experience] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)

    source_text: str | None = None
