# Production image for the FastAPI backend.
#
# Base: python:3.12-slim. Until 2026-10-18 this was the ~4 GB Microsoft
# Playwright image, a leftover from before JS rendering moved to Firecrawl
# (commit c66fccf). Nothing in app/ imports playwright or selenium any more,
# so the browser bundle was 3.5 GB of dead weight on every CI build and VPS
# pull. If JS rendering ever returns to in-process Playwright, switch the base
# back AND pin `playwright==` to the image's version — a pip-installed
# Playwright newer than the baked-in browsers fails at runtime with
# "Executable doesn't exist".
FROM python:3.12-slim

WORKDIR /app

# curl: the compose healthcheck in cushlabs-prod-server runs
# `curl -f http://localhost:10000/api/v1/health/`. Without it the container
# reports "unhealthy" forever even though the app is fine.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Stamp the build with the git SHA so GET /api/v1/health/ can report which
# commit is running. CI passes --build-arg GIT_SHA=${{ github.sha }}; the
# production smoke test compares this to main to detect "merged but not
# deployed" drift.
ARG GIT_SHA=unknown
ENV APP_VERSION=${GIT_SHA}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

# Shell form so $PORT is expanded (compose sets PORT=10000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
