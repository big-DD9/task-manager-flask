from flask import Blueprint, request, jsonify
from ..models import User
from ..extensions import db

user_bp = Blueprint("users", __name__)


@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "Name and email required"}), 400

    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 201