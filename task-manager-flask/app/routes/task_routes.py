from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.extensions import db
from app.models import Task
from app.schemas import TaskCreateSchema, TaskUpdateSchema

task_bp = Blueprint("tasks", __name__)

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()


def _get_owned_task_or_none(task_id, user_id):
    return Task.query.filter_by(id=task_id, user_id=user_id).first()


@task_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    status_filter = request.args.get("status")

    query = Task.query.filter_by(user_id=user_id)
    if status_filter:
        if status_filter not in Task.VALID_STATUSES:
            return jsonify({
                "error": f"Invalid status filter. Must be one of {Task.VALID_STATUSES}"
            }), 400
        query = query.filter_by(status=status_filter)

    tasks = query.order_by(Task.id.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@task_bp.route("/", methods=["POST"])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()

    try:
        data = task_create_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    task = Task(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "pending"),
        user_id=user_id,
    )
    db.session.add(task)
    db.session.commit()

    current_app.logger.info(f"Task {task.id} created by user {user_id}")

    return jsonify(task.to_dict()), 201


@task_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    task = _get_owned_task_or_none(task_id, user_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(task.to_dict())


@task_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    task = _get_owned_task_or_none(task_id, user_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    try:
        data = task_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    for field in ("title", "description", "status"):
        if field in data:
            setattr(task, field, data[field])

    db.session.commit()
    current_app.logger.info(f"Task {task.id} updated by user {user_id}")

    return jsonify(task.to_dict())


@task_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = _get_owned_task_or_none(task_id, user_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()
    current_app.logger.info(f"Task {task.id} deleted by user {user_id}")

    return jsonify({"message": "Task deleted"})
