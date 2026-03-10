"""Planner critique retry loop as a LangGraph StateGraph."""

from typing import Any
from langgraph.graph import StateGraph, END
from agents.planner import plan_renewal
from agents.planner_critique import critique_plan
from schemas.models import PlannerLoopState, CritiqueResult
from mock_services.bigquery import MockBigQueryClient
from mock_services.vector_search import MockVectorSearch

bigquery = MockBigQueryClient()


class PlannerLoopGraph:
    """Planner → Critique → Retry loop with max 3 retries."""

    def __init__(self, vector_search: MockVectorSearch):
        self.vector_search = vector_search
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(dict)

        workflow.add_node("plan", self._plan_node)
        workflow.add_node("critique", self._critique_node)
        workflow.add_node("approved", self._approved_node)
        workflow.add_node("escalate", self._escalate_node)

        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "critique")

        workflow.add_conditional_edges("critique", self._route_after_critique, {
            "approved": "approved",
            "retry": "plan",
            "escalate": "escalate",
        })

        workflow.add_edge("approved", END)
        workflow.add_edge("escalate", END)

        return workflow.compile()

    async def _plan_node(self, state: dict) -> dict:
        """Run the planner agent."""
        # Initialize retry count if not present
        if "plan_retry_count" not in state:
            state["plan_retry_count"] = 0
        else:
            state["plan_retry_count"] = int(state.get("plan_retry_count", 0)) + 1
        
        # Initialize feedback history
        if "feedback_history" not in state:
            state["feedback_history"] = []
        
        result = await plan_renewal(state, self.vector_search)
        return result

    async def _critique_node(self, state: dict) -> dict:
        """Run the critique agent."""
        plan = state.get("execution_plan", {})
        policy_data = state.get("policy_data", {})
        propensity = state.get("propensity_score")

        critique = await critique_plan(plan, policy_data, propensity)
        state["critique"] = critique.model_dump()
        state["critique_result"] = critique.model_dump()
        
        # Store rejection reasons as feedback for next retry
        rejection_reasons = critique.rejection_reasons if hasattr(critique, 'rejection_reasons') else state.get("critique", {}).get("rejection_reasons", [])
        if rejection_reasons and isinstance(rejection_reasons, list):
            state["feedback_history"] = rejection_reasons

        # Log to BigQuery analytics
        retry_count = state.get("plan_retry_count", 0)
        if isinstance(retry_count, int):
            await bigquery.async_insert("critique_logs", [{
                "trace_id": state.get("trace_id", ""),
                "agent_id": "planner_critique",
                "verdict": critique.verdict,
                "score": float(critique.score) if critique.score else 0.0,
                "tone_score": float(critique.tone_score) if critique.tone_score else 0.0,
                "language_quality_score": float(critique.language_quality_score) if critique.language_quality_score else 0.0,
                "hallucination_detected": 1 if critique.hallucination_detected else 0,
                "retry_count": retry_count,
            }])

        return state

    def _route_after_critique(self, state: dict) -> str:
        """Determine next step based on critique result."""
        critique = state.get("critique", {})
        retry_count = int(state.get("plan_retry_count", 0)) if state.get("plan_retry_count") else 0

        if critique.get("verdict") == "APPROVED":
            return "approved"
        elif retry_count >= 3:
            return "escalate"
        else:
            return "retry"

    async def _approved_node(self, state: dict) -> dict:
        """Plan approved — pass through."""
        state["current_step"] = "plan_approved"
        return state

    async def _escalate_node(self, state: dict) -> dict:
        """Max retries reached — escalate."""
        state["escalation_flag"] = True
        rejection_reasons = state.get("critique", {}).get("rejection_reasons", [])
        if isinstance(rejection_reasons, (list, tuple)):
            reasons_str = ", ".join(str(r) for r in rejection_reasons)
        else:
            reasons_str = str(rejection_reasons) if rejection_reasons else "Unknown"
        state["escalation_reason"] = f"Planner critique failed after 3 retries: {reasons_str}"
        state["current_step"] = "plan_escalated"
        return state

    async def run(self, state: dict) -> dict:
        """Execute the planner loop."""
        result = await self.graph.ainvoke(state)
        return result

    async def ainvoke(self, state: dict, config: dict = None) -> dict:
        """Async invoke the planner loop (alias for run)."""
        return await self.run(state)
