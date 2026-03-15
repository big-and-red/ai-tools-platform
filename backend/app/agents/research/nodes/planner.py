import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.research.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.agents.research.schemas import PlannerOutput
from app.agents.research.state import ResearchState

logger = structlog.get_logger()


async def planner_node(
    state: ResearchState, config: RunnableConfig
) -> dict:
    llm = config["configurable"]["llm"]
    redis = config["configurable"]["redis"]
    job_id = state["job_id"]
    trace = config["configurable"].get("langfuse_trace")

    await redis.publish(
        f"job:{job_id}",
        json.dumps({"type": "status", "node": "planner", "message": "Breaking down your query..."}),
    )

    span = trace.start_observation(
        as_type="generation",
        name="node.planner",
        model=llm.model_name,
        input={"query": state["query"]},
    ) if trace else None

    structured_llm = llm.with_structured_output(PlannerOutput, include_raw=True)
    raw_result = await structured_llm.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=state["query"]),
    ])

    result: PlannerOutput = raw_result["parsed"]
    questions = result.questions or [state["query"]]

    if span:
        usage = (raw_result["raw"].usage_metadata or {}) if raw_result.get("raw") else {}
        span.update(
            output={"questions": questions},
            usage_details={
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
            },
        )
        span.end()

    await redis.publish(
        f"job:{job_id}",
        json.dumps({"type": "questions", "node": "planner", "data": {"questions": questions}}),
    )

    logger.info("planner.completed", job_id=job_id, questions_count=len(questions))
    return {"questions": questions}
