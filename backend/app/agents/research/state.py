from typing import TypedDict


class SearchResult(TypedDict):
    question: str
    snippets: list[str]
    sources: list[str]


class Section(TypedDict):
    title: str
    content: str


class Report(TypedDict):
    title: str
    sections: list[Section]
    sources: list[str]


class ResearchState(TypedDict):
    query: str
    job_id: str
    questions: list[str]
    search_results: list[SearchResult]
    retry_count: int
    report: Report | None
    formatted_output: str
