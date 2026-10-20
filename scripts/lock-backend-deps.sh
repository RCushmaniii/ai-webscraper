#!/usr/bin/env bash
# Regenerate backend/constraints.txt from a clean Linux resolution of
# backend/requirements.txt (bash — Claude runs it via the Bash tool; never
# paste into PowerShell).
#
# Usage:
#   bash scripts/lock-backend-deps.sh            # local docker
#   REMOTE=deploy@178.156.192.117 bash scripts/lock-backend-deps.sh   # no local docker: use the VPS's
#
# Resolution happens inside python:3.12-slim, the image the backend ships
# in, so platform markers (uvloop etc.) match production and not the
# developer's Windows machine. requirements.txt is piped over stdin so the
# remote variant needs nothing copied first. Only the header is written by
# this script; the pins are pip's own output.
set -euo pipefail

cd "$(dirname "$0")/.."
REQ=backend/requirements.txt
OUT=backend/constraints.txt
RUN="docker run --rm -i python:3.12-slim sh -c 'cat > /tmp/req.txt && pip install -q --no-cache-dir --disable-pip-version-check -r /tmp/req.txt >/dev/null && pip freeze --disable-pip-version-check'"

if [ -n "${REMOTE:-}" ]; then
  pins="$(ssh "$REMOTE" "$RUN" < "$REQ")"
elif command -v docker >/dev/null 2>&1; then
  pins="$(eval "$RUN" < "$REQ")"
else
  echo "docker not found locally; run with REMOTE=deploy@178.156.192.117" >&2
  exit 1
fi

today="$(date -u +%Y-%m-%d)"
{
  cat <<EOF
# Pinned transitive versions for the backend image. Used as
#   pip install -r requirements.txt -c constraints.txt
# by backend/Dockerfile and .github/workflows/ci.yml.
#
# Why: requirements.txt leaves most ranges open, so every image build used to
# re-resolve the whole tree. On 2026-10-19 production ran 45 packages newer
# than any developer machine (starlette 0.52 -> 1.9, anyio, h11, httpx ...)
# and a production-only failure could not be reproduced locally until the
# container's exact set was rebuilt by hand.
#
# A constraint only applies to packages pip is already going to install; it
# never adds one. Linux-only entries (uvloop) are ignored on Windows.
#
# Regenerate (Linux resolution, matches the image):
#   bash scripts/lock-backend-deps.sh
# Direct dependencies and their minimum versions stay in requirements.txt;
# bump there first, then regenerate this file in the same PR.
#
# Generated $today in python:3.12-slim by scripts/lock-backend-deps.sh.
EOF
  printf '%s\n' "$pins" | grep '==' | sort -f
} > "$OUT"
echo "wrote $OUT ($(grep -c '==' "$OUT") pins)"
