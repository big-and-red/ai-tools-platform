from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    questions: list[str] = Field(
        description="3-5 specific sub-questions that together answer the original query"
    )


class CriticOutput(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the search results are sufficient to write a comprehensive answer"
    )
    refined_queries: list[str] = Field(
        default=[],
        description="New search queries to try if results are insufficient",
    )


class Section(BaseModel):
    title: str
    content: str = Field(description="Section content with inline citations [1], [2]")


class SynthesizerOutput(BaseModel):
    title: str = Field(description="Report title")
    sections: list[Section] = Field(description="3-5 report sections")
    sources: list[str] = Field(default=[], description="List of source URLs cited (optional, may be empty)")
