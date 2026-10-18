#!/usr/bin/env bash
# Build the frontend locally and publish it to the Hetzner VPS (bash — run
# from Git Bash or via Claude's Bash tool).
#
# The static build is served by Caddy from /home/deploy/apps/static/webscraper.
# VITE_APP_VERSION is baked into <meta name="app-version"> so the production
# smoke test can tell which commit is live.
#
# Usage:
#   bash scripts/deploy-frontend.sh           # builds current HEAD
set -euo pipefail

HOST="deploy@178.156.192.117"
DEST="~/apps/static/webscraper"

cd "$(dirname "$0")/../frontend"
SHA="$(git rev-parse HEAD)"
if [ -n "$(git status --porcelain -- . )" ]; then
  echo "WARNING: frontend has uncommitted changes; the deployed build will claim version $SHA but differ from it." >&2
fi

echo "Building frontend at $SHA ..."
rm -rf build
REACT_APP_API_URL=https://scraper.cushlabs.ai/api/v1 VITE_APP_VERSION="$SHA" npm run build

echo "Uploading to $HOST:$DEST ..."
# Clear stale hashed assets so the directory only holds this build.
ssh "$HOST" "mkdir -p $DEST && rm -rf $DEST/assets"
scp -q -r build/* "$HOST:$DEST/"

EXPECTED_VERSION="$SHA" bash ../scripts/smoke-prod.sh https://scraper.cushlabs.ai
