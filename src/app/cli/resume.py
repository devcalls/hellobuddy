from __future__ import annotations

import json
from pathlib import Path

from app.config.resume_settings import ResumeSettings
from app.integration.ai.llm import LLMServiceFactory
from app.models.resume.optimization import (
    OptimizationMode,
    ResumeOptimizationRequest,
    ResumeSection,
)
from app.services.resume.llm_resume_extractor import (
    LLMResumeExtractor,
)
from app.services.resume.resume_optimizer_service import (
    ResumeOptimizerService,
)
from app.services.resume.resume_parser_service import (
    ResumeParserService,
)
from app.services.resume.section_optimizer import (
    SectionOptimizer,
)

resume_settings = ResumeSettings()


# ----------------------------------------------------------------------
# LLM
# ----------------------------------------------------------------------


def _build_llm_service():
    """
    Build the provider-neutral LLM service.

    The provider is selected through LLMServiceFactory.
    """

    return LLMServiceFactory.create(
        settings=resume_settings.llm,
    )


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------


def _build_parser_service() -> ResumeParserService:
    """
    Build the resume parsing service.

    Dependency chain:

        LLMService
            ↓
        LLMResumeExtractor
            ↓
        ResumeParserService
    """

    llm_service = _build_llm_service()

    extractor = LLMResumeExtractor(
        llm_service=llm_service,
        settings=resume_settings,
    )

    return ResumeParserService(
        settings=resume_settings,
        llm_extractor=extractor,
    )


# ----------------------------------------------------------------------
# Optimizer
# ----------------------------------------------------------------------


def _build_optimizer_service() -> ResumeOptimizerService:
    """
    Build the resume optimization service.

    ResumeOptimizerService owns the orchestration:

        resume file
             ↓
        ResumeParserService
             ↓
         ResumeAST
             ↓
        SectionOptimizer
             ↓
       optimized ResumeAST
    """

    llm_service = _build_llm_service()

    extractor = LLMResumeExtractor(
        llm_service=llm_service,
        settings=resume_settings,
    )

    parser_service = ResumeParserService(
        settings=resume_settings,
        llm_extractor=extractor,
    )

    section_optimizer = SectionOptimizer(
        llm_service=llm_service,
        settings=resume_settings,
    )

    return ResumeOptimizerService(
        parser_service=parser_service,
        section_optimizer=section_optimizer,
    )


# ----------------------------------------------------------------------
# JSON
# ----------------------------------------------------------------------


def _write_json(
    data: dict,
    output: str | None,
) -> None:
    """
    Write JSON to stdout or to a file.
    """

    serialized = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )

    if output is None:
        print(serialized)
        return

    output_path = Path(output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        serialized,
        encoding="utf-8",
    )

    print(f"✓ Output written to {output_path}")


# ----------------------------------------------------------------------
# Parse
# ----------------------------------------------------------------------


def parse_resume(
    file_path: str,
    output: str | None = None,
) -> int:
    """
    Parse a resume into ResumeAST.

    CLI:

        hellobuddy resume parse resume.pdf

    Or:

        hellobuddy resume parse resume.pdf \
            --output resume_ast.json
    """

    try:
        resume_path = Path(file_path)

        if not resume_path.exists():
            print(f"✗ Resume file not found: {resume_path}")
            return 1

        parser_service = _build_parser_service()

        print(f"Analyzing resume: {resume_path}")

        analysis = parser_service.parse(resume_path)

        # ----------------------------------------------------------
        # ResumeParserService returns ResumeAnalysis.
        #
        # The canonical persisted artifact is ResumeAST,
        # not ResumeAnalysis.
        # ----------------------------------------------------------

        _write_json(
            data=analysis.resume.model_dump(mode="json"),
            output=output,
        )

        print("✓ Resume analysis completed")

        return 0

    except Exception as exc:
        print(f"✗ Resume analysis failed: {exc}")
        return 1


# ----------------------------------------------------------------------
# Optimize
# ----------------------------------------------------------------------


def optimize_resume(
    file_path: str,
    output: str | None = None,
    mode: str = "general_ats",
    sections: list[str] | None = None,
    input_type: str = "resume",
) -> int:
    """
    Analyze and optimize a resume.

    Two input modes are supported.

    1. Resume file:

        hellobuddy resume optimize resume.pdf

        Flow:

            resume file
                ↓
            parse
                ↓
            ResumeAST
                ↓
            optimize
                ↓
            optimization result

    2. Existing AST:

        hellobuddy resume optimize resume_ast.json \
            --input-type ast

        Flow:

            AST JSON
                ↓
            ResumeAST
                ↓
            optimize
                ↓
            optimization result

    The second mode avoids running document extraction again.
    """

    try:
        input_path = Path(file_path)

        if not input_path.exists():
            print(f"✗ Input file not found: {input_path}")
            return 1

        # ----------------------------------------------------------
        # Validate input type.
        # ----------------------------------------------------------

        if input_type not in {"resume", "ast"}:
            raise ValueError(f"Unsupported input type: {input_type}")

        # ----------------------------------------------------------
        # Convert CLI strings to domain enums.
        # ----------------------------------------------------------

        optimization_mode = OptimizationMode(mode)

        selected_sections = None

        if sections:
            selected_sections = [ResumeSection(section) for section in sections]

        # ----------------------------------------------------------
        # Build optimization request.
        # ----------------------------------------------------------

        request_kwargs = {
            "mode": optimization_mode,
        }

        if selected_sections:
            request_kwargs["sections"] = selected_sections

        request = ResumeOptimizationRequest(**request_kwargs)

        # ----------------------------------------------------------
        # Build service.
        # ----------------------------------------------------------

        optimizer_service = _build_optimizer_service()

        print(f"Optimizing resume: {input_path}")

        print(f"Optimization mode: " f"{optimization_mode.value}")

        print(f"Input type: {input_type}")

        # ----------------------------------------------------------
        # Optimize.
        #
        # IMPORTANT:
        #
        # For a resume:
        #
        #     optimize_file()
        #
        # internally performs:
        #
        #     file → parse → AST → optimize
        #
        # For an existing AST:
        #
        #     optimize_ast_file()
        #
        # performs:
        #
        #     JSON → ResumeAST → optimize
        # ----------------------------------------------------------

        if input_type == "ast":
            result = optimizer_service.optimize_ast_file(
                ast_path=input_path,
                request=request,
            )
        else:
            result = optimizer_service.optimize_file(
                resume_path=input_path,
                request=request,
            )

        # ----------------------------------------------------------
        # Write complete optimization result.
        # ----------------------------------------------------------

        _write_json(
            data=result.model_dump(mode="json"),
            output=output,
        )

        # ----------------------------------------------------------
        # Report validation state.
        # ----------------------------------------------------------

        if result.validation_passed:
            print("✓ Resume optimization completed")
            return 0

        print("⚠ Resume optimization completed " "with validation errors")

        for error in result.validation_errors:
            print(f"  - {error}")

        return 2

    except ValueError as exc:
        print(f"✗ Invalid resume optimization option: {exc}")
        return 1

    except Exception as exc:
        print(f"✗ Resume optimization failed: {exc}")
        return 1
