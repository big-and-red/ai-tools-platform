from typing import Literal

from pydantic import BaseModel, Field


class CodeIssue(BaseModel):
    severity: Literal["critical", "warning", "suggestion"] = Field(
        description="Issue severity: critical = bugs/security, warning = code smells, suggestion = style/best practices"
    )
    line: str | None = Field(
        default=None,
        description="Line number or range, e.g. '42' or '10-15'. null if not applicable",
    )
    title: str = Field(description="One-line issue title")
    explanation: str = Field(description="Detailed explanation and how to fix")
    code_snippet: str | None = Field(
        default=None,
        description="Suggested fix as a code snippet, if applicable",
    )


class CodeReviewResult(BaseModel):
    language: str = Field(description="Detected or specified programming language")
    summary: str = Field(description="One-paragraph overall assessment")
    issues: list[CodeIssue] = Field(
        default_factory=list,
        description="List of issues found, ordered by severity (critical first)",
    )
    score: int = Field(
        description="Code quality score from 1 to 10",
        ge=1,
        le=10,
    )
