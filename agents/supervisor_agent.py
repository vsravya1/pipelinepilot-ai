import uuid
from datetime import datetime

from services.fivetran_service import get_pipeline_status
from services.gitlab_service import prepare_gitlab_action
from services.mongodb_service import save_task, save_messages

from agents.data_engineer_agent import generate_transformation
from agents.data_quality_agent import run_quality_checks
from agents.prod_support_agent import investigate_issue


def create_plan(task_type, source, dataset, target, goal):
    if task_type == "New Job Creation":
        return [
            "Check Fivetran pipeline/source readiness",
            "Inspect source schema",
            "Generate transformation logic",
            "Create data quality rules",
            "Run data quality checks",
            "Prepare release readiness report",
            "Prepare GitLab checklist for approval"
        ]

    if task_type == "Production Support Issue":
        return [
            "Check Fivetran connector health",
            "Review last sync status",
            "Detect possible schema drift",
            "Run data quality impact checks",
            "Identify likely root cause",
            "Prepare GitLab incident issue for approval"
        ]

    return [
        "Load source dataset",
        "Run data quality checks",
        "Identify failed rules",
        "Recommend safe correction actions",
        "Prepare GitLab data quality issue for approval"
    ]


def run_workflow(task_type, source, dataset, target, goal):
    task_id = "TASK-" + str(uuid.uuid4())[:8].upper()
    created_at = datetime.utcnow().isoformat()

    messages = []

    def add_message(actor, message):
        messages.append({
            "actor": actor,
            "message": message
        })

    add_message("User", goal)

    plan = create_plan(task_type, source, dataset, target, goal)
    add_message("Supervisor Agent", "Created execution plan: " + " → ".join(plan))

    fivetran_status = get_pipeline_status(source, dataset)
    add_message("Fivetran MCP", fivetran_status["summary"])

    transformation = None
    support_result = None

    if task_type == "New Job Creation":
        transformation = generate_transformation(dataset, target)
        add_message("Data Engineer Agent", transformation["summary"])

    quality_result = run_quality_checks()
    add_message("Data Quality Agent", quality_result["summary"])

    if task_type == "Production Support Issue":
        support_result = investigate_issue(dataset, fivetran_status, quality_result)
        add_message("Production Support Agent", support_result["summary"])

    if task_type == "Data Quality Check":
        add_message(
            "Data Quality Agent",
            "Recommended safe correction actions: " + "; ".join(quality_result["safe_fixes"])
        )

    gitlab_action = prepare_gitlab_action(
        task_type=task_type,
        dataset=dataset,
        quality_result=quality_result,
        support_result=support_result,
        transformation=transformation
    )

    add_message("Supervisor Agent", "Prepared GitLab action and waiting for human approval.")

    task = {
        "task_id": task_id,
        "created_at": created_at,
        "task_type": task_type,
        "source": source,
        "dataset": dataset,
        "target": target,
        "goal": goal,
        "plan": plan,
        "fivetran_status": fivetran_status,
        "transformation": transformation,
        "support_result": support_result,
        "quality_result": quality_result,
        "gitlab_action": gitlab_action,
        "status": quality_result["status"],
        "readiness_score": quality_result["score"],
        "messages": messages
    }

    save_task(task)
    save_messages(task_id, messages)

    return task