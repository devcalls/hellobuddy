"""
Canonical Resume Abstract Syntax Tree (ResumeAST).

This module defines the structured representation of a resume.

Design principles:
    1. The AST represents what is actually present in the resume.
    2. LLM extraction produces this structure.
    3. source_text provides provenance back to the original document.
    4. ExtractionEvidence captures extraction quality.
    5. Numeric confidence is application-derived, not LLM-generated.
    6. The AST must not contain ATS optimization logic.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

# ============================================================
# Extraction / Provenance
# ============================================================


class ExtractionEvidence(BaseModel):
    """
    Evidence supporting an extracted piece of information.

    The LLM identifies the supporting text, its location, and
    the qualitative quality of that evidence.

    Numeric confidence and review status are derived by the
    application after extraction.
    """

    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(
        description=(
            "Exact or near-exact text from the original "
            "resume supporting this extraction."
        )
    )

    source_section: Optional[str] = Field(
        default=None,
        description=(
            "Resume section containing the evidence, "
            "for example Experience, Education, Skills."
        ),
    )

    quality: Literal[
        "high",
        "medium",
        "low",
    ] = Field(
        description=(
            "Qualitative quality of the evidence. "
            "Use high when the extracted fact is explicitly "
            "supported by the resume text, medium when there "
            "is some ambiguity, and low when the evidence is "
            "weak or inferred."
        )
    )

    reason: Optional[str] = Field(
        default=None,
        description=(
            "Explanation of ambiguity or uncertainty "
            "when the evidence is not high quality."
        ),
    )

    # ---------------------------------------------------------
    # Application-derived fields
    # ---------------------------------------------------------

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Application-derived confidence score. "
            "Calculated from evidence quality and other "
            "validation signals. The LLM must not generate "
            "this value."
        ),
    )

    needs_review: bool = Field(
        default=False,
        description=(
            "Application-derived flag indicating that the "
            "evidence or extracted value should be reviewed "
            "by the user."
        ),
    )

    extraction_method: Literal[
        "llm",
        "user",
        "system",
    ] = Field(
        default="llm", description=("How this information was extracted or created.")
    )


# ============================================================
# Dates
# ============================================================


class DateRange(BaseModel):
    """
    Represents a date range such as:

        Jan 2022 - Present
        2019 - 2022
        June 2020 - Dec 2021
    """

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[date] = Field(
        default=None, description="Normalized start date."
    )

    end_date: Optional[date] = Field(default=None, description="Normalized end date.")

    current: bool = Field(
        default=False,
        description=(
            "True when the original resume indicates "
            "that the position/education/project is current."
        ),
    )

    source_text: Optional[str] = Field(
        default=None,
        description=(
            "Original date text from the resume, " "for example 'Jan 2022 - Present'."
        ),
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting the date extraction."
    )


# ============================================================
# Contact Information
# ============================================================


class ContactInformation(BaseModel):
    """
    Candidate contact information.
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None

    email: Optional[str] = None

    phone: Optional[str] = None

    location: Optional[str] = None

    linkedin: Optional[str] = None

    github: Optional[str] = None

    portfolio: Optional[str] = None

    source_text: Optional[str] = Field(
        default=None,
        description=("Original resume text supporting the contact " "information."),
    )

    evidence: list[ExtractionEvidence] = Field(default_factory=list)


# ============================================================
# Achievements
# ============================================================


class Achievement(BaseModel):
    """
    A meaningful accomplishment, responsibility, or
    achievement extracted from an experience or project.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        description=("Original or minimally normalized achievement " "statement.")
    )

    action: Optional[str] = Field(
        default=None,
        description=(
            "Primary action expressed by the achievement, "
            "for example 'Built', 'Led', 'Designed'."
        ),
    )

    technologies: list[str] = Field(
        default_factory=list,
        description=("Technologies explicitly mentioned in " "the achievement."),
    )

    skills: list[str] = Field(
        default_factory=list,
        description=("Skills explicitly represented by the " "achievement."),
    )

    metrics: list[str] = Field(
        default_factory=list,
        description=("Quantifiable metrics explicitly present " "in the achievement."),
    )

    impact: Optional[str] = Field(
        default=None,
        description=(
            "Impact explicitly stated or clearly expressed " "in the source text."
        ),
    )

    source_text: Optional[str] = Field(
        default=None,
        description=("Original resume bullet or text supporting " "this achievement."),
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting this achievement."
    )


# ============================================================
# Professional Experience
# ============================================================


class Experience(BaseModel):
    """
    One professional experience entry.
    """

    model_config = ConfigDict(extra="forbid")

    company: str = Field(description="Company or organization name.")

    title: str = Field(description="Job title or role.")

    date_range: DateRange = Field(description="Employment period.")

    location: Optional[str] = Field(
        default=None, description="Work location when available."
    )

    description: Optional[str] = Field(
        default=None, description=("General role description, if present.")
    )

    achievements: list[Achievement] = Field(
        default_factory=list, description="Achievements and responsibilities."
    )

    source_text: Optional[str] = Field(
        default=None,
        description=("Original resume text representing this " "experience entry."),
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description=("Evidence supporting the experience entry.")
    )


# ============================================================
# Skills
# ============================================================


class Skill(BaseModel):
    """
    Individual skill extracted from the resume.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Skill or technology name.")

    category: Optional[str] = Field(
        default=None,
        description=(
            "Optional skill category such as "
            "Programming Language, Cloud, Database, "
            "Framework, Tool, or Soft Skill."
        ),
    )

    proficiency: Optional[str] = Field(
        default=None,
        description=("Proficiency level only when explicitly " "stated in the resume."),
    )

    source_text: Optional[str] = Field(
        default=None, description=("Original resume text supporting this skill.")
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting this skill."
    )


# ============================================================
# Education
# ============================================================


class Education(BaseModel):
    """
    Academic qualification.
    """

    model_config = ConfigDict(extra="forbid")

    institution: str = Field(description="Educational institution.")

    degree: Optional[str] = Field(default=None, description="Degree or qualification.")

    field_of_study: Optional[str] = Field(
        default=None, description="Major, specialization, or field of study."
    )

    date_range: Optional[DateRange] = Field(
        default=None, description="Education period when available."
    )

    location: Optional[str] = Field(
        default=None, description="Institution location when available."
    )

    source_text: Optional[str] = Field(
        default=None,
        description=("Original resume text supporting this " "education entry."),
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting this education entry."
    )


# ============================================================
# Certifications
# ============================================================


class Certification(BaseModel):
    """
    Professional certification extracted from the resume.
    """

    name: str = Field(description="Certification name.")

    issuer: Optional[str] = Field(
        default=None, description="Organization that issued the certification."
    )

    date: Optional[str] = Field(
        default=None, description="Certification date when available."
    )

    credential_id: Optional[str] = Field(
        default=None, description="Certification credential ID when available."
    )

    credential_url: Optional[str] = Field(
        default=None, description="Certification verification URL when available."
    )

    source_text: Optional[str] = Field(
        default=None, description="Original resume text supporting this certification."
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting the extraction."
    )


# ============================================================
# Projects
# ============================================================


class Project(BaseModel):
    """
    A project listed on the resume.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Project name.")

    description: Optional[str] = Field(default=None, description="Project description.")

    technologies: list[str] = Field(
        default_factory=list,
        description=("Technologies explicitly mentioned in " "the project."),
    )

    achievements: list[Achievement] = Field(
        default_factory=list,
        description=(
            "Achievements or meaningful contributions " "associated with the project."
        ),
    )

    source_text: Optional[str] = Field(
        default=None, description=("Original resume text representing " "this project.")
    )

    evidence: list[ExtractionEvidence] = Field(
        default_factory=list, description="Evidence supporting this project."
    )


# ============================================================
# Resume Metadata
# ============================================================


class ResumeMetadata(BaseModel):
    """
    Metadata owned by HelloBuddy rather than extracted
    from the resume by the LLM.
    """

    model_config = ConfigDict(extra="forbid")

    source_file: Optional[str] = None

    source_format: Optional[str] = None

    parser_version: str = "2.0-llm"

    raw_text: Optional[str] = Field(
        default=None,
        description=(
            "Complete text extracted from the source " "document before LLM processing."
        ),
    )


# ============================================================
# Canonical Resume AST
# ============================================================


class ResumeAST(BaseModel):
    """
    Canonical structured representation of a resume.

    This is the central contract used by:

        Document Reader
              ↓
        LLM Resume Extractor
              ↓
           ResumeAST
              ↓
        Validation
              ↓
        ATS Analysis
              ↓
        Resume Optimization
    """

    model_config = ConfigDict(extra="forbid")

    metadata: ResumeMetadata = Field(default_factory=ResumeMetadata)

    contact: ContactInformation = Field(default_factory=ContactInformation)

    summary: Optional[str] = Field(
        default=None,
        description=(
            "Professional summary or objective exactly " "as represented in the resume."
        ),
    )

    experience: list[Experience] = Field(
        default_factory=list, description="Professional experience entries."
    )

    skills: list[Skill] = Field(
        default_factory=list, description="Skills explicitly present in the resume."
    )

    education: list[Education] = Field(
        default_factory=list, description="Education entries."
    )

    certifications: list[Certification] = Field(
        default_factory=list, description="Professional certifications."
    )

    projects: list[Project] = Field(
        default_factory=list, description="Projects listed on the resume."
    )
    # Original text extracted from the resume.
    #
    # This is intentionally kept at the ResumeAST level
    # because it represents the complete source document.
    source_text: Optional[str] = Field(
        default=None,
        description=(
            "Complete original text extracted from the "
            "resume document. Used for provenance, "
            "debugging, re-processing and ATS analysis."
        ),
    )
