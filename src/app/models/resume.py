from pydantic import BaseModel, Field
from typing import List


class ResumeMetadata(BaseModel):
    model_config = {"extra": "forbid"}
    """Universal, PII-free applicant profile focused on structural capacities."""
    total_years_experience: float = Field(
        description="Total cumulative years of professional work experience as a floating-point number."
    )
    current_seniority_level: str = Field(
        description="Categorized seniority level. Must be one of: Junior, Mid, Senior, Lead, Principal, Executive."
    )
    core_expertise_domains: List[str] = Field(
        description="High-level fields of focus, verticals, or industries they have operated within (e.g., Corporate Finance, Machine Learning, Supply Chain)."
    )
    technical_tools_and_systems: List[str] = Field(
        description="Domain-specific tools, software platforms, hardware, suites, or languages utilized (e.g., Bloomberg Terminal, QuickBooks, Excel VBA, FastAPI, Salesforce)."
    )
    methodologies_and_frameworks: List[str] = Field(
        description="Strategic frameworks, operating methodologies, compliances, regulations, or structural patterns used (e.g., DCF Valuation, GAAP, Agile/Scrum, Six Sigma, Lean)."
    )
    primary_job_titles: List[str] = Field(
        description="Cleaned, normalized historical functional titles held by the professional."
    )
    summary_profile: str = Field(
        description="A concise, 2-3 sentence anonymized summary of their core professional identity, omitting names and specific employers."
    )
