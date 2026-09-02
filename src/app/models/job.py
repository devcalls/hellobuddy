from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Dict


class JobPosting(BaseModel):
    job_id: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    expiration_date: str | None = None
    via: str | None = None
    apply_link: HttpUrl | None = None  # Validates that it's a properly formatted URL
    salary: str | None = "Not specified"
    provider_name: str

    @field_validator("description", mode="before")
    @classmethod
    def clean_whitespace(cls, value: str) -> str:
        """Cleans up excessive newlines and spaces common in scraped job descriptions."""
        if isinstance(value, str):
            # Normalize multiple empty lines down to a clean readable format
            lines = [line.strip() for line in value.split("\n")]
            return "\n".join(line for line in lines if line)
        return value


class JobSearch(BaseModel):
    query_params: Dict
    location: str
    country: str | None = None
    result_params: Dict
