from flask import Flask, request, jsonify

app = Flask(__name__)

tasks = {
    1: {"id": 1, "user_id": 1, "title": "Learn Docker Compose", "completed": False},
    2: {"id": 2, "user_id": 1, "title": "Test REST API", "completed": False},
    3: {"id": 3, "user_id": 2, "title": "Write laboratory report", "completed": True}
}

next_task_id = 4


@app.route("/")
def home():
    return jsonify({
        "service": "Service B",
        "description": "Tasks REST API",
        "status": "running"
    })


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(list(tasks.values()))


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = tasks.get(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task)


@app.route("/tasks/by-user/<int:user_id>", methods=["GET"])
def get_tasks_by_user(user_id):
    user_tasks = [
        task for task in tasks.values()
        if task["user_id"] == user_id
    ]

    return jsonify(user_tasks)


@app.route("/tasks", methods=["POST"])
def create_task():
    global next_task_id

    data = request.get_json()

    if not data or "user_id" not in data or "title" not in data:
        return jsonify({"error": "Fields 'user_id' and 'title' are required"}), 400

    task = {
        "id": next_task_id,
        "user_id": data["user_id"],
        "title": data["title"],
        "completed": data.get("completed", False)
    }

    tasks[next_task_id] = task
    next_task_id += 1

    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = tasks.get(task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is empty"}), 400

    task["user_id"] = data.get("user_id", task["user_id"])
    task["title"] = data.get("title", task["title"])
    task["completed"] = data.get("completed", task["completed"])

    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = tasks.pop(task_id, None)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "message": "Task deleted successfully",
        "deleted_task": task
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)