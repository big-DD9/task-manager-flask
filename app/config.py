import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()


class Config:
    """Base config with settings shared across all environments."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///task_manager.db"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    # In-memory SQLite normally gives each connection its own empty DB.
    # StaticPool forces every connection to share the same one, which is
    # what we want for tests.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }


class ProductionConfig(Config):
    DEBUG = False
    # In production these MUST be set via environment variables (e.g. on EC2
    # via systemd EnvironmentFile, or AWS Secrets Manager). The app will
    # refuse to start with default secrets - see __init__.py.


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
