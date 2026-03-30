#!/usr/bin/env bash
# validate-submission.sh — Support Triage OpenEnv pre-submission validator
#
# Usage:
#   ./scripts/validate-submission.sh <space_url> [repo_dir]
#
# Example:
#   ./scripts/validate-submission.sh https://your-space.hf.space .

set -uo pipefail

PING_URL="${1:-}"
REPO_DIR="${2:-.}"
PASS=0
FAIL=0

# Colors
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BOLD='\033[1m'; NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BOLD='' NC=''
fi

pass() { echo -e "${GREEN}✓${NC} $1"; ((PASS++)); }
fail() { echo -e "${RED}✗${NC} $1"; ((FAIL++)); }
info() { echo -e "${YELLOW}→${NC} $1"; }

echo -e "\n${BOLD}Support Triage OpenEnv — Pre-Submission Validator${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. File structure ────────────────────────────────────────────────────────
info "Checking required files..."

for f in \
  "openenv.yaml" \
  "Dockerfile" \
  "requirements.txt" \
  "inference.py" \
  "README.md" \
  "app/main.py" \
  "app/models.py" \
  "app/environment.py" \
  "tasks/task_definitions.py" \
  "tasks/graders.py"
do
  if [ -f "${REPO_DIR}/${f}" ]; then
    pass "File exists: ${f}"
  else
    fail "Missing required file: ${f}"
  fi
done

# ── 2. openenv.yaml validation ───────────────────────────────────────────────
info "Validating openenv.yaml..."
if python3 - <<'EOF'
import yaml, sys
with open("openenv.yaml") as f:
    doc = yaml.safe_load(f)
required = ["name","version","description","tasks","endpoints"]
missing = [k for k in required if k not in doc]
if missing:
    print("Missing keys:", missing); sys.exit(1)
tasks = doc.get("tasks", [])
if len(tasks) < 3:
    print(f"Need ≥3 tasks, found {len(tasks)}"); sys.exit(1)
for t in tasks:
    for k in ["id","name","difficulty","passing_score"]:
        if k not in t:
            print(f"Task missing key: {k}"); sys.exit(1)
print("openenv.yaml OK")
EOF
then
  pass "openenv.yaml valid (3+ tasks, required keys present)"
else
  fail "openenv.yaml validation failed"
fi

# ── 3. Python syntax check ───────────────────────────────────────────────────
info "Checking Python syntax..."
find "${REPO_DIR}" -name "*.py" -not -path "*/__pycache__/*" | while read -r pyfile; do
  if python3 -m py_compile "${pyfile}" 2>/dev/null; then
    pass "Syntax OK: ${pyfile#${REPO_DIR}/}"
  else
    fail "Syntax error: ${pyfile#${REPO_DIR}/}"
  fi
done

# ── 4. Inference script checks ───────────────────────────────────────────────
info "Checking inference.py..."
if grep -q "OpenAI" "${REPO_DIR}/inference.py"; then
  pass "inference.py uses OpenAI client"
else
  fail "inference.py must use OpenAI client"
fi

for var in "API_BASE_URL" "MODEL_NAME" "HF_TOKEN"; do
  if grep -q "${var}" "${REPO_DIR}/inference.py"; then
    pass "inference.py references \$${var}"
  else
    fail "inference.py missing env var: ${var}"
  fi
done

# ── 5. Dockerfile checks ─────────────────────────────────────────────────────
info "Checking Dockerfile..."
if grep -q "EXPOSE 7860" "${REPO_DIR}/Dockerfile"; then
  pass "Dockerfile exposes port 7860"
else
  fail "Dockerfile must EXPOSE 7860"
fi
if grep -q "HEALTHCHECK" "${REPO_DIR}/Dockerfile"; then
  pass "Dockerfile has HEALTHCHECK"
else
  fail "Dockerfile missing HEALTHCHECK"
fi

# ── 6. HF Space ping ─────────────────────────────────────────────────────────
if [ -n "${PING_URL}" ]; then
  info "Pinging HF Space at ${PING_URL}/health ..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${PING_URL}/health" --max-time 15 || echo "000")
  if [ "${HTTP_CODE}" = "200" ]; then
    pass "HF Space health check returned 200"
  else
    fail "HF Space health check returned ${HTTP_CODE} (expected 200)"
  fi

  # Test reset()
  info "Testing reset() endpoint..."
  RESET_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${PING_URL}/reset" \
    -H "Content-Type: application/json" \
    -d '{"task_id":"task_easy"}' --max-time 15 || echo "000")
  if [ "${RESET_CODE}" = "200" ]; then
    pass "reset() returned 200"
  else
    fail "reset() returned ${RESET_CODE}"
  fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"

if [ "${FAIL}" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}✅  All checks passed — ready to submit!${NC}"
  exit 0
else
  echo -e "${RED}${BOLD}❌  Fix failures before submitting.${NC}"
  exit 1
fi
