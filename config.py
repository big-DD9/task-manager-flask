import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///task_manager.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False