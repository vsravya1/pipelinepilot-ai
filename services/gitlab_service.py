import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_API_BASE = "https://gitlab.com/api/v4"


def prepare_gitlab_action(task_type, dataset, quality_result, support_result=None, transformation=None):
    title = f"{task_type}: Review required for {dataset}"

    lines = [
        f"Task Type: {task_type}",
        f"Dataset: {dataset}",
        f"Readiness Score: {quality_result['score']}/100",
        f"Status: {quality_result['status']}",
        "",
        "Data Quality Issues:"
    ]

    if quality_result["issues"]:
        for issue in quality_result["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- No data quality issues found")

    lines.append("")
    lines.append("Recommended Safe Fixes:")

    for fix in quality_result["safe_fixes"]:
        lines.append(f"- {fix}")

    if support_result:
        lines.append("")
        lines.append("Production Support Finding:")
        lines.append(f"- Root Cause: {support_result['root_cause']}")
        lines.append(f"- Impact: {support_result['impact']}")
        lines.append(f"- Recommended Fix: {support_result['recommended_fix']}")

    if transformation:
        lines.append("")
        lines.append("Generated Transformation SQL:")
        lines.append("```sql")
        lines.append(transformation["sql"])
        lines.append("```")

    return {
        "title": title,
        "description": "\n".join(lines),
        "status": "Prepared - waiting for human approval",
        "gitlab_url": None
    }


def create_gitlab_issue(title, description):
    if not GITLAB_TOKEN:
        raise ValueError("GITLAB_TOKEN is missing in .env")

    if not GITLAB_PROJECT_ID:
        raise ValueError("GITLAB_PROJECT_ID is missing in .env")

    url = f"{GITLAB_API_BASE}/projects/{GITLAB_PROJECT_ID}/issues"

    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
    }

    payload = {
        "title": title,
        "description": description,
        "labels": "pipelinepilot-ai,dataops,agent-generated"
    }

    response = requests.post(url, headers=headers, data=payload, timeout=30)

    if response.status_code not in [200, 201]:
        raise Exception(f"GitLab issue creation failed: {response.status_code} - {response.text}")

    issue = response.json()

    return {
        "issue_id": issue.get("iid"),
        "web_url": issue.get("web_url"),
        "title": issue.get("title")
    }