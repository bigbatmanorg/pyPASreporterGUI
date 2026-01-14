# Verification Guide

This document describes how to verify a pyPASreporterGUI installation.

## Quick Verification

### 1. CLI Doctor Command

```bash
pypasreportergui doctor
```

Expected output:
```
pyPASreporterGUI Doctor

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Component        ┃ Version    ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ pyPASreporterGUI │ 0.1.0      │
│ Apache Superset  │ 4.x.x      │
│ DuckDB           │ 0.10.x     │
│ Flask            │ 2.x.x      │
│ Python           │ 3.11.x     │
└──────────────────┴────────────┘

Sanity Checks:
✓ Superset app factory available
✓ DuckDB engine working
✓ Branding blueprint available

All checks passed! pyPASreporterGUI is ready to use.
```

### 2. Smoke Tests (with running server)

Start the server:
```bash
pypasreportergui run --port 8088
```

In another terminal:
```bash
python tools/verify.py --base-url http://127.0.0.1:8088
```

Expected output:
```
pyPASreporterGUI Smoke Tests
Base URL: http://127.0.0.1:8088
============================================================

📡 Basic Endpoints:
  ✓ Health: OK
  ✓ Login Page: OK

🎨 Branding Assets:
  ✓ Logo: OK
  ✓ Favicon: OK

🔌 pyPASreporterGUI API:
  ✓ Ping: OK

🔐 Authentication:
  ✓ Login: OK (got token)

📊 Authenticated Endpoints:
  ✓ Databases API: OK
  ✓ Charts API: OK

============================================================
✓ All smoke tests passed!
```

---

## Manual Verification Steps

### 1. Server Health

```bash
curl http://127.0.0.1:8088/health
# Expected: "OK"
```

### 2. Login Page

```bash
curl -s http://127.0.0.1:8088/login/ | grep -o "pyPASreporterGUI"
# Expected: "pyPASreporterGUI"
```

### 3. Branding Assets

```bash
# Logo
curl -I http://127.0.0.1:8088/pypasreportergui_static/logo-horiz.png
# Expected: HTTP/1.1 200 OK

# Favicon
curl -I http://127.0.0.1:8088/pypasreportergui_static/favicon.png
# Expected: HTTP/1.1 200 OK
```

### 4. API Authentication

```bash
# Get token
TOKEN=$(curl -s -X POST http://127.0.0.1:8088/api/v1/security/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","provider":"db"}' \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

# Test authenticated endpoint
curl -s http://127.0.0.1:8088/api/v1/database/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.count'
# Expected: A number (0 or more)
```

### 5. pyPASreporterGUI API

```bash
curl -s http://127.0.0.1:8088/api/pypasreportergui/ping | jq
# Expected:
# {
#   "status": "ok",
#   "app_name": "pyPASreporterGUI",
#   "version": "0.1.0",
#   "message": "pyPASreporterGUI is running!"
# }
```

---

## DuckDB Verification

### 1. Python Test

```python
from sqlalchemy import create_engine, text

# In-memory test
engine = create_engine("duckdb:///:memory:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 42 as answer"))
    print(result.fetchone())  # (42,)
```

### 2. File Database Test

```python
from sqlalchemy import create_engine, text
import tempfile
import os

# Create temp file
db_path = os.path.join(tempfile.gettempdir(), "test.duckdb")

engine = create_engine(f"duckdb:///{db_path}")
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE test (id INT, name VARCHAR)"))
    conn.execute(text("INSERT INTO test VALUES (1, 'hello')"))
    conn.commit()
    result = conn.execute(text("SELECT * FROM test"))
    print(result.fetchall())  # [(1, 'hello')]

print(f"Database created at: {db_path}")
```

---

## Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_core.py -v

# Run with coverage
pytest tests/ --cov=pypasreportergui --cov-report=html
```

---

## Browser Verification

1. Open http://127.0.0.1:8088
2. Verify:
   - [ ] Page title shows "pyPASreporterGUI"
   - [ ] Logo is not default Superset logo
   - [ ] Favicon is custom
   - [ ] Login form appears

3. Login with admin/admin
4. Verify:
   - [ ] Dashboard loads without errors
   - [ ] Navigation works
   - [ ] Data → Databases page loads

5. Add DuckDB connection:
   - [ ] Go to Data → Databases → + Database
   - [ ] Select "Other"
   - [ ] Enter: `duckdb:///:memory:`
   - [ ] Test Connection → Success
   - [ ] Save

---

## Verification Checklist

| Item | Command/Action | Expected Result |
|------|---------------|-----------------|
| CLI available | `pypasreportergui --version` | Version number |
| Doctor passes | `pypasreportergui doctor` | All checks green |
| Server starts | `pypasreportergui run` | No errors |
| Health check | `curl /health` | "OK" |
| Branding loads | Check browser | Custom logo |
| Login works | admin/admin | Dashboard |
| DuckDB works | Test connection | Success |
| API works | `/api/pypasreportergui/ping` | JSON response |
