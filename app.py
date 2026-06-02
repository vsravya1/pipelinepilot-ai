from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = []

@app.route("/")
def create_task():
    return render_template("create_task.html")

@app.route("/run-task", methods=["POST"])
def run_task():
    task = {
        "id": len(tasks) + 1,
        "task_type": request.form.get("task_type"),
        "source": request.form.get("source"),
        "goal": request.form.get("goal"),
        "status": "Completed",
        "score": 82,
        "summary": "Mock agent workflow completed. Real integrations will be added next."
    }
    tasks.append(task)
    return render_template("result.html", task=task)

@app.route("/tasks")
def view_tasks():
    return render_template("view_tasks.html", tasks=tasks)

if __name__ == "__main__":
    app.run(debug=True)
