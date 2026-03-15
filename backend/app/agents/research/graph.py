from langgraph.graph import END, StateGraph

from app.agents.research.nodes.critic import critic_node, should_retry
from app.agents.research.nodes.formatter import formatter_node
from app.agents.research.nodes.planner import planner_node
from app.agents.research.nodes.search import search_node
from app.agents.research.nodes.synthesizer import synthesizer_node
from app.agents.research.state import ResearchState


def build_research_graph() -> StateGraph:
    builder = StateGraph(ResearchState)

    builder.add_node("planner", planner_node)
    builder.add_node("search", search_node)
    builder.add_node("critic", critic_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("formatter", formatter_node)

    builder.set_entry_point("planner")
    builder.add_edge("planner", "search")
    builder.add_edge("search", "critic")
    builder.add_conditional_edges("critic", should_retry, {
        "search": "search",
        "synthesizer": "synthesizer",
    })
    builder.add_edge("synthesizer", "formatter")
    builder.add_edge("formatter", END)

    return builder
