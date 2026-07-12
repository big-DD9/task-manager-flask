# Task Manager API

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

## Running locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edit secrets if you want

python run.py
```

API runs on `http://localhost:5000`. Try it:

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Solo","email":"solo@example.com","password":"testpassword123"}'
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
- [ ] Dockerize + docker-compose (Postgres)
- [ ] Deploy to AWS (EC2 + RDS)
- [ ] CloudWatch logging/alarms
- [ ] GitHub Actions CI/CD
