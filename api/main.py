"""FastAPI application — all RenewAI endpoints."""

import os
import uuid
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas.models import (
    DueDateTriggerRequest, InboundTriggerRequest, LapseTriggerRequest,
    QueueResolveRequest, TriggerResponse, InboundResponse, LapseResponse,
    HealthResponse,
)
from graphs.orchestrator_graph import build_orchestrator_graph
from services.human_queue import HumanQueueService
from mock_services.crm import MockCRMClient
from mock_services.cloud_sql_audit import MockAuditDB
from mock_services.bigquery import MockBigQueryClient
from mock_services.vector_search import MockVectorSearch

# Initialize services
crm = MockCRMClient()
audit_db = MockAuditDB()
bigquery = MockBigQueryClient()
human_queue = HumanQueueService()
orchestrator_graph = None
vector_search = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize graph on startup."""
    global orchestrator_graph, vector_search
    vector_search = MockVectorSearch()
    await vector_search.async_init()
    orchestrator_graph = build_orchestrator_graph(vector_search)
    print("✅ RenewAI Backend started successfully")
    print(f"   Gemini API Key: {'configured' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
    print(f"   LangSmith: {'enabled' if os.getenv('LANGCHAIN_API_KEY') else 'disabled'}")
    print(f"   Policies loaded: {len(crm.get_all_policies())}")
    yield
    print("🛑 RenewAI Backend shutting down")


app = FastAPI(
    title="RenewAI API",
    description="AI-powered Insurance Renewal System for Suraksha Life Insurance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== TRIGGER ENDPOINTS =====================

@app.post("/trigger/due-date", response_model=TriggerResponse)
async def trigger_due_date(request: DueDateTriggerRequest):
    """Trigger a renewal workflow based on days to due date."""
    policy = crm.get_policy(request.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {request.policy_id} not found")

    trace_id = str(uuid.uuid4())
    initial_state = {
        "trace_id": trace_id,
        "policy_id": request.policy_id,
        "customer_id": policy.customer_id,
        "trigger_type": "due_date",
        "days_to_due": request.days_to_due,
        "current_step": "init",
        "plan_retry_count": 0,
        "escalation_flag": False,
        "interaction_history": [],
    }

    try:
        config = {"configurable": {"thread_id": trace_id}}
        result = await orchestrator_graph.ainvoke(initial_state, config=config)

        # Handle escalation
        if result.get("escalation_flag"):
            await human_queue.add_to_queue(result, result.get("escalation_reason", "Auto-escalated"))

        return TriggerResponse(
            trace_id=trace_id,
            status=result.get("final_status", "completed"),
            result=result.get("execution_result"),
        )
    except Exception as e:
        return TriggerResponse(trace_id=trace_id, status=f"error: {str(e)[:200]}", result=None)


@app.post("/trigger/inbound", response_model=InboundResponse)
async def trigger_inbound(request: InboundTriggerRequest):
    """Handle an inbound customer message."""
    policy = crm.get_policy(request.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {request.policy_id} not found")

    trace_id = str(uuid.uuid4())
    initial_state = {
        "trace_id": trace_id,
        "policy_id": request.policy_id,
        "customer_id": policy.customer_id,
        "trigger_type": "inbound_message",
        "current_step": "init",
        "plan_retry_count": 0,
        "escalation_flag": False,
        "interaction_history": [{"channel": request.channel, "message": request.message}],
    }

    try:
        config = {"configurable": {"thread_id": trace_id}}
        result = await orchestrator_graph.ainvoke(initial_state, config=config)

        if result.get("escalation_flag"):
            await human_queue.add_to_queue(result, result.get("escalation_reason", "Inbound escalation"))

        exec_result = result.get("execution_result", {})
        return InboundResponse(
            trace_id=trace_id,
            response_sent=True,
            intent=exec_result.get("intent_detected", "processed"),
        )
    except Exception as e:
        return InboundResponse(trace_id=trace_id, response_sent=False, intent=f"error: {str(e)[:100]}")


@app.post("/trigger/lapse", response_model=LapseResponse)
async def trigger_lapse(request: LapseTriggerRequest):
    """Trigger a revival campaign for a lapsed policy."""
    policy = crm.get_policy(request.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {request.policy_id} not found")

    trace_id = str(uuid.uuid4())
    initial_state = {
        "trace_id": trace_id,
        "policy_id": request.policy_id,
        "customer_id": policy.customer_id,
        "trigger_type": "lapse_event",
        "days_to_due": -request.days_since_lapse,
        "current_step": "init",
        "plan_retry_count": 0,
        "escalation_flag": False,
        "interaction_history": [],
    }

    try:
        config = {"configurable": {"thread_id": trace_id}}
        result = await orchestrator_graph.ainvoke(initial_state, config=config)

        if result.get("escalation_flag"):
            await human_queue.add_to_queue(result, result.get("escalation_reason", "Lapse revival"))

        return LapseResponse(trace_id=trace_id, revival_attempted=True)
    except Exception as e:
        return LapseResponse(trace_id=trace_id, revival_attempted=False)


# ===================== AUDIT ENDPOINTS =====================

@app.get("/audit/trace/{trace_id}")
async def get_audit_trace(trace_id: str):
    """Get full audit trail for a trace."""
    logs = audit_db.get_trace(trace_id)
    return {"trace_id": trace_id, "steps": logs, "total_steps": len(logs)}


@app.get("/audit/policy/{policy_id}")
async def get_policy_audit(policy_id: str):
    """Get all interactions for a policy."""
    logs = audit_db.get_policy_history(policy_id)
    return {"policy_id": policy_id, "interactions": logs, "total": len(logs)}


# ===================== QUEUE ENDPOINTS =====================

@app.get("/queue/pending")
async def get_pending_queue():
    """Get all pending human queue cases."""
    cases = human_queue.get_pending_cases()
    return {"cases": cases, "total": len(cases)}


@app.post("/queue/resolve/{queue_id}")
async def resolve_queue_case(queue_id: str, request: QueueResolveRequest):
    """Resolve a human queue case."""
    result = await human_queue.resolve_case(queue_id, request.resolution, request.specialist_notes)
    if not result:
        raise HTTPException(status_code=404, detail=f"Queue case {queue_id} not found")
    return {"status": "resolved", "case": result}


# ===================== KPI ENDPOINTS =====================

@app.get("/kpi/summary")
async def get_kpi_summary():
    """Get current KPI metrics."""
    return await bigquery.get_kpi_summary()


@app.post("/trigger/scan/t-minus/{days}")
async def trigger_batch_scan(days: int):
    """Scan for policies due within N days and trigger workflows."""
    due_policies = crm.get_due_policies(days)
    results = []
    
    for policy in due_policies:
        # Avoid double-triggering if already in high-risk scan window
        # (This is a simplified mock logic)
        try:
            res = await trigger_due_date(DueDateTriggerRequest(
                policy_id=policy.policy_id,
                days_to_due=(datetime.strptime(policy.due_date, "%Y-%m-%d") - datetime.now()).days
            ))
            results.append({"policy_id": policy.policy_id, "status": "triggered", "trace_id": res.trace_id})
        except Exception as e:
            results.append({"policy_id": policy.policy_id, "status": f"error: {str(e)}"})
            
    return {
        "status": "batch_scan_complete",
        "total_scanned": len(due_policies),
        "triggered_count": len([r for r in results if r["status"] == "triggered"]),
        "results": results
    }


# ===================== HEALTH =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    gemini_status = "connected" if os.getenv("GEMINI_API_KEY") else "not_configured"
    langsmith_status = "connected" if os.getenv("LANGCHAIN_API_KEY") else "not_configured"
    return HealthResponse(status="healthy", gemini=gemini_status, langsmith=langsmith_status)


# ===================== DEMO =====================

@app.post("/demo/run-all")
async def run_demo():
    """Run demo scenarios for all sample policies."""
    policies = crm.get_all_policies()
    results = []

    for policy in policies[:3]:  # Limit to 3 for fast demo
        try:
            trace_id = str(uuid.uuid4())
            days = 45 if policy.status == "active" else 10
            trigger_type = "lapse_event" if policy.status == "lapsed" else "due_date"

            initial_state = {
                "trace_id": trace_id,
                "policy_id": policy.policy_id,
                "customer_id": policy.customer_id,
                "trigger_type": trigger_type,
                "days_to_due": days,
                "current_step": "init",
                "plan_retry_count": 0,
                "escalation_flag": False,
                "interaction_history": [],
            }

            config = {"configurable": {"thread_id": trace_id}}
            result = await orchestrator_graph.ainvoke(initial_state, config=config)

            if result.get("escalation_flag"):
                await human_queue.add_to_queue(result, result.get("escalation_reason", "Demo"))

            results.append({
                "policy_id": policy.policy_id,
                "customer_name": policy.customer_name,
                "risk_tier": policy.risk_tier,
                "channel": result.get("execution_result", {}).get("channel", "unknown"),
                "status": result.get("final_status", "unknown"),
                "converted": result.get("execution_result", {}).get("converted", False),
                "escalated": result.get("escalation_flag", False),
                "trace_id": trace_id,
            })
        except Exception as e:
            results.append({
                "policy_id": policy.policy_id,
                "customer_name": policy.customer_name,
                "status": f"error: {str(e)[:100]}",
                "trace_id": trace_id,
            })

    converted = sum(1 for r in results if r.get("converted"))
    escalated = sum(1 for r in results if r.get("escalated"))

    return {
        "total_policies": len(results),
        "converted": converted,
        "escalated": escalated,
        "conversion_rate": f"{(converted/max(len(results),1))*100:.1f}%",
        "results": results,
    }


# ===================== POLICY LOOKUP =====================

@app.get("/policies")
async def list_policies():
    """List all sample policies."""
    policies = crm.get_all_policies()
    return {"policies": [p.model_dump() for p in policies], "total": len(policies)}


@app.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a specific policy."""
    policy = crm.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return policy.model_dump()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", "8000")))
