"""
Seed the database with the initial tool catalog and dev user.
Run: STAND_NAME=local python scripts/seed.py
"""
import asyncio
import sys
import os
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.tool import Tool
from app.models.user import User

# Must match DEV_USER_ID in app/core/deps.py
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

TOOLS = [
    {
        "name": "Research Agent",
        "description": (
            "Multi-step agent with web search and synthesis. "
            "Decomposes your query into sub-questions, searches multiple sources in parallel, "
            "evaluates relevance, and produces a structured report with citations."
        ),
        "tool_type": "research_agent",
        "credit_cost_base": 200,
    },
    {
        "name": "Code Reviewer",
        "description": (
            "Paste any code snippet and get structured feedback with severity levels. "
            "Covers correctness, performance, security, and style — grouped by category."
        ),
        "tool_type": "code_review",
        "credit_cost_base": 50,
    },
    {
        "name": "Document Q&A",
        "description": (
            "Upload a PDF and ask questions about its content. "
            "Powered by a RAG pipeline — answers are grounded in the document with page references."
        ),
        "tool_type": "doc_qa",
        "credit_cost_base": 100,
    },
    {
        "name": "Resume Analyzer",
        "description": (
            "Upload your resume and get an actionable score with specific improvement suggestions. "
            "Evaluates impact, clarity, ATS compatibility, and role alignment."
        ),
        "tool_type": "resume",
        "credit_cost_base": 30,
    },
]


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        # Dev user (stub for Step 05 auth — must match DEV_USER_ID in core/deps.py)
        existing_user = await session.execute(
            select(User).where(User.id == DEV_USER_ID)
        )
        if existing_user.scalar_one_or_none() is None:
            session.add(User(
                id=DEV_USER_ID,
                email="dev@aimarket.local",
                password_hash="dev-stub-no-auth",
            ))
            print("  + dev user (dev@aimarket.local)")
        else:
            print("  ~ dev user (already exists, skipped)")

        # Tools
        for tool_data in TOOLS:
            existing = await session.execute(
                select(Tool).where(Tool.tool_type == tool_data["tool_type"])
            )
            if existing.scalar_one_or_none() is None:
                session.add(Tool(**tool_data))
                print(f"  + {tool_data['name']}")
            else:
                print(f"  ~ {tool_data['name']} (already exists, skipped)")

        await session.commit()

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
