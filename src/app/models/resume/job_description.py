from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    text: str

    skills: list[str] = Field(default_factory=list)

    keywords: list[str] = Field(default_factory=list)


class JobDescriptionAST(BaseModel):

    title: str

    company: str | None = None

    seniority: str | None = None

    location: str | None = None

    employment_type: str | None = None

    required_skills: list[str] = Field(default_factory=list)

    preferred_skills: list[str] = Field(default_factory=list)

    responsibilities: list[JobRequirement] = Field(default_factory=list)

    qualifications: list[JobRequirement] = Field(default_factory=list)

    keywords: list[str] = Field(default_factory=list)
