import json
import sys
import traceback

from app.config.resume_settings import (
    ResumeSettings,
)

from app.services.resume.resume_parser_service import (
    ResumeParserService,
)


def parse_resume(
    file_path: str,
    output: str | None = None,
) -> int:

    try:

        settings = ResumeSettings()

        parser = ResumeParserService(
            settings=settings
        )

        print(
            f"Parsing resume: {file_path}"
        )

        analysis = parser.parse(
            file_path
        )
        
        print(
            f"Confidence: "
            f"{analysis.confidence.score:.1f}% "
            f"({analysis.confidence.level.value})"
        )
        resume = analysis.resume

        result = resume.model_dump(
            mode="json"
        )

        formatted = json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )

        if output:

            with open(
                output,
                "w",
                encoding="utf-8",
            ) as file:

                file.write(
                    formatted
                )

            print(
                f"✓ Resume AST written to: "
                f"{output}"
            )

        else:

            print()
            print(formatted)

        print()
        print(
            "Resume extraction complete:"
        )

        print(
            f"  Experience     : "
            f"{len(resume.experience)}"
        )

        print(
            f"  Skills         : "
            f"{len(resume.skills)}"
        )

        print(
            f"  Education      : "
            f"{len(resume.education)}"
        )

        print(
            f"  Certifications : "
            f"{len(resume.certifications)}"
        )

        print(
            f"  Projects       : "
            f"{len(resume.projects)}"
        )

        return 0

    except Exception as error:

        
        print("\n✗ Resume extraction failed.")
        print(f"\n  {type(error).__name__}: {error}")

        traceback.print_exc()

        raise