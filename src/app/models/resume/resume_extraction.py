
from typing import Optional

from pydantic import BaseModel, Field


class ExtractedAchievement(BaseModel):
    """
    Achievement extracted directly from the resume.
    """

    text: str = Field(
        description="The achievement bullet exactly or closely as written."
    )


class ExtractedExperience(BaseModel):
    """
    Work experience extracted by the LLM.
    """

    company: Optional[str] = Field(
        default=None,
        description="Company or organization name."
    )

    job_title: Optional[str] = Field(
        default=None,
        description="Job title or role."
    )

    location: Optional[str] = Field(
        default=None,
        description="Job location when present."
    )

    start_date: Optional[str] = Field(
        default=None,
        description="Employment start date as written in the resume."
    )

    end_date: Optional[str] = Field(
        default=None,
        description="Employment end date as written in the resume."
    )

    achievements: list[ExtractedAchievement] = Field(
        default_factory=list,
        description="Achievements or responsibility bullets."
    )


class ExtractedEducation(BaseModel):
    """
    Education extracted by the LLM.
    """

    institution: Optional[str] = Field(
        default=None,
        description="University, college, or institution."
    )

    degree: Optional[str] = Field(
        default=None,
        description="Degree or qualification."
    )

    field_of_study: Optional[str] = Field(
        default=None,
        description="Field or specialization."
    )

    start_date: Optional[str] = Field(
        default=None,
        description="Education start date when available."
    )

    end_date: Optional[str] = Field(
        default=None,
        description="Education end date or graduation date."
    )


class ExtractedSkill(BaseModel):
    """
    Skill extracted by the LLM.
    """

    name: str = Field(
        description="Skill name."
    )

    category: Optional[str] = Field(
        default=None,
        description="Skill category such as programming, cloud, database, etc."
    )


class ExtractedCertification(BaseModel):
    """
    Certification extracted by the LLM.
    """

    name: str = Field(
        description="Certification name."
    )

    issuer: Optional[str] = Field(
        default=None,
        description="Certification issuing organization."
    )

    date: Optional[str] = Field(
        default=None,
        description="Certification date when available."
    )

    credential_id: Optional[str] = Field(
        default=None,
        description="Credential ID when available."
    )

    credential_url: Optional[str] = Field(
        default=None,
        description="Credential verification URL when available."
    )


class ExtractedProject(BaseModel):
    """
    Project extracted by the LLM.
    """

    name: str = Field(
        description="Project name."
    )

    description: Optional[str] = Field(
        default=None,
        description="Project description."
    )

    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies explicitly associated with the project."
    )

    achievements: list[ExtractedAchievement] = Field(
        default_factory=list,
        description="Project achievements or outcomes."
    )


class ResumeExtraction(BaseModel):
    """
    LLM-facing resume extraction schema.

    IMPORTANT:
    This model intentionally contains only information that
    model needs to extract from the resume.

    Do not add:
        - ResumeMetadata
        - confidence
        - needs_review
        - extraction_method
        - application-specific IDs
        - internal processing state
    """

    summary: Optional[str] = Field(
        default=None,
        description="Professional summary/objective if present."
    )

    experiences: list[ExtractedExperience] = Field(
        default_factory=list,
        description="Work experiences found in the resume."
    )

    education: list[ExtractedEducation] = Field(
        default_factory=list,
        description="Education entries found in the resume."
    )

    skills: list[ExtractedSkill] = Field(
        default_factory=list,
        description="Skills explicitly mentioned in the resume."
    )

    certifications: list[ExtractedCertification] = Field(
        default_factory=list,
        description="Certifications found in the resume."
    )

    projects: list[ExtractedProject] = Field(
        default_factory=list,
        description="Projects found in the resume."
    )

