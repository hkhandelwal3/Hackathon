# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Avoid Python writing .pyc/.pyo files and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

# Copy lock files first for caching
COPY pyproject.toml poetry.lock* ./

# Install all deps inside container
RUN poetry install --no-interaction --no-ansi

# Copy app source
COPY . .

# Run your app with poetry
# Replace "app:app" with your entrypoint (Flask=app:app | FastAPI=main:app)
CMD ["poetry", "run", "gunicorn", "-b", "0.0.0.0:${PORT}", "final:app"]
