# Task Manager API

![CI/CD](https://github.com/big-DD9/task-manager-flask/actions/workflows/ci.yml/badge.svg)

A Flask REST API for managing tasks, with JWT authentication and per-user
task isolation. Built as a portfolio project demonstrating production-style
backend practices: auth, input validation, testing, structured logging, and
(coming in later phases) containerized AWS deployment.

## Features

- JWT-based auth (register / login)
- Full task CRUD, scoped to the authenticated user
- Task filtering by status (`?status=done`)
- Request validation via Marshmallow schemas
- Structured logging (stdout, ready to ship to CloudWatch)
- 15 passing pytest tests covering auth, CRUD, and cross-user isolation

## Tech stack

Flask, SQLAlchemy, Flask-JWT-Extended, Marshmallow, pytest. SQLite for local
dev, PostgreSQL in production (RDS).

## Project structure

```
app/
  __init__.py       # app factory
  config.py         # dev/test/prod config
  extensions.py      # db, jwt instances
  models.py          # User, Task
  schemas.py          # request validation
  logging_config.py
  routes/
    auth_routes.py    # /auth/register, /auth/login
    user_routes.py     # /users/me
    task_routes.py      # /tasks CRUD
tests/
run.py
```

## Running locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements-dev.txt

cp .env.example .env

python run.py
```

## Running with Docker (app + Postgres)

This runs the whole stack - Flask app and a real Postgres database - in
containers, matching what production (EC2 + RDS) will look like.

```bash
docker compose up --build
```

API runs on `http://localhost:5000`. Postgres is on `localhost:5432` if you
want to inspect it with a DB tool.

Stop everything:
```bash
docker compose down
```

Stop and wipe the database too (fresh start):
```bash
docker compose down -v
```

## Running tests

```bash
pytest tests/ -v
```

## API endpoints

| Method | Endpoint             | Auth required | Description              |
|--------|-----------------------|----------------|---------------------------|
| POST   | /auth/register         | No             | Create account, returns JWT |
| POST   | /auth/login             | No             | Log in, returns JWT        |
| GET    | /users/me                | Yes            | Current user's profile     |
| GET    | /tasks/                  | Yes            | List your tasks (`?status=`) |
| POST   | /tasks/                   | Yes            | Create a task               |
| GET    | /tasks/<id>                 | Yes            | Get one task                 |
| PUT    | /tasks/<id>                   | Yes            | Update a task                  |
| DELETE | /tasks/<id>                     | Yes            | Delete a task                    |
| GET    | /health                            | No             | Health check (for load balancer) |

## Roadmap

- [x] Auth, validation, tests, logging
- [x] Dockerize + docker-compose (Postgres)
- [x] GitHub Actions CI/CD - tests run on every push/PR; a Docker image is
      built and published to GitHub Container Registry on every merge to
      main (see [Packages](../../pkgs/container/task-manager-flask))
- [ ] Deploy to AWS (EC2 + RDS)
- [ ] CloudWatch logging/alarms
