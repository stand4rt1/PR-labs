const API_URL = "http://localhost:5000";

async function loadTasks() {
    const response = await fetch(`${API_URL}/tasks`);
    const tasks = await response.json();

    const tableBody = document.getElementById("tasksTableBody");
    tableBody.innerHTML = "";

    tasks.forEach(task => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${task.id}</td>
            <td>
                <input id="title-${task.id}" value="${task.title}">
            </td>
            <td>
                <input id="description-${task.id}" value="${task.description || ""}">
            </td>
            <td>
                <input type="checkbox" id="completed-${task.id}" ${task.completed ? "checked" : ""}>
            </td>
            <td>
                <button onclick="updateTask(${task.id})">Update</button>
                <button onclick="deleteTask(${task.id})">Delete</button>
                <button onclick="sendTaskEmail(${task.id})">Send Email</button>
            </td>
        `;

        tableBody.appendChild(row);
    });
}

async function createTask() {
    const title = document.getElementById("titleInput").value;
    const description = document.getElementById("descriptionInput").value;

    if (!title) {
        alert("Task title is required.");
        return;
    }

    await fetch(`${API_URL}/tasks`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: title,
            description: description,
            completed: false
        })
    });

    document.getElementById("titleInput").value = "";
    document.getElementById("descriptionInput").value = "";

    loadTasks();
}

async function updateTask(taskId) {
    const title = document.getElementById(`title-${taskId}`).value;
    const description = document.getElementById(`description-${taskId}`).value;
    const completed = document.getElementById(`completed-${taskId}`).checked;

    await fetch(`${API_URL}/tasks/${taskId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: title,
            description: description,
            completed: completed
        })
    });

    loadTasks();
}

async function deleteTask(taskId) {
    await fetch(`${API_URL}/tasks/${taskId}`, {
        method: "DELETE"
    });

    loadTasks();
}

async function getTaskById() {
    const taskId = document.getElementById("taskIdInput").value;
    const result = document.getElementById("singleTaskResult");

    if (!taskId) {
        alert("Task ID is required.");
        return;
    }

    const response = await fetch(`${API_URL}/tasks/${taskId}`);
    const data = await response.json();

    result.textContent = JSON.stringify(data, null, 2);
}

loadTasks();

async function sendTaskEmail(taskId) {
    const email = document.getElementById("emailInput").value;

    if (!email) {
        alert("Recipient email is required.");
        return;
    }

    const response = await fetch(`${API_URL}/tasks/${taskId}/email`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email
        })
    });

    const result = await response.json();

    if (response.ok) {
        alert("Email sent successfully.");
    } else {
        alert("Email sending failed: " + JSON.stringify(result));
    }
}