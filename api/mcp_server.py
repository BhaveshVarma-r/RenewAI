"""MCP server for RenewAI agents using FastMCP."""

from fastmcp import FastMCP
from mock_services.crm import MockCRMClient
from mock_services.cloud_sql_audit import MockAuditDB
from mock_services.bigquery import MockBigQueryClient
from services.human_queue import HumanQueueService
import json

# Initialize the MCP server
mcp = FastMCP("RenewAI")

# Services
crm = MockCRMClient()
audit_db = MockAuditDB()
bigquery = MockBigQueryClient()
human_queue = HumanQueueService()

@mcp.tool()
def get_policy_details(policy_id: str) -> str:
    """Fetch full policy details from CRM.
    
    Args:
        policy_id: The ID of the policy (e.g., POL001).
    """
    policy = crm.get_policy(policy_id)
    if not policy:
        return f"Policy {policy_id} not found."
    return json.dumps(policy.model_dump(), indent=2)

@mcp.tool()
def get_audit_trail(policy_id: str) -> str:
    """Get the step-by-step history of interactions for a policy.
    
    Args:
        policy_id: The ID of the policy.
    """
    history = audit_db.get_policy_history(policy_id)
    return json.dumps(history, indent=2)

@mcp.tool()
def check_kpi_metrics() -> str:
    """Retrieve current KPI metrics for the renewal system."""
    # Note: This is a synchronous wrap for the mock BQ client
    import asyncio
    kpis = asyncio.run(bigquery.get_kpi_summary())
    return json.dumps(kpis, indent=2)

@mcp.tool()
def list_pending_escalations() -> str:
    """List all cases currently waiting in the human queue."""
    cases = human_queue.get_pending_cases()
    return json.dumps(cases, indent=2)

if __name__ == "__main__":
    mcp.run()
