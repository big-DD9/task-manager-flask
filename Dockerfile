# Slim base image - much smaller than the full python:3.12 image, still
# has everything we need since we're not compiling anything exotic.
FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffering stdout - the
# buffering one matters because our logging setup writes to stdout, and
# we want those logs to show up immediately (e.g. in `docker logs`),
# not sit in a buffer.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System packages needed to build psycopg2-binary and give it a working
# Postgres client library at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first, before the rest of the code. Docker caches each
# layer - if only your app code changes (not dependencies), this layer is
# reused instead of reinstalling every package from scratch on every build.
COPY requirements.txt requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Now copy the actual application code
COPY . .

# Run as a non-root user - if the app is ever compromised, the attacker
# doesn't get root inside the container. Basic container security hygiene.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# gunicorn instead of Flask's built-in dev server - the dev server is
# single-threaded and explicitly not meant for anything but local testing.
# "run:app" means: import run.py and use the `app` object defined inside it.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "run:app"]
