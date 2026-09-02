from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.resume.resume_ast import ResumeAST
from app.models.resume.optimization import (
    ResumeOptimizationResult,
)


class ResumeASTOptimizer:

    def apply(
        self,
        resume_ast: ResumeAST,
        optimization: ResumeOptimizationResult,
    ) -> ResumeAST:

        data = deepcopy(resume_ast.model_dump(mode="python"))

        for section in optimization.sections:

            if not section.validation_passed:
                continue

            section_name = section.section.value

            data[section_name] = deepcopy(section.optimized_content)

        return ResumeAST.model_validate(data)
