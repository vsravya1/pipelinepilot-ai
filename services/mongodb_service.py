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


def approve_gitlab_action(task_id, gitlab_result):
    result = db.tasks.update_one(
        {"task_id": task_id},
        {
            "$set": {
                "gitlab_action.status": "Approved - GitLab issue created",
                "gitlab_action.gitlab_url": gitlab_result.get("web_url"),
                "gitlab_action.issue_id": gitlab_result.get("issue_id"),
                "approval_status": "Approved"
            }
        }
    )

    db.approvals.insert_one({
        "task_id": task_id,
        "approval_status": "Approved",
        "action": "GitLab issue created",
        "gitlab_url": gitlab_result.get("web_url"),
        "issue_id": gitlab_result.get("issue_id"),
        "created_at": datetime.utcnow().isoformat()
    })

    return result.modified_count > 0   