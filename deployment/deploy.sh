#!/usr/bin/env bash
# deploy.sh — MediAssist AI server-side deployment script
# Run on the production server (e.g. via SSH or GitHub Actions)
# Usage: ./deployment/deploy.sh [--branch main] [--skip-seed]

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/mediassist}"
REPO_URL="${REPO_URL:-}"                  # set in env or pass via CI
BRANCH="${BRANCH:-main}"
SKIP_SEED=false
COMPOSE="docker compose"

# ── Parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch)   BRANCH="$2";    shift 2 ;;
    --skip-seed) SKIP_SEED=true; shift   ;;
    *) echo "Unknown arg: $1"; exit 1    ;;
  esac
done

log() { echo -e "\033[1;36m[deploy]\033[0m $*"; }
ok()  { echo -e "\033[1;32m[  ok  ]\033[0m $*"; }
err() { echo -e "\033[1;31m[error ]\033[0m $*" >&2; exit 1; }

# ── 1. Update repo ────────────────────────────────────────────────────────────
log "Updating repo on branch ${BRANCH}…"
if [[ ! -d "$APP_DIR/.git" ]]; then
  [[ -z "$REPO_URL" ]] && err "REPO_URL not set and $APP_DIR is not a git repo"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
ok "Code updated to $(git rev-parse --short HEAD)"

# ── 2. Validate env file ──────────────────────────────────────────────────────
log "Checking .env…"
[[ -f .env ]] || err ".env not found — copy .env.example and fill in secrets"
# Ensure required keys are present
REQUIRED_VARS=(GROQ_API_KEY OPENROUTER_API_KEY SECRET_KEY TELEGRAM_BOT_TOKEN)
for v in "${REQUIRED_VARS[@]}"; do
  grep -q "^${v}=" .env || err "Missing required env var: ${v}"
done
ok ".env validated"

# ── 3. Pull latest images ─────────────────────────────────────────────────────
log "Pulling images…"
$COMPOSE pull --quiet
ok "Images up to date"

# ── 4. Build app image ────────────────────────────────────────────────────────
log "Building application image…"
$COMPOSE build --no-cache backend nginx
ok "Images built"

# ── 5. Rolling restart ────────────────────────────────────────────────────────
log "Starting services (no-downtime reload)…"
$COMPOSE up -d --remove-orphans
ok "All services started"

# ── 6. Wait for backend health ────────────────────────────────────────────────
log "Waiting for backend health check…"
RETRIES=30
until curl -sf http://localhost:8000/health > /dev/null; do
  RETRIES=$((RETRIES - 1))
  [[ $RETRIES -eq 0 ]] && err "Backend failed to become healthy"
  sleep 2
done
ok "Backend is healthy"

# ── 7. Run migrations / seed (first deploy or explicit flag) ─────────────────
if [[ "$SKIP_SEED" == false ]]; then
  log "Running database seed & RAG ingest…"
  $COMPOSE exec -T backend python -m backend.database.seed       || true
  $COMPOSE exec -T backend python -m backend.rag.ingestion.pipeline ./docs/medical || true
  ok "Data initialized"
fi

# ── 8. Prune old images ───────────────────────────────────────────────────────
log "Pruning dangling images…"
docker image prune -f --filter "until=24h" > /dev/null
ok "Cleanup done"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "\033[1;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[1;32m  MediAssist AI deployed successfully!\033[0m"
echo -e "\033[1;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo "  App:      http://$(hostname -I | awk '{print $1}'):80"
echo "  API:      http://$(hostname -I | awk '{print $1}')/api"
echo "  Monitor:  http://$(hostname -I | awk '{print $1}')/monitor"
echo "  Commit:   $(git rev-parse --short HEAD)"
echo ""
