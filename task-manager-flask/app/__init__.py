import os
from flask import Flask, jsonify
from app.config import config_by_name
from app.extensions import db, jwt
from app.logging_config import configure_logging


def create_app(env=None):
    app = Flask(__name__)

    env = env or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name[env])

    if env == "production":
        _guard_against_default_secrets(app)

    configure_logging(app)

    db.init_app(app)
    jwt.init_app(app)

    # Import models before create_all() so their tables are registered on
    # db.metadata - calling create_all() before models are imported is a
    # common bug that silently results in zero tables being created.
    from app import models  # noqa: F401

    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.task_routes import task_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(task_bp, url_prefix="/tasks")

    with app.app_context():
        db.create_all()

    @app.route("/health")
    def health():
        # Used by load balancer / uptime checks in later deployment phases
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    return app


def _guard_against_default_secrets(app):
    if app.config["SECRET_KEY"] == "dev-secret-change-me-please-and-thank-you" or \
       app.config["JWT_SECRET_KEY"] == "dev-jwt-secret-change-me-please-and-thank-you":
        raise RuntimeError(
            "Refusing to start in production with default secrets. "
            "Set SECRET_KEY and JWT_SECRET_KEY environment variables."
        )
