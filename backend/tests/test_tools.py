from uuid import uuid4

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool


@pytest_asyncio.fixture
async def seeded_tools(db_session: AsyncSession) -> list[Tool]:
    tools = [
        Tool(
            name="Research Agent",
            description="Multi-step research with web search.",
            tool_type="research_agent",
            credit_cost_base=200,
        ),
        Tool(
            name="Code Reviewer",
            description="Structured code feedback with severity levels.",
            tool_type="code_review",
            credit_cost_base=50,
        ),
        Tool(
            name="Document Q&A",
            description="RAG pipeline over uploaded PDFs.",
            tool_type="doc_qa",
            credit_cost_base=100,
        ),
        Tool(
            name="Resume Analyzer",
            description="Score and actionable feedback for resumes.",
            tool_type="resume",
            credit_cost_base=30,
        ),
    ]
    db_session.add_all(tools)
    await db_session.flush()
    return tools


async def test_list_tools(client: AsyncClient, seeded_tools: list[Tool]) -> None:
    resp = await client.get("/api/v1/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    names = {t["name"] for t in data}
    assert "Research Agent" in names


async def test_list_tools_schema(client: AsyncClient, seeded_tools: list[Tool]) -> None:
    resp = await client.get("/api/v1/tools")
    tool = resp.json()[0]
    assert set(tool.keys()) >= {"id", "name", "description", "tool_type", "credit_cost_base", "is_active"}


async def test_get_tool(client: AsyncClient, seeded_tools: list[Tool]) -> None:
    tool_id = str(seeded_tools[0].id)
    resp = await client.get(f"/api/v1/tools/{tool_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Research Agent"
    assert resp.json()["tool_type"] == "research_agent"


async def test_get_tool_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/tools/{uuid4()}")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]
