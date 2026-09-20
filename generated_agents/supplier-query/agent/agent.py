from __future__ import annotations

from harness_core import AgentHarness, get_logger, load_config
from langgraph.graph import END, StateGraph

from .nodes import analyze
from .schemas import SupplierQueryInput, SupplierQueryOutput

logger = get_logger(__name__)


def _build_graph():
    g = StateGraph(dict)
    g.add_node("analyze", analyze)
    g.set_entry_point("analyze")
    g.add_edge("analyze", END)
    return g.compile()


_graph = _build_graph()
_config = load_config("config/harness.yaml")

harness = AgentHarness(
    graph=_graph,
    agent_name="supplier-query",
    agent_version="0.1.0",
    input_schema=SupplierQueryInput,
    output_schema=SupplierQueryOutput,
    config=_config,
)
