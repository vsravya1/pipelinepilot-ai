from flask import Flask, render_template, request, redirect, url_for
from agents.supervisor_agent import run_workflow
from services.mongodb_service import get_tasks, get_task, get_messages, get_report, approve_gitlab_action
from services.gitlab_service import create_gitlab_issue

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("create_task.html")


@app.route("/run-task", methods=["POST"])
def run_task():
    task_type = request.form.get("task_type")
    source = request.form.get("source")
    dataset = request.form.get("dataset")
    target = request.form.get("target")
    goal = request.form.get("goal")
    pipeline_mode = request.form.get("pipeline_mode")

    task = run_workflow(
    task_type=task_type,
    source=source,
    dataset=dataset,
    target=target,
    goal=goal,
    pipeline_mode=pipeline_mode
    )
    return render_template("result.html", task=task)


@app.route("/tasks")
def view_tasks():
    tasks = get_tasks()
    return render_template("view_tasks.html", tasks=tasks, selected_task=None)


@app.route("/tasks/<task_id>")
def task_detail(task_id):
    tasks = get_tasks()
    selected_task = get_task(task_id)
    messages = get_messages(task_id)

    if selected_task:
        selected_task["saved_messages"] = messages
        selected_task["saved_report"] = get_report(task_id)

    return render_template(
        "view_tasks.html",
        tasks=tasks,
        selected_task=selected_task
    )

@app.route("/approve-gitlab/<task_id>", methods=["POST"])
def approve_gitlab(task_id):
    task = get_task(task_id)

    if not task:
        return "Task not found", 404

    gitlab_action = task.get("gitlab_action", {})

    gitlab_result = create_gitlab_issue(
        title=gitlab_action.get("title"),
        description=gitlab_action.get("description")
    )

    approve_gitlab_action(task_id, gitlab_result)

    return redirect(url_for("task_detail", task_id=task_id))


if __name__ == "__main__":
    app.run(debug=True)