#!/usr/bin/env bash
# Production smoke test for AI WebScraper (bash — runs in GitHub Actions and
# in Git Bash on Windows; Claude runs it via the Bash tool, never paste into
# PowerShell).
#
# Usage:
#   bash scripts/smoke-prod.sh [BASE_URL]            # default https://scraper.cushlabs.ai
#
# Env:
#   EXPECTED_VERSION   git SHA that SHOULD be deployed (CI passes github.sha,
#                      deploy scripts pass the SHA they just shipped). Unset =
#                      skip the drift check.
#   DRIFT_IS_WARNING   "1" = a version mismatch is a ::warning:: (scheduled
#                      run; the VPS pull is a manual step). Unset = mismatch
#                      FAILS (deploy scripts: the thing you just shipped must
#                      be what is serving).
#
# Checks (any hard failure exits 1):
#   1. API health 200 with status=ok and a version field
#   2. Backend security headers present
#   3. Anonymous access to a data endpoint is refused (auth gate alive)
#   4. Frontend index.html 200 with CSP header and a built JS bundle that loads
#   5. Frontend meta app-version present
#   6. Version drift backend/frontend vs EXPECTED_VERSION
set -u

BASE="${1:-https://scraper.cushlabs.ai}"
API="$BASE/api/v1"
FAIL=0
WARN=0

say()  { printf '%s\n' "$*"; }
pass() { say "  PASS  $*"; }
fail() { say "  FAIL  $*"; FAIL=1; }
warn() { say "  WARN  $*"; WARN=1; if [ -n "${GITHUB_ACTIONS:-}" ]; then say "::warning::$*"; fi; }

fetch_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@"; }

say "Smoke test: $BASE"

# 1. API health ---------------------------------------------------------------
health_body="$(curl -s --max-time 20 "$API/health/" || true)"
health_code="$(fetch_code "$API/health/")"
if [ "$health_code" = "200" ] && printf '%s' "$health_body" | grep -q '"status":"ok"'; then
  pass "API health 200 ok"
else
  fail "API health -> HTTP $health_code body: ${health_body:0:200}"
fi
backend_version="$(printf '%s' "$health_body" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p')"
if [ -n "$backend_version" ]; then
  pass "backend version: $backend_version"
else
  fail "backend health payload has no version field (image predates 2026-10-18?)"
fi

# 2. Security headers ---------------------------------------------------------
hdrs="$(curl -s -D - -o /dev/null --max-time 20 "$API/health/" | tr -d '\r' | tr 'A-Z' 'a-z')"
for h in "x-content-type-options: nosniff" "x-frame-options: deny" "strict-transport-security:"; do
  if printf '%s' "$hdrs" | grep -q "^$h"; then pass "header $h"; else fail "missing header $h"; fi
done

# 3. Auth gate ----------------------------------------------------------------
anon="$(fetch_code "$API/crawls/")"
case "$anon" in
  401|403) pass "anonymous GET /crawls/ refused ($anon)" ;;
  *)       fail "anonymous GET /crawls/ returned $anon (expected 401/403)" ;;
esac

# 4. Frontend -----------------------------------------------------------------
TMPIDX="$(mktemp)"
index_code="$(curl -s -D "$TMPIDX.h" -o "$TMPIDX" -w '%{http_code}' --max-time 20 "$BASE/")"
if [ "$index_code" = "200" ]; then pass "frontend index 200"; else fail "frontend index -> $index_code"; fi
if tr -d '\r' < "$TMPIDX.h" | grep -qi '^content-security-policy:'; then pass "CSP header on frontend"; else fail "no CSP header on frontend"; fi
# index.html loads https://vitals.cushlabs.ai/tracker.js, which POSTs reports.
# Until 2026-10-19 connect-src omitted that origin, so the browser blocked every
# report and nobody noticed. The Caddyfile on the VPS owns this header.
if tr -d '\r' < "$TMPIDX.h" | grep -i '^content-security-policy:' | grep -q 'connect-src[^;]*https://vitals\.cushlabs\.ai'; then
  pass "CSP connect-src allows vitals.cushlabs.ai"
else
  fail "CSP connect-src blocks vitals.cushlabs.ai (Web Vitals reports are dropped)"
fi

bundle="$(grep -o 'src="/assets/[^"]*\.js"' "$TMPIDX" | head -1 | sed 's/src="\([^"]*\)"/\1/')"
if [ -n "$bundle" ]; then
  bcode="$(fetch_code "$BASE$bundle")"
  if [ "$bcode" = "200" ]; then pass "JS bundle loads ($bundle)"; else fail "JS bundle $bundle -> $bcode"; fi
else
  fail "no /assets/*.js bundle referenced by index.html"
fi

# 5. Frontend version ---------------------------------------------------------
frontend_version="$(sed -n 's/.*<meta name="app-version" content="\([^"]*\)".*/\1/p' "$TMPIDX" | head -1)"
if [ -n "$frontend_version" ] && [ "$frontend_version" != "%VITE_APP_VERSION%" ]; then
  pass "frontend version: $frontend_version"
else
  fail "frontend has no app-version meta (build predates 2026-10-18 or VITE_APP_VERSION unset at build)"
fi
rm -f "$TMPIDX" "$TMPIDX.h"

# 5b. Bot info page -----------------------------------------------------------
# The crawler's User-Agent points site owners here; a 404 would make us look
# like an anonymous scraper to anyone who checks.
bot_body="$(curl -s --max-time 20 "$BASE/bot.html" || true)"
if printf '%s' "$bot_body" | grep -q 'CushLabsBot'; then
  pass "bot.html explains CushLabsBot"
else
  fail "$BASE/bot.html missing or does not mention CushLabsBot"
fi

# 6. Drift --------------------------------------------------------------------
if [ -n "${EXPECTED_VERSION:-}" ]; then
  for pair in "backend:$backend_version" "frontend:$frontend_version"; do
    side="${pair%%:*}"; got="${pair#*:}"
    if [ "$got" = "$EXPECTED_VERSION" ]; then
      pass "$side is at expected $EXPECTED_VERSION"
    elif [ "${DRIFT_IS_WARNING:-}" = "1" ]; then
      warn "$side version $got != main $EXPECTED_VERSION — merged but not deployed. Run: bash scripts/deploy-$side.sh"
    else
      fail "$side version $got != expected $EXPECTED_VERSION"
    fi
  done
fi

say ""
if [ "$FAIL" = "1" ]; then say "SMOKE: FAILED"; exit 1; fi
if [ "$WARN" = "1" ]; then say "SMOKE: OK with warnings"; else say "SMOKE: OK"; fi
exit 0
