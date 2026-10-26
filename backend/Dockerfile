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

# Unprivileged runtime user (uid 1000 matches the `deploy` user on the Hetzner
# box). The only runtime write path is STORAGE_DIR (/app/storage), which in
# production is the `webscraper-storage` volume. That volume must be owned by
# uid 1000: it was chowned on the box on 2026-10-26, and a fresh host needs
#   docker run --rm -v cushlabs-prod-server_webscraper-storage:/d alpine chown -R 1000:1000 /d
# before the first start, or init_db's create_storage_directories() fails.
RUN useradd --create-home --uid 1000 --user-group --shell /usr/sbin/nologin app

# Copy requirements first for better layer caching.
# constraints.txt pins every transitive package to the versions the test
# suite ran against. Without it each image build re-resolved the open
# ranges in requirements.txt (2026-10-19: 45 packages newer than any
# developer machine, starlette 0.52 -> 1.9). Regenerate with
# scripts/lock-backend-deps.sh.
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

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

# When STORAGE_DIR is not a mounted volume (plain `docker run`), the app must
# still be able to create it under /app.
RUN mkdir -p /app/storage && chown app:app /app/storage

USER app

EXPOSE 10000

# Shell form so $PORT is expanded (compose sets PORT=10000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
