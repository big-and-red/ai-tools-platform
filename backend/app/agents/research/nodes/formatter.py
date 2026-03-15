import json

import structlog
from langchain_core.runnables import RunnableConfig

from app.agents.research.state import ResearchState

logger = structlog.get_logger()


def _linkify_citations(text: str, sources: list[str]) -> str:
    """Replace [N] with [[N]](url) for each cited source."""
    import re
    def replace(m: re.Match) -> str:
        idx = int(m.group(1))
        if 1 <= idx <= len(sources):
            return f"[[{idx}]]({sources[idx - 1]})"
        return m.group(0)
    return re.sub(r"\[(\d+)\]", replace, text)


def _to_markdown(report: dict) -> str:
    sources = report.get("sources", [])
    lines = [f"# {report['title']}", ""]
    for section in report.get("sections", []):
        lines.append(f"## {section['title']}")
        lines.append(_linkify_citations(section["content"], sources))
        lines.append("")
    if sources:
        lines.append("## Sources")
        for i, url in enumerate(sources, 1):
            lines.append(f"{i}. [{url}]({url})")
    return "\n".join(lines)


async def formatter_node(
    state: ResearchState, config: RunnableConfig
) -> dict:
    redis = config["configurable"]["redis"]
    job_id = state["job_id"]
    report = state["report"]
    trace = config["configurable"].get("langfuse_trace")

    span = trace.start_observation(as_type="span", name="node.formatter", input={"report_title": report.get("title", "")}) if trace else None

    formatted = _to_markdown(report)

    if span:
        span.update(output={"chars": len(formatted)})
        span.end()

    await redis.publish(
        f"job:{job_id}",
        json.dumps({
            "type": "report",
            "node": "formatter",
            "data": {"title": report["title"], "content": formatted},
        }),
    )

    logger.info("formatter.completed", job_id=job_id)
    return {"formatted_output": formatted}
