import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

FIVETRAN_API_KEY = os.getenv("FIVETRAN_API_KEY")
FIVETRAN_API_SECRET = os.getenv("FIVETRAN_API_SECRET")
FIVETRAN_API_BASE = "https://api.fivetran.com/v1"


def _mock_pipeline_status(source, dataset, reason="Using demo status"):
    return {
        "connector": f"{source} {dataset} connector",
        "status": "Healthy with warning",
        "last_sync": "18 minutes ago",
        "schema_drift": True,
        "new_fields": ["coupon_code", "delivery_partner"],
        "source": "mock",
        "summary": (
            f"{reason}. Fivetran pipeline checked. Last sync was 18 minutes ago. "
            "Schema drift detected: new fields coupon_code and delivery_partner."
        )
    }


def _get_connections():
    if not FIVETRAN_API_KEY or not FIVETRAN_API_SECRET:
        return None, "Fivetran API credentials are missing"

    url = f"{FIVETRAN_API_BASE}/connections"

    headers = {
        "Accept": "application/json;version=2"
    }

    response = requests.get(
        url,
        headers=headers,
        auth=HTTPBasicAuth(FIVETRAN_API_KEY, FIVETRAN_API_SECRET),
        timeout=30
    )

    if response.status_code not in [200]:
        return None, f"Fivetran API returned {response.status_code}: {response.text}"

    return response.json(), None


def get_pipeline_status(source, dataset):
    data, error = _get_connections()

    if error:
        return _mock_pipeline_status(source, dataset, reason=error)

    connections = data.get("data", {}).get("items", [])

    if not connections:
        return _mock_pipeline_status(
            source,
            dataset,
            reason="No Fivetran connections found in this trial account"
        )

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
        "connector": selected.get("schema", selected.get("id", "unknown")),
        "status": status_text,
        "last_sync": selected.get("succeeded_at") or selected.get("updated_at") or "Not available",
        "schema_drift": schema_drift,
        "new_fields": warning_messages + task_messages,
        "source": "fivetran_api",
        "summary": (
            f"Fivetran API checked connection {selected.get('schema', selected.get('id'))}. "
            f"Status: {status_text}. "
            f"Warnings/tasks found: {len(warning_messages) + len(task_messages)}."
        )
    }