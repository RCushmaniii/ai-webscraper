#!/usr/bin/env bash
# Deploy the backend image to the Hetzner VPS (bash — run from Git Bash or via
# Claude's Bash tool; the ssh payload runs on Linux).
#
# Flow (see CLAUDE.md "Deploy Backend"): merge to main → CI builds the image and
# pushes ghcr.io/rcushmaniii/ai-webscraper:latest → this script pulls it on the
# box, recreates the container, waits for health, and runs the production smoke
# test with EXPECTED_VERSION = the SHA that should now be serving.
#
# Usage:
#   bash scripts/deploy-backend.sh            # expects origin/main HEAD to be deployed
#   bash scripts/deploy-backend.sh <sha>      # expect a specific SHA
set -euo pipefail

HOST="deploy@178.156.192.117"
COMPOSE_DIR="~/apps/cushlabs-prod-server"
SERVICE="webscraper"

cd "$(dirname "$0")/.."
git fetch -q origin main
# Accept a short SHA too: the GitHub API only matches full ones, and a 7-char
# argument made this script abort with "no run found" on 2026-10-19.
EXPECTED="$(git rev-parse --verify "${1:-origin/main}^{commit}")"

echo "Expecting backend version: $EXPECTED"

# Make sure CI has actually published the image for this SHA before pulling.
# Actions can take a minute or two to schedule the run after a merge, so poll
# instead of aborting on the first miss, and look past the newest run in case
# another push landed on main in between.
run_id=""
for attempt in $(seq 1 12); do
  run_id="$(gh run list --workflow build-image.yml --branch main --limit 10 --json databaseId,headSha \
    --jq "map(select(.headSha==\"$EXPECTED\")) | .[0].databaseId // empty")"
  [ -n "$run_id" ] && break
  echo "No 'Build & push image' run for $EXPECTED yet (attempt $attempt/12); waiting 15s ..."
  sleep 15
done
if [ -z "$run_id" ]; then
  echo "No 'Build & push image' run found for $EXPECTED after 3 minutes — did the push only touch docs? Aborting." >&2
  exit 1
fi
echo "Waiting for image build run $run_id ..."
gh run watch "$run_id" --exit-status >/dev/null

echo "Pulling + recreating $SERVICE on the VPS ..."
ssh "$HOST" "cd $COMPOSE_DIR && docker compose pull $SERVICE && docker compose up -d $SERVICE"

echo "Waiting for container health ..."
for i in $(seq 1 30); do
  state="$(ssh "$HOST" "docker inspect --format '{{.State.Health.Status}}' $SERVICE" 2>/dev/null || echo unknown)"
  if [ "$state" = "healthy" ]; then break; fi
  sleep 5
done
echo "Container health: $state"
[ "$state" = "healthy" ] || { ssh "$HOST" "docker logs --tail 50 $SERVICE"; exit 1; }

# Reclaim the old 4 GB image layers; keeps the 75 GB disk honest.
ssh "$HOST" "docker image prune -f >/dev/null" || true

EXPECTED_VERSION="$EXPECTED" bash scripts/smoke-prod.sh https://scraper.cushlabs.ai
