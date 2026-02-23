from flask import Flask
from .config import Config
from .extensions import db
from .routes.user_routes import user_bp
from .routes.task_routes import task_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(task_bp, url_prefix="/tasks")

    return app