import os
import time
import json
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app)
sock = Sock(app)

websocket_clients = set()


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "todo_db"),
        user=os.environ.get("DB_USER", "todo_user"),
        password=os.environ.get("DB_PASSWORD", "todo_password"),
        port=os.environ.get("DB_PORT", "5432")
    )


def init_database():
    for attempt in range(10):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT FALSE
                );
            """)

            connection.commit()
            cursor.close()
            connection.close()

            print("Database initialized successfully.")
            return

        except Exception as error:
            print(f"Database is not ready yet. Attempt {attempt + 1}/10")
            print(error)
            time.sleep(3)

    raise Exception("Could not connect to database.")


def broadcast_tasks_update(action):
    message = json.dumps({
        "event": "tasks_updated",
        "action": action
    })

    disconnected_clients = []

    for client in websocket_clients:
        try:
            client.send(message)
        except Exception:
            disconnected_clients.append(client)

    for client in disconnected_clients:
        websocket_clients.discard(client)


@sock.route("/ws")
def websocket(ws):
    websocket_clients.add(ws)
    print("WebSocket client connected.")

    try:
        while True:
            message = ws.receive()

            if message is None:
                break

            ws.send(json.dumps({
                "event": "connection_alive",
                "message": "WebSocket connection is active"
            }))

    except Exception as error:
        print(f"WebSocket error: {error}")

    finally:
        websocket_clients.discard(ws)
        print("WebSocket client disconnected.")


@app.route("/")
def home():
    return jsonify({
        "service": "Todo Backend API with WebSocket",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/tasks", methods=["GET"])
def get_tasks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, description, completed
        FROM tasks
        ORDER BY id;
    """)

    rows = cursor.fetchall()

    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "completed": row[3]
        })

    cursor.close()
    connection.close()

    return jsonify(tasks)


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, description, completed
        FROM tasks
        WHERE id = %s;
    """, (task_id,))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    })


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Field 'title' is required"}), 400

    title = data["title"]
    description = data.get("description", "")
    completed = data.get("completed", False)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO tasks (title, description, completed)
        VALUES (%s, %s, %s)
        RETURNING id, title, description, completed;
    """, (title, description, completed))

    row = cursor.fetchone()
    connection.commit()

    cursor.close()
    connection.close()

    task = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    }

    broadcast_tasks_update("created")

    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is empty"}), 400

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, description, completed
        FROM tasks
        WHERE id = %s;
    """, (task_id,))

    existing_task = cursor.fetchone()

    if existing_task is None:
        cursor.close()
        connection.close()
        return jsonify({"error": "Task not found"}), 404

    title = data.get("title", existing_task[1])
    description = data.get("description", existing_task[2])
    completed = data.get("completed", existing_task[3])

    cursor.execute("""
        UPDATE tasks
        SET title = %s, description = %s, completed = %s
        WHERE id = %s
        RETURNING id, title, description, completed;
    """, (title, description, completed, task_id))

    row = cursor.fetchone()
    connection.commit()

    cursor.close()
    connection.close()

    task = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    }

    broadcast_tasks_update("updated")

    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM tasks
        WHERE id = %s
        RETURNING id, title, description, completed;
    """, (task_id,))

    row = cursor.fetchone()
    connection.commit()

    cursor.close()
    connection.close()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    deleted_task = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    }

    broadcast_tasks_update("deleted")

    return jsonify({
        "message": "Task deleted successfully",
        "deleted_task": deleted_task
    })


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5000)