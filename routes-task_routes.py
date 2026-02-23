from flask import Blueprint, request, jsonify
from ..models import Task
from ..extensions import db

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/", methods=["POST"])
def create_task():
    data = request.get_json()

    required_fields = ["title", "user_id"]

    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Title and user_id required"}), 400

    task = Task(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "pending"),
        user_id=data["user_id"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "user_id": task.user_id
    }), 201


@task_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "user_id": task.user_id
    })


@task_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()

    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify({"message": "Task updated"})


@task_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"})