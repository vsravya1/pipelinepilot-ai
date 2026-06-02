from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = []

@app.route("/")
def create_task():
    return render_template("create_task.html")

@app.route("/run-task", methods=["POST"])
def run_task():
    task_type = request.form.get("task_type")
    source = request.form.get("source")
    goal = request.form.get("goal")

    task = {
        "id": len(tasks) + 1,
        "task_type": task_type,
        "source": source,
        "goal": goal,
        "status": "Completed",
        "score": 78,
        "summary": "PipelinePilot AI completed a mock multi-agent DataOps workflow.",
        "fivetran_status": "Healthy, last sync 18 minutes ago",
        "issues": [
            "Schema drift detected: new field coupon_code",
            "27 records missing customer_id",
            "9 records have negative order_amount",
            "14 records have invalid timestamp format"
        ],
        "recommendations": [
            "Add customer_id null validation",
            "Quarantine negative order_amount records",
            "Standardize created_at timestamp format",
            "Update transformation to include coupon_code"
        ],
        "agent_steps": [
            "Supervisor Agent created execution plan",
            "Fivetran MCP checked connector health and sync freshness",
            "Data Engineer Agent generated transformation logic",
            "Data Quality Agent ran validation checks",
            "Production Support Agent summarized business impact",
            "GitLab action prepared and waiting for approval"
        ]
    }

    tasks.append(task)
    return render_template("result.html", task=task)

@app.route("/tasks")
def view_tasks():
    return render_template("view_tasks.html", tasks=tasks)

if __name__ == "__main__":
    app.run(debug=True)
