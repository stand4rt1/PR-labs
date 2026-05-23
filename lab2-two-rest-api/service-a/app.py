from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

users = {
    1: {"id": 1, "name": "Ion Popescu", "email": "ion@example.com"},
    2: {"id": 2, "name": "Maria Rusu", "email": "maria@example.com"}
}

next_user_id = 3
TASK_SERVICE_URL = "http://service-b:5001"


@app.route("/")
def home():
    return jsonify({
        "service": "Service A",
        "description": "Users REST API",
        "status": "running"
    })


@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(list(users.values()))


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.get(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user)


@app.route("/users", methods=["POST"])
def create_user():
    global next_user_id

    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "Fields 'name' and 'email' are required"}), 400

    user = {
        "id": next_user_id,
        "name": data["name"],
        "email": data["email"]
    }

    users[next_user_id] = user
    next_user_id += 1

    return jsonify(user), 201


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = users.get(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is empty"}), 400

    user["name"] = data.get("name", user["name"])
    user["email"] = data.get("email", user["email"])

    return jsonify(user)


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = users.pop(user_id, None)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "message": "User deleted successfully",
        "deleted_user": user
    })


@app.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    try:
        response = requests.get(f"{TASK_SERVICE_URL}/tasks/by-user/{user_id}", timeout=5)
        response.raise_for_status()

        return jsonify({
            "user": users[user_id],
            "tasks": response.json()
        })

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to Service B",
            "details": str(error)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)