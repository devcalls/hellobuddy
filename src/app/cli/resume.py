from __future__ import annotations

import json
from pathlib import Path

from app.config.resume_settings import ResumeSettings
from app.integration.ai.llm import (
    LLMService,

)
from app.integration.ai.factory import LLMServiceFactory
from app.models.resume.optimization import (
    OptimizationMode,
    ResumeOptimizationRequest,
    ResumeSection,
)
from app.models.resume.resume_ast import ResumeAST
from app.services.resume.llm_resume_extractor import (
    LLMResumeExtractor,
)
from app.services.resume.optimization_applier import (
    OptimizationApplier,
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


def _build_llm_service() -> LLMService:
    """
    Build the provider-neutral LLM service.

    Provider selection is completely isolated inside
    LLMServiceFactory.

    The CLI does not know whether the configured provider is
    Gemini, OpenAI, Anthropic, or another implementation.
    """

    return LLMServiceFactory.create(
        settings=resume_settings.llm,
    )


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------


def _build_parser_service(
    llm_service: LLMService | None = None,
) -> ResumeParserService:
    """
    Build the resume parsing service.

    Dependency chain:

        LLMService
            ↓
        LLMResumeExtractor
            ↓
        ResumeParserService
    """

    if llm_service is None:
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


def _build_optimizer_service(
    llm_service: LLMService | None = None,
) -> ResumeOptimizerService:
    """
    Build the resume optimization service.

    Dependency chain:

        LLMService
            ↓
        SectionOptimizer
            ↓
        ResumeOptimizerService
            ↓
        OptimizationApplier

    IMPORTANT:

    ResumeOptimizerService operates on an existing ResumeAST.

    It does not parse documents.
    """

    if llm_service is None:
        llm_service = _build_llm_service()

    section_optimizer = SectionOptimizer(
        llm_service=llm_service,
    )

    optimization_applier = OptimizationApplier()

    return ResumeOptimizerService(
        section_optimizer=section_optimizer,
        optimization_applier=optimization_applier,
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
# AST loading
# ----------------------------------------------------------------------


def _load_resume_ast(
    ast_path: Path,
) -> ResumeAST:
    """
    Load an existing ResumeAST from JSON.

    This path intentionally bypasses document parsing and LLM
    extraction.
    """

    try:
        payload = json.loads(
            ast_path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in AST file: {ast_path}"
        ) from exc

    try:
        resume = ResumeAST.model_validate(
            payload
        )
    except Exception as exc:
        raise ValueError(
            f"Invalid ResumeAST in file: {ast_path}: {exc}"
        ) from exc

    # Existing ASTs must satisfy the same semantic invariants
    # as newly parsed ASTs.
    from app.services.resume.resume_validation_service import (
        ResumeValidationService,
    )

    ResumeValidationService().validate(resume)

    return resume


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

        hellobuddy resume parse resume.pdf \\
            --output resume_ast.json
    """

    try:
        resume_path = Path(file_path)

        if not resume_path.exists():
            print(
                f"✗ Resume file not found: {resume_path}"
            )
            return 1

        if not resume_path.is_file():
            print(
                f"✗ Resume path is not a file: {resume_path}"
            )
            return 1

        llm_service = _build_llm_service()

        parser_service = _build_parser_service(
            llm_service=llm_service,
        )

        print(
            f"Analyzing resume: {resume_path}"
        )

        analysis = parser_service.parse(
            resume_path
        )

        # ----------------------------------------------------------
        # ResumeParserService returns ResumeAnalysis.
        #
        # ResumeAST is the canonical persisted artifact.
        # ----------------------------------------------------------

        _write_json(
            data=analysis.resume.model_dump(
                mode="json"
            ),
            output=output,
        )

        print(
            "✓ Resume analysis completed"
        )

        return 0

    except ValueError as exc:
        print(
            f"✗ Resume parsing failed: {exc}"
        )
        return 1

    except Exception as exc:
        print(
            f"✗ Resume parsing failed: {exc}"
        )
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
            ResumeParserService
                ↓
            ResumeAST
                ↓
            ResumeOptimizerService
                ↓
            optimized ResumeAST

    2. Existing AST:

        hellobuddy resume optimize resume_ast.json \\
            --input-type ast

        Flow:

            AST JSON
                ↓
            ResumeAST
                ↓
            ResumeOptimizerService
                ↓
            optimized ResumeAST

    The user therefore does NOT need to manually run
    `resume parse` before optimizing a normal resume file.
    """

    try:
        input_path = Path(file_path)

        if not input_path.exists():
            print(
                f"✗ Input file not found: {input_path}"
            )
            return 1

        if not input_path.is_file():
            print(
                f"✗ Input path is not a file: {input_path}"
            )
            return 1

        # ----------------------------------------------------------
        # Validate input type.
        # ----------------------------------------------------------

        if input_type not in {
            "resume",
            "ast",
        }:
            raise ValueError(
                f"Unsupported input type: {input_type}. "
                f"Expected 'resume' or 'ast'."
            )

        # ----------------------------------------------------------
        # Convert CLI strings to domain enums.
        # ----------------------------------------------------------

        try:
            optimization_mode = OptimizationMode(
                mode
            )
        except ValueError as exc:
            raise ValueError(
                f"Unsupported optimization mode: {mode}"
            ) from exc

        selected_sections: list[
            ResumeSection
        ] | None = None

        if sections:

            try:
                selected_sections = [
                    ResumeSection(section)
                    for section in sections
                ]
            except ValueError as exc:
                raise ValueError(
                    f"Unsupported resume section: {exc}"
                ) from exc

        # ----------------------------------------------------------
        # Build optimization request.
        # ----------------------------------------------------------

        request_kwargs = {
            "mode": optimization_mode,
        }

        if selected_sections is not None:
            request_kwargs["sections"] = (
                selected_sections
            )

        request = ResumeOptimizationRequest(
            **request_kwargs
        )

        print(
            f"Optimizing resume: {input_path}"
        )

        print(
            f"Optimization mode: "
            f"{optimization_mode.value}"
        )

        print(
            f"Input type: {input_type}"
        )

        # ----------------------------------------------------------
        # Build ONE LLM service.
        #
        # The same provider-neutral service can be shared by
        # extraction and optimization.
        # ----------------------------------------------------------

        llm_service = _build_llm_service()

        # ----------------------------------------------------------
        # Build optimizer.
        # ----------------------------------------------------------

        optimizer_service = (
            _build_optimizer_service(
                llm_service=llm_service,
            )
        )

        # ----------------------------------------------------------
        # Obtain ResumeAST.
        # ----------------------------------------------------------

        if input_type == "ast":

            print(
                "Loading existing ResumeAST..."
            )

            resume_ast = _load_resume_ast(
                input_path
            )

        else:

            print(
                "Parsing resume..."
            )

            parser_service = (
                _build_parser_service(
                    llm_service=llm_service,
                )
            )

            analysis = parser_service.parse(
                input_path
            )

            resume_ast = analysis.resume

        # ----------------------------------------------------------
        # Optimize the ResumeAST.
        # ----------------------------------------------------------

        print(
            "Optimizing ResumeAST..."
        )

        result = optimizer_service.optimize_ast(
            resume=resume_ast,
            request=request,
        )

        # ----------------------------------------------------------
        # Write complete optimization result.
        # ----------------------------------------------------------

        _write_json(
            data=result.model_dump(
                mode="json"
            ),
            output=output,
        )

        # ----------------------------------------------------------
        # Report validation state.
        # ----------------------------------------------------------

        if result.validation_passed:

            print(
                "✓ Resume optimization completed"
            )

            return 0

        print(
            "⚠ Resume optimization completed "
            "with validation errors"
        )

        for error in result.validation_errors:
            print(
                f"  - {error}"
            )

        return 2

    except ValueError as exc:

        print(
            f"✗ Invalid resume optimization option: "
            f"{exc}"
        )

        return 1

    except Exception as exc:

        print(
            f"✗ Resume optimization failed: {exc}"
        )

        return 1