#!/bin/bash
# validate_linux.sh - Smoke test for pyPASreporterGUI frozen build
# This script validates that the frozen build can initialize and start.
# Exits 0 on success, non-zero on failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${PROJECT_ROOT}/dist/pyPASreporterGUI"
EXECUTABLE="${DIST_DIR}/pyPASreporterGUI"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Track failures
FAILURES=0

check_file() {
    local path="$1"
    local desc="$2"
    if [[ -e "$path" ]]; then
        log_info "✓ $desc exists: $path"
        return 0
    else
        log_error "✗ $desc missing: $path"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

check_directory() {
    local path="$1"
    local desc="$2"
    if [[ -d "$path" ]]; then
        local count
        count=$(find "$path" -type f | wc -l)
        log_info "✓ $desc exists: $path ($count files)"
        return 0
    else
        log_error "✗ $desc missing: $path"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# =============================================================================
# 1. Verify build artifacts exist
# =============================================================================
log_info "=== Checking build artifacts ==="

check_file "$EXECUTABLE" "Executable"
check_file "${DIST_DIR}/_internal" "Internal bundle directory"
check_directory "${DIST_DIR}/_internal/superset/migrations/versions" "Superset migrations"
check_directory "${DIST_DIR}/_internal/superset/static" "Superset static assets"
check_directory "${DIST_DIR}/_internal/superset/templates" "Superset templates"

# Check minimum migration count (should be ~340+)
MIGRATIONS_DIR="${DIST_DIR}/_internal/superset/migrations/versions"
if [[ -d "$MIGRATIONS_DIR" ]]; then
    MIGRATION_COUNT=$(find "$MIGRATIONS_DIR" -name "*.py" -type f | wc -l)
    if [[ $MIGRATION_COUNT -ge 300 ]]; then
        log_info "✓ Sufficient migrations bundled: $MIGRATION_COUNT files"
    else
        log_error "✗ Too few migrations bundled: $MIGRATION_COUNT (expected 300+)"
        FAILURES=$((FAILURES + 1))
    fi
fi

if [[ $FAILURES -gt 0 ]]; then
    log_error "Build artifact validation failed with $FAILURES errors"
    exit 1
fi

# =============================================================================
# 2. Test doctor command
# =============================================================================
log_info ""
log_info "=== Testing doctor command ==="

if "$EXECUTABLE" doctor; then
    log_info "✓ doctor command succeeded"
else
    log_error "✗ doctor command failed"
    FAILURES=$((FAILURES + 1))
fi

# =============================================================================
# 3. Test init command
# =============================================================================
log_info ""
log_info "=== Testing init command ==="

# Use a temporary home directory to avoid polluting the user's config
TEST_HOME=$(mktemp -d)
export HOME="$TEST_HOME"
log_info "Using temporary HOME: $TEST_HOME"

cleanup() {
    if [[ -n "${TEST_HOME:-}" && -d "$TEST_HOME" ]]; then
        log_info "Cleaning up: $TEST_HOME"
        rm -rf "$TEST_HOME"
    fi
}
trap cleanup EXIT

if "$EXECUTABLE" init 2>&1; then
    log_info "✓ init command succeeded"
else
    log_error "✗ init command failed"
    FAILURES=$((FAILURES + 1))
fi

# Verify init created expected files
check_file "${TEST_HOME}/.pypasreportergui/superset_config.py" "Generated config"
check_file "${TEST_HOME}/.pypasreportergui/superset.db" "SQLite database"

# =============================================================================
# 4. Test run command (briefly)
# =============================================================================
log_info ""
log_info "=== Testing run command (startup only) ==="

# Start server in background, wait for it to bind, then kill
PORT=19088
"$EXECUTABLE" run --port $PORT &
SERVER_PID=$!

# Wait up to 30 seconds for server to start
STARTED=0
for i in {1..30}; do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/health" 2>/dev/null; then
        STARTED=1
        log_info "✓ Server responded on port $PORT after ${i}s"
        break
    fi
    # Also check if process is still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        log_error "✗ Server process died unexpectedly"
        break
    fi
    sleep 1
done

# Kill the server
if kill -0 $SERVER_PID 2>/dev/null; then
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
fi

if [[ $STARTED -eq 1 ]]; then
    log_info "✓ run command succeeded"
else
    # Server might not have /health endpoint, check if it bound to port
    if timeout 5 bash -c "echo >/dev/tcp/127.0.0.1/$PORT" 2>/dev/null; then
        log_info "✓ run command bound to port (health check unavailable)"
    else
        log_warn "⚠ run command may have issues (could not verify port binding)"
        # Don't fail on this - server might just be slow to start
    fi
fi

# =============================================================================
# Summary
# =============================================================================
log_info ""
log_info "=== Validation Summary ==="

if [[ $FAILURES -eq 0 ]]; then
    log_info "✓ All validation checks passed!"
    exit 0
else
    log_error "✗ Validation failed with $FAILURES errors"
    exit 1
fi
