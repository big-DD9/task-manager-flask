# Task Manager Backend (Flask)

A RESTful task management backend system built with Flask and SQLAlchemy.

## Overview

This project demonstrates backend architectural principles including:

- App Factory Pattern
- Blueprint route separation
- Relational database modeling
- One-to-many relationships
- RESTful API design
- Structured error handling

##  Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite (default)
- REST API Architecture

##  API Endpoints

### Users
POST /users/

### Tasks
POST /tasks/
GET /tasks/<id>
PUT /tasks/<id>
DELETE /tasks/<id>

##  Database Design

- User → One-to-Many → Task
- Task includes status-based workflow management

##  Run Locally

1. Clone repo
2. Install dependencies:
   pip install -r requirements.txt
3. Run:
   python run.py
