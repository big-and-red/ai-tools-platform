import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.research.prompts.synthesizer import SYNTHESIZER_SYSTEM_PROMPT
from app.agents.research.schemas import SynthesizerOutput
from app.agents.research.state import ResearchState

logger = structlog.get_logger()


async def synthesizer_node(
    state: ResearchState, config: RunnableConfig
) -> dict:
    llm = config["configurable"]["llm"]
    redis = config["configurable"]["redis"]
    job_id = state["job_id"]
    trace = config["configurable"].get("langfuse_trace")

    await redis.publish(
        f"job:{job_id}",
        json.dumps({"type": "status", "node": "synthesizer", "message": "Writing report..."}),
    )

    span = trace.start_observation(
        as_type="generation",
        name="node.synthesizer",
        model=llm.model_name,
        input={"query": state["query"]},
    ) if trace else None

    # Build a deduplicated numbered source list so LLM can cite by exact index
    all_sources: list[str] = []
    seen: set[str] = set()
    for sr in state["search_results"]:
        for url in sr["sources"]:
            if url and url not in seen:
                seen.add(url)
                all_sources.append(url)

    numbered_sources = "\n".join(f"[{i}] {url}" for i, url in enumerate(all_sources, 1))

    context = (
        f"Query: {state['query']}\n\n"
        f"Available sources (use ONLY these numbers for citations):\n{numbered_sources}\n\n"
        f"Search results:\n{json.dumps(state['search_results'], ensure_ascii=False)}"
    )

    structured_llm = llm.with_structured_output(SynthesizerOutput, include_raw=True)
    raw_result = await structured_llm.ainvoke([
        SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])
    result: SynthesizerOutput = raw_result["parsed"]

    # Re-map cited sources from the canonical numbered list (prevents hallucinated URLs)
    import re
    cited_indices: set[int] = set()
    for section in result.sections:
        for m in re.finditer(r"\[(\d+)\]", section.content):
            idx = int(m.group(1))
            if 1 <= idx <= len(all_sources):
                cited_indices.add(idx)

    # Keep only actually cited sources, preserving order
    final_sources = [all_sources[i - 1] for i in sorted(cited_indices)]

    report = {
        "title": result.title,
        "sections": [{"title": s.title, "content": s.content} for s in result.sections],
        "sources": final_sources,
    }

    if span:
        usage = (raw_result["raw"].usage_metadata or {}) if raw_result.get("raw") else {}
        span.update(
            output={"title": result.title, "sections_count": len(result.sections)},
            usage_details={
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
            },
        )
        span.end()

    logger.info("synthesizer.completed", job_id=job_id, sections=len(report["sections"]))
    return {"report": report}
