"""
Top-level LangGraph assembly.
Flow:
  START → orchestrator → [scheduling | diagnosis | emergency | feedback]
                          diagnosis → [scheduling | emergency | hitl]
  All terminal nodes → END
"""

from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState
from backend.agents.orchestrator.node import orchestrator_node, orchestrator_router
from backend.agents.scheduling.node import scheduling_node
from backend.agents.diagnosis.node import diagnosis_node, diagnosis_router
from backend.agents.emergency.node import emergency_node
from backend.agents.feedback.node import feedback_node
from backend.agents.hitl.node import hitl_node


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("scheduling", scheduling_node)
    workflow.add_node("diagnosis", diagnosis_node)
    workflow.add_node("emergency", emergency_node)
    workflow.add_node("feedback", feedback_node)
    workflow.add_node("hitl", hitl_node)

    workflow.set_entry_point("orchestrator")

    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator_router,
        {
            "scheduling": "scheduling",
            "diagnosis": "diagnosis",
            "emergency": "emergency",
            "feedback": "feedback",
        },
    )

    workflow.add_conditional_edges(
        "diagnosis",
        diagnosis_router,
        {
            "scheduling": "scheduling",
            "emergency": "emergency",
            "hitl": "hitl",
        },
    )

    workflow.add_edge("scheduling", END)
    workflow.add_edge("emergency", END)
    workflow.add_edge("feedback", END)
    workflow.add_edge("hitl", END)

    return workflow.compile()


graph = build_graph()
