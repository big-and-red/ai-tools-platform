import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.research.prompts.critic import CRITIC_SYSTEM_PROMPT
from app.agents.research.schemas import CriticOutput
from app.agents.research.state import ResearchState

logger = structlog.get_logger()

MAX_RETRIES = 2


async def critic_node(
    state: ResearchState, config: RunnableConfig
) -> dict:
    llm = config["configurable"]["llm"]
    redis = config["configurable"]["redis"]
    job_id = state["job_id"]
    trace = config["configurable"].get("langfuse_trace")

    await redis.publish(
        f"job:{job_id}",
        json.dumps({"type": "status", "node": "critic", "message": "Evaluating search results..."}),
    )

    span = trace.start_observation(
        as_type="generation",
        name="node.critic",
        model=llm.model_name,
        input={"query": state["query"]},
    ) if trace else None

    context = json.dumps({
        "query": state["query"],
        "search_results": state["search_results"],
    })

    structured_llm = llm.with_structured_output(CriticOutput, include_raw=True)
    raw_result = await structured_llm.ainvoke([
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    result: CriticOutput = raw_result["parsed"]

    if span:
        usage = (raw_result["raw"].usage_metadata or {}) if raw_result.get("raw") else {}
        span.update(
            output={"is_sufficient": result.is_sufficient, "refined_queries": result.refined_queries},
            usage_details={
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
            },
        )
        span.end()

    if not result.is_sufficient and result.refined_queries:
        logger.info("critic.retry", job_id=job_id, retry_count=state.get("retry_count", 0))
        return {
            "is_sufficient": False,
            "questions": result.refined_queries,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {"is_sufficient": True, "retry_count": state.get("retry_count", 0)}


def should_retry(state: ResearchState) -> str:
    if not state.get("is_sufficient", True) and state.get("retry_count", 0) <= MAX_RETRIES:
        return "search"
    return "synthesizer"
