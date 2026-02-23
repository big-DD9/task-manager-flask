from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    tasks = db.relationship("Task", backref="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(50), default="pending")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)