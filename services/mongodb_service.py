import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "pipelinepilot")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing. Add it to your .env file.")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000
)

db = client[MONGODB_DB]


def get_orders():
    return list(db.orders.find({}, {"_id": 0}))


def save_task(task):
    db.tasks.insert_one(task)


def get_tasks():
    return list(db.tasks.find({}, {"_id": 0}).sort("created_at", -1))


def get_task(task_id):
    return db.tasks.find_one({"task_id": task_id}, {"_id": 0})


def save_messages(task_id, messages):
    docs = []

    for msg in messages:
        docs.append({
            "task_id": task_id,
            "actor": msg.get("actor"),
            "message": msg.get("message"),
            "created_at": datetime.utcnow().isoformat()
        })

    if docs:
        db.messages.insert_many(docs)


def get_messages(task_id):
    return list(db.messages.find({"task_id": task_id}, {"_id": 0}))


def test_connection():
    db.command("ping")
    return True


def add_message(task_id, actor, message):
    db.messages.insert_one({
        "task_id": task_id,
        "actor": actor,
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    })

def approve_gitlab_action(task_id, gitlab_result):
    result = db.tasks.update_one(
        {"task_id": task_id},
        {
            "$set": {
                "gitlab_action.status": "Approved - GitLab work item created",
                "gitlab_action.gitlab_url": gitlab_result.get("web_url"),
                "gitlab_action.issue_id": gitlab_result.get("issue_id"),
                "approval_status": "Approved"
            }
        }
    )

    db.approvals.insert_one({
        "task_id": task_id,
        "approval_status": "Approved",
        "action": "GitLab work item created",
        "gitlab_url": gitlab_result.get("web_url"),
        "issue_id": gitlab_result.get("issue_id"),
        "created_at": datetime.utcnow().isoformat()
    })

    add_message(task_id, "Human", "Approved GitLab action.")
    add_message(
        task_id,
        "GitLab",
        f"Created GitLab work item #{gitlab_result.get('issue_id')}: {gitlab_result.get('web_url')}"
    )

    return result.modified_count > 0

def save_report(task):
    report = {
        "task_id": task.get("task_id"),
        "task_type": task.get("task_type"),
        "dataset": task.get("dataset"),
        "source": task.get("source"),
        "target": task.get("target"),
        "status": task.get("status"),
        "readiness_score": task.get("readiness_score"),
        "fivetran_status": task.get("fivetran_status"),
        "quality_result": task.get("quality_result"),
        "support_result": task.get("support_result"),
        "transformation": task.get("transformation"),
        "agent_summary": task.get("agent_summary"),
        "gitlab_action": task.get("gitlab_action"),
        "created_at": datetime.utcnow().isoformat(),
        "bigquery_result": task.get("bigquery_result")
    }

    db.reports.insert_one(report)
    return True


def get_report(task_id):
    return db.reports.find_one({"task_id": task_id}, {"_id": 0})