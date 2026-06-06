import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")
FIVETRAN_API_BASE = "https://api.fivetran.com/v1"


def _demo_fallback(source, dataset, mcp_result):
    return {
        "integration_mode": "MCP",
        "mcp_call_status": mcp_result.get("mcp_call_status", "Unknown"),
        "mcp_result": mcp_result.get("mcp_result", "No MCP result available"),
        "connections_found": mcp_result.get("connections_found", 0),
        "fallback_used": True,
        "fallback_status": "Healthy with warning demo status",
        "connector": f"{source} {dataset} connector",
        "status": "Healthy with warning",
        "last_sync": "18 minutes ago",
        "schema_drift": True,
        "new_fields": ["coupon_code", "delivery_partner"],
        "source": "fivetran_mcp_fallback",
        "summary": (
            "Fivetran MCP tool call completed, but no live Fivetran connections were found "
            "in this trial account. PipelinePilot AI used demo pipeline status so the "
            "agent workflow could continue."
        )
    }


def _call_fivetran_account_api():
    """
    This is the current practical MCP-style bridge.
    It checks Fivetran connection availability using Fivetran credentials.
    Later, this wrapper can be replaced with the official Fivetran MCP client call.
    """

    if not FIVETRAN_API_KEY or not FIVETRAN_API_SECRET:
        return {
            "mcp_call_status": "Not connected",
            "mcp_result": "Fivetran API credentials are missing",
            "connections_found": 0,
            "connections": []
        }

    url = f"{FIVETRAN_API_BASE}/connections"

    headers = {
        "Accept": "application/json;version=2"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            auth=HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET),
            timeout=30
        )

        if response.status_code != 200:
            return {
                "mcp_call_status": "Failed",
                "mcp_result": f"Fivetran returned {response.status_code}: {response.text}",
                "connections_found": 0,
                "connections": []
            }

        data = response.json()
        connections = data.get("data", {}).get("items", [])

        if not connections:
            return {
                "mcp_call_status": "Connected",
                "mcp_result": "Connected, no live connections found",
                "connections_found": 0,
                "connections": []
            }

        return {
            "mcp_call_status": "Connected",
            "mcp_result": f"Connected, {len(connections)} live connection(s) found",
            "connections_found": len(connections),
            "connections": connections
        }

    except Exception as e:
        return {
            "mcp_call_status": "Failed",
            "mcp_result": str(e),
            "connections_found": 0,
            "connections": []
        }


def get_pipeline_status(source, dataset):
    mcp_result = _call_fivetran_account_api()
    connections = mcp_result.get("connections", [])

    if not connections:
        return _demo_fallback(source, dataset, mcp_result)

    selected = None

    for conn in connections:
        schema = str(conn.get("schema", "")).lower()
        service = str(conn.get("service", "")).lower()

        if dataset.lower() in schema or source.lower() in service:
            selected = conn
            break

    if not selected:
        selected = connections[0]

    status_obj = selected.get("status", {})
    tasks = status_obj.get("tasks", [])
    warnings = status_obj.get("warnings", [])

    setup_state = status_obj.get("setup_state", "unknown")
    sync_state = status_obj.get("sync_state", "unknown")
    paused = selected.get("paused", False)

    schema_drift = len(warnings) > 0 or len(tasks) > 0

    warning_messages = []
    for warning in warnings:
        if isinstance(warning, dict):
            warning_messages.append(warning.get("message", str(warning)))
        else:
            warning_messages.append(str(warning))

    task_messages = []
    for task in tasks:
        if isinstance(task, dict):
            task_messages.append(task.get("message", str(task)))
        else:
            task_messages.append(str(task))

    status_text = f"setup_state={setup_state}, sync_state={sync_state}, paused={paused}"

    return {
        "integration_mode": "MCP",
        "mcp_call_status": mcp_result.get("mcp_call_status"),
        "mcp_result": mcp_result.get("mcp_result"),
        "connections_found": mcp_result.get("connections_found"),
        "fallback_used": False,
        "fallback_status": None,
        "connector": selected.get("schema", selected.get("id", "unknown")),
        "status": status_text,
        "last_sync": selected.get("succeeded_at") or selected.get("updated_at") or "Not available",
        "schema_drift": schema_drift,
        "new_fields": warning_messages + task_messages,
        "source": "fivetran_mcp",
        "summary": (
            f"Fivetran MCP checked connection {selected.get('schema', selected.get('id'))}. "
            f"Status: {status_text}. "
            f"Warnings/tasks found: {len(warning_messages) + len(task_messages)}."
        )
    }