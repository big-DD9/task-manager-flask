# Phase 2 Notes: Dockerizing the Task Manager

This documents every change made today, why it was made, and what each
piece of code does. Keep this as a reference for interviews - it's
basically the "walk me through your architecture" answer already written
out.

---

## 1. Bug fix: `app/config.py` - the `DATABASE_URL` empty-string trap

**Before:**
```python
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///task_manager.db"
)
```

**After:**
```python
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///task_manager.db"
```

**Why:** `os.getenv("VAR", default)`'s `default` argument only kicks in when
the variable is completely *unset* in the environment. If `.env` contains
`DATABASE_URL=` (set to an empty string), Python sees that as "this
variable exists, its value is `''`" - not "this variable doesn't exist."
So the SQLite fallback never triggered, and SQLAlchemy crashed trying to
parse an empty string as a database URL. This is exactly the crash you hit
when first running `python run.py` on Windows.

The fix (`os.getenv("DATABASE_URL") or "sqlite:///..."`) treats *any*
falsy value - `None` (truly unset) or `""` (empty) - the same way, falling
back to SQLite in both cases. This matters more now because Docker will be
setting `DATABASE_URL` explicitly to a Postgres connection string, and we
want local (non-Docker) runs to keep defaulting cleanly to SQLite.

---

## 2. Bug fix: weak default JWT secret

**Before:** `"dev-secret-change-me"` / `"dev-jwt-secret-change-me"` (both
under 32 bytes)

**After:** `"dev-secret-change-me-please-and-thank-you"` (longer)

**Why:** JWT's HMAC-SHA256 signing algorithm recommends a minimum 32-byte
key. The short default was triggering an `InsecureKeyLengthWarning` on
every test run. Harmless for local dev (these are never real secrets -
production refuses to start with defaults at all, see `__init__.py`), but
worth cleaning up rather than ignoring a warning that would look bad if
someone reviewing your code saw it firing.

---

## 3. Splitting `requirements.txt` into three files

**Before:** one `requirements.txt` with everything, including `pytest`.

**After:**
- **`requirements.txt`** - only what the app needs to actually run (Flask,
  SQLAlchemy, JWT, etc.). No test tools, no Postgres driver.
- **`requirements-dev.txt`** - `requirements.txt` plus `pytest` and
  `pytest-flask`, for local development/testing.
- **`requirements-docker.txt`** - `requirements.txt` plus
  `psycopg2-binary` (the Postgres driver), used only inside the Docker
  image.

**Why:** Two separate problems, one fix.

First: your Docker image should only contain what production actually
runs - not test tools. Smaller image, smaller attack surface, faster
builds.

Second: `psycopg2-binary` was the exact package that failed to install on
your Windows machine (it tried to compile from source and needed
`pg_config`, which you don't have). It only fails like that in certain
environments where a prebuilt wheel isn't available for your exact Python
version. Docker's Linux environment doesn't have that problem - clean
wheels are available there. By keeping `psycopg2-binary` out of
`requirements.txt` and `requirements-dev.txt`, your Windows local dev
workflow (`pip install -r requirements-dev.txt`) never touches that
package at all, and you'll never hit that error again locally. It only
gets installed inside the Docker build, where it works fine.

---

## 4. `Dockerfile` - the recipe for building the app's container image

Walking through it top to bottom:

```dockerfile
FROM python:3.12-slim
```
Base image. `slim` is a stripped-down Debian with just enough to run
Python - much smaller than the full `python:3.12` image (which includes a
lot of build tools and libraries you don't need at runtime).

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```
Two Python behavior tweaks. The first stops Python from writing `.pyc`
compiled bytecode files into the image (pointless in a container that gets
rebuilt from scratch each time anyway). The second disables output
buffering - without it, your app's log messages could sit in a buffer and
not show up in `docker logs` right away, which is annoying when you're
trying to debug something live.

```dockerfile
WORKDIR /app
```
Sets `/app` as the working directory inside the container - all following
commands (`COPY`, `RUN`, etc.) happen relative to this.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
```
Installs the system-level tools needed to build `psycopg2-binary`
(`libpq-dev` is the Postgres client library, `gcc` is a C compiler). The
`rm -rf /var/lib/apt/lists/*` at the end deletes package-manager cache
files afterward - they're only needed during install, and leaving them in
the image just wastes space.

```dockerfile
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
COPY . .
```
This ordering is deliberate, not arbitrary. Docker builds images in
layers, and caches each layer. If you copied all your code first and
*then* installed dependencies, changing a single line of Python would
invalidate the cache and force a full dependency reinstall on every build.
By copying just the requirements file first and installing from it, that
expensive step only re-runs when your actual dependencies change - editing
`app/models.py` and rebuilding will reuse the cached dependency layer and
just be fast.

```dockerfile
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
```
By default, a container runs as `root`. If someone found a way to exploit
the running app, running as root would give them root access inside the
container. Creating a dedicated non-root `appuser` and switching to it
before running the app is a standard security practice - it's a small
addition but it's exactly the kind of detail that shows up well in a
security-conscious code review.

```dockerfile
EXPOSE 5000
```
Documents that the container listens on port 5000. This is metadata, not
enforcement - it doesn't actually open the port by itself (that happens in
`docker-compose.yml`'s `ports:` section), but it's good self-documentation.

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "run:app"]
```
The command that runs when the container starts. `gunicorn` is a
production-grade WSGI server - Flask's built-in `app.run()` is
single-threaded and explicitly documented as unsuitable for anything but
local development (it can't handle concurrent requests properly).
`--workers 3` runs three separate worker processes, so the app can serve
multiple requests at once. `run:app` tells gunicorn: import `run.py`, and
use the object called `app` inside it (that's `app = create_app()` in your
`run.py`).

---

## 5. `.dockerignore` - what NOT to copy into the image

Same idea as `.gitignore`, but for Docker builds. Without it, `COPY . .`
in the Dockerfile would copy everything in your project folder into the
image - including your local `venv/` folder (huge, and platform-specific -
a Windows venv wouldn't even work inside a Linux container), your `.env`
file (would bake your local secrets into the image - a real security
issue if that image ever got pushed somewhere), and your local SQLite
database file.

---

## 6. `docker-compose.yml` - running app + database together

Docker Compose lets you define multiple containers that work together as
one system, described in a single YAML file.

```yaml
services:
  db:
    image: postgres:16-alpine
```
Uses an official, pre-built Postgres image (version 16, `alpine` = a
minimal Linux base, smaller than the default). You don't need to write a
Dockerfile for Postgres - well-maintained official images already exist
for it.

```yaml
    environment:
      POSTGRES_USER: taskuser
      POSTGRES_PASSWORD: taskpass
      POSTGRES_DB: taskmanager
```
These environment variables are read by the Postgres image itself (that's
documented behavior of the official `postgres` image) - on first startup
it creates a database called `taskmanager` with a user `taskuser` who has
that password, ready to use.

```yaml
    volumes:
      - postgres_data:/var/lib/postgresql/data
```
Without this, every time you ran `docker compose down` and back up, your
database would start completely empty - containers are ephemeral by
default. A named volume (`postgres_data`) persists the actual database
files on your host machine, separate from the container's lifecycle - your
data survives container restarts.

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskuser -d taskmanager"]
      interval: 5s
      timeout: 5s
      retries: 5
```
`pg_isready` is a Postgres tool that checks if the database is actually
ready to accept connections (not just that the container has started -
Postgres takes a few seconds to initialize even after its process begins).
Compose runs this check every 5 seconds and considers the service
"healthy" once it succeeds.

```yaml
  app:
    build: .
```
Unlike `db`, which uses a pre-built image, `app` gets built from your own
`Dockerfile` in the current directory (`.`).

```yaml
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://taskuser:taskpass@db:5432/taskmanager
```
Note the hostname in that URL is `db`, not `localhost`. Inside a Compose
network, each service can reach the others by their service name as if it
were a hostname - Docker sets up internal DNS for this automatically. This
is also exactly why the config.py bug fix mattered: this variable is
genuinely set here, not empty, so this is the code path that gets
exercised for the first time today.

```yaml
    depends_on:
      db:
        condition: service_healthy
```
This is what actually uses that healthcheck. Without it, Compose only
guarantees container *start order*, not readiness - `app` could start and
try to connect to Postgres in the split-second before Postgres is actually
accepting connections, and crash. `condition: service_healthy` makes `app`
wait until `db`'s healthcheck passes before starting at all.

---

## 7. What was verified today (and what wasn't)

**Verified in this session:**
- Full test suite (15 tests) still passes against the updated config
- Python syntax of all changed files
- YAML syntax of `docker-compose.yml`

**Not yet verified - do this next, on your Windows machine with Docker
Desktop installed:**
- An actual `docker compose up --build` run
- Confirming the app can really talk to the Postgres container
- Confirming data persists across a `docker compose down` / `up` cycle

I don't have Docker available in the environment I built this in, so this
was built through careful manual review rather than a live test run - the
real first test happens on your machine. If anything breaks there, that's
expected to debug together, not a sign something's wrong with the
approach.
