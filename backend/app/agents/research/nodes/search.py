import asyncio
import json

import structlog
from langchain_core.runnables import RunnableConfig
from tavily import AsyncTavilyClient

from app.agents.research.state import ResearchState, SearchResult

logger = structlog.get_logger()


async def _search_one(
    client: AsyncTavilyClient, question: str
) -> SearchResult:
    response = await client.search(
        question,
        max_results=5,
        search_depth="advanced",  # deeper crawl, higher quality snippets
        days=90,                  # only results from last 3 months
    )
    snippets = [r.get("content", "") for r in response.get("results", [])]
    sources = [r.get("url", "") for r in response.get("results", [])]
    return SearchResult(question=question, snippets=snippets, sources=sources)


async def search_node(
    state: ResearchState, config: RunnableConfig
) -> dict:
    tavily_api_key = config["configurable"]["tavily_api_key"]
    redis = config["configurable"]["redis"]
    job_id = state["job_id"]
    questions = state["questions"]
    trace = config["configurable"].get("langfuse_trace")

    await redis.publish(
        f"job:{job_id}",
        json.dumps({
            "type": "status",
            "node": "search",
            "message": f"Searching {len(questions)} topics in parallel...",
        }),
    )

    span = trace.start_observation(as_type="span", name="node.search", input={"questions": questions}) if trace else None

    client = AsyncTavilyClient(api_key=tavily_api_key)
    results = await asyncio.gather(*[_search_one(client, q) for q in questions])

    if span:
        span.update(
            output={"results_count": len(results)},
            metadata={"tavily_calls": len(questions)},
        )
        span.end()

    logger.info("search.completed", job_id=job_id, results_count=len(results))
    return {"search_results": list(results)}
