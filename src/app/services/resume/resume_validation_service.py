from app.models.resume.resume_ast import (
    ResumeAST,
)


class ResumeValidationService:

    def validate(
        self,
        resume: ResumeAST,
    ) -> ResumeAST:

        self._validate_experience(resume)

        self._validate_source_text(resume)

        return resume

    def _validate_experience(
        self,
        resume: ResumeAST,
    ):

        for experience in resume.experience:

            if not experience.company.strip():

                raise ValueError("Experience contains " "an empty company name.")

            if not experience.title.strip():

                raise ValueError("Experience contains " "an empty title.")

    def _validate_source_text(
        self,
        resume: ResumeAST,
    ):

        for experience in resume.experience:

            if not experience.source_text:

                raise ValueError(
                    f"Experience '{experience.company}' " "has no source_text."
                )

            for achievement in experience.achievements:

                if not achievement.source_text:

                    raise ValueError("Achievement is missing " "source_text.")
