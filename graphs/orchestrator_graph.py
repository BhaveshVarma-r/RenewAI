"""Main orchestrator LangGraph — the central workflow engine."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.orchestrator import (
    init_node, classify_node, route_to_channel, route_after_safety,
    deliver_node, escalate_node, complete_node,
)
from agents.email_agent import send_renewal_email
from agents.whatsapp_agent import handle_whatsapp
from agents.voice_agent import make_renewal_call
from middleware.safety_gate import SafetyGate
from graphs.planner_loop import PlannerLoopGraph
from mock_services.cloud_sql_audit import MockAuditDB
from schemas.models import AuditLogEntry
from mock_services.vector_search import MockVectorSearch

safety_gate = SafetyGate()
audit_db = MockAuditDB()
planner_loop = None # Declare as global, initialized in build_orchestrator_graph
vector_search = None # Declare as global, initialized in build_orchestrator_graph


async def plan_node(state: dict) -> dict:
    """Run the planner loop (plan ➜ critique ➜ retry)."""
    result = await planner_loop.ainvoke(state)
    # Merge planner results back into state
    for key in ("execution_plan", "critique_result", "escalation_flag", "escalation_reason", "plan_retry_count"):
        if key in result:
            state[key] = result[key]
    state["current_step"] = "planned"
    return state


async def email_node(state: dict) -> dict:
    """Run the email agent."""
    global vector_search # Access the global instance
    return await send_renewal_email(state, vector_search)


async def whatsapp_node(state: dict) -> dict:
    """Run the WhatsApp agent."""
    return await handle_whatsapp(state)


async def voice_node(state: dict) -> dict:
    """Run the voice agent."""
    global vector_search # Access the global instance
    return await make_renewal_call(state, vector_search)


async def safety_node(state: dict) -> dict:
    """Run the safety gate pipeline."""
    from schemas.models import PolicyData, CritiqueResult

    content = ""
    result = state.get("execution_result", {})
    if result.get("html_content"):
        content = result["html_content"]
    elif result.get("script_preview"):
        content = result["script_preview"]
    elif result.get("channel") == "whatsapp":
        content = f"WhatsApp interaction: intent={result.get('intent_detected')}"
    else:
        content = str(result)

    policy_data = state.get("policy_data")
    if isinstance(policy_data, dict):
        policy_data = PolicyData(**policy_data)

    critique = state.get("critique_result")
    if isinstance(critique, dict):
        try:
            critique = CritiqueResult(**critique)
        except Exception:
            critique = None

    safety_result = await safety_gate.process(
        content=content,
        language=policy_data.language_preference if policy_data else "english",
        policy_data=policy_data,
        critique_result=critique,
        channel=result.get("channel", "email"),
    )

    state["compliance_result"] = safety_result.compliance.model_dump() if safety_result.compliance else {}
    if not safety_result.passed:
        state["escalation_flag"] = True
        state["escalation_reason"] = f"Safety gate: {safety_result.violations}"

    state["current_step"] = "safety_checked"

    # Audit the safety gate result
    audit_db.write_audit_log(AuditLogEntry(
        trace_id=state.get("trace_id", ""),
        step_sequence=5,
        agent_id="safety_gate",
        policy_id=state.get("policy_id", ""),
        customer_id=state.get("customer_id", ""),
        agent_input={"content_preview": content[:200]},
        agent_response={
            "passed": safety_result.passed,
            "violations": safety_result.violations,
        },
        compliance_verdict=safety_result.compliance.verdict if safety_result.compliance else None,
    ))

    return state


def build_orchestrator_graph(vector_search_param: MockVectorSearch):
    """Build the main orchestration graph."""
    global planner_loop, vector_search # Declare as global
    vector_search = vector_search_param # Store as global
    planner_loop = PlannerLoopGraph(vector_search_param) # Pass vector_search here
    workflow = StateGraph(dict)

    # Add all nodes
    workflow.add_node("init", init_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("email", email_node)
    workflow.add_node("whatsapp", whatsapp_node)
    workflow.add_node("voice", voice_node)
    workflow.add_node("safety_check", safety_node)
    workflow.add_node("deliver", deliver_node)
    workflow.add_node("escalate", escalate_node)
    workflow.add_node("complete", complete_node)

    workflow.set_entry_point("init")

    workflow.add_edge("init", "classify")
    workflow.add_edge("classify", "plan")

    workflow.add_conditional_edges("plan", route_to_channel, {
        "email": "email",
        "whatsapp": "whatsapp",
        "voice": "voice",
        "escalate": "escalate",
    })

    workflow.add_edge("email", "safety_check")
    workflow.add_edge("whatsapp", "safety_check")
    workflow.add_edge("voice", "safety_check")

    workflow.add_conditional_edges("safety_check", route_after_safety, {
        "deliver": "deliver",
        "escalate": "escalate",
    })

    workflow.add_edge("deliver", "complete")
    workflow.add_edge("escalate", "complete")
    workflow.add_edge("complete", END)

    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    return graph
