# pyPASreporterGUI Troubleshooting Guide

This document covers common issues and their solutions.

---

## Installation Issues

### Python Version

**Problem:** `Python 3.10+ required`

**Solution:**
```bash
# Check version
python --version

# Install Python 3.11 (recommended)
# Linux: apt install python3.11
# macOS: brew install python@3.11
# Windows: Download from python.org
```

### Node.js/npm

**Problem:** `node not found` or `npm version too old`

**Solution:**
```bash
# Option 1: Install via conda (recommended for Windows)
conda install -y -c conda-forge nodejs=20

# Option 2: Install Node.js 18+ from https://nodejs.org/

# Option 3: Use nvm (Linux/macOS)
nvm install 20
nvm use 20

# Upgrade npm (if needed)
npm install -g npm@latest
```

### Virtual Environment

**Problem:** `.venv not found`

**Solution:**
```bash
# Run prerequisites script
bash tools/prereqs.sh  # Linux/macOS
.\tools\prereqs.ps1    # Windows

# Or manually create venv
python -m venv .venv
source .venv/bin/activate
pip install uv
```

---

## Build Issues

### Frontend Build Fails

**Problem:** `npm ci` or `npm run build` fails

**Solutions:**

1. **Clear cache and retry:**
   ```bash
   cd superset-src/superset-frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

2. **Check Node.js version:**
   ```bash
   node --version  # Should be 18+
   ```

3. **Memory issues (large build):**
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm run build
   ```

### Wheel Build Fails

**Problem:** `No wheel found for apache-superset`

**Solutions:**

1. **Ensure frontend is built:**
   ```bash
   python tools/build_superset.py
   ```

2. **Clean build artifacts:**
   ```bash
   rm -rf superset-src/build superset-src/*.egg-info
   python tools/build_wheels.py
   ```

3. **Check pyproject.toml exists:**
   ```bash
   ls superset-src/pyproject.toml
   ```

### PyInstaller Fails (Windows)

**Problem:** Executable won't build or run

**Solutions:**

1. **Missing dependencies:**
   - Check `build_exe.spec` for hidden imports
   - Add missing modules to `hiddenimports` list

2. **Static assets missing:**
   - Verify `datas` in spec file includes all required files
   - Check Superset static folder exists

3. **Antivirus interference:**
   - Temporarily disable antivirus
   - Add build folder to exclusions

---

## Runtime Issues

### Server Won't Start

**Problem:** `superset: command not found`

**Solution:**
```bash
# Linux/macOS: Ensure venv is activated
source .venv/bin/activate

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Verify superset is installed
which superset      # Linux/macOS
Get-Command superset  # Windows

# Alternative: Run via Python module directly
python -m superset.cli.main run -h 127.0.0.1 -p 8088
```

**Problem:** `SECRET_KEY must be set`

**Solution:**
```bash
# Run init to generate config
pypasreportergui init

# Or set manually
export SUPERSET_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### Database Errors

**Problem:** `OperationalError: no such table`

**Solution:**
```bash
# Run database migrations
pypasreportergui init
# Or manually:
superset db upgrade
superset init
```

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:**
- Only run one instance at a time
- Check for zombie processes: `ps aux | grep superset`
- Delete lock file if exists

### Port Already in Use

**Problem:** `Address already in use`

**Solutions:**

1. **Use different port:**
   ```bash
   pypasreportergui run --port 9090
   ```

2. **Find and kill process:**
   ```bash
   # Linux/macOS
   lsof -i :8088
   kill <PID>
   
   # Windows
   netstat -ano | findstr :8088
   taskkill /PID <PID> /F
   ```

---

## UI Issues

### Blank Page After Login

**Problem:** White/blank page after successful login

**Solutions:**

1. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
   - Clear cookies for localhost

2. **Check static assets:**
   ```bash
   ls superset-src/superset/static/assets/
   ```

3. **Rebuild frontend:**
   ```bash
   python tools/build_superset.py
   ```

### Branding Not Showing

**Problem:** Default Superset logo appears instead of pyPASreporterGUI

**Solutions:**

1. **Verify branding files exist:**
   ```bash
   ls src/pypasreportergui/branding/static/
   # Should show: logo-horiz.png, favicon.png
   ```

2. **Check config:**
   ```bash
   grep APP_NAME ~/.pypasreportergui/superset_config.py
   # Should show: APP_NAME = "pyPASreporterGUI"
   ```

3. **Regenerate config:**
   ```bash
   pypasreportergui init --force
   ```

---

## DuckDB Issues

### Can't Connect to DuckDB

**Problem:** `Connection failed` when adding DuckDB database

**Solutions:**

1. **Check URI format:**
   ```
   # Correct format:
   duckdb:///absolute/path/to/file.duckdb
   
   # Wrong formats:
   duckdb://path/to/file.duckdb  (missing slash)
   duckdb://../relative/path.duckdb  (relative path)
   ```

2. **Verify file permissions:**
   ```bash
   ls -la /path/to/file.duckdb
   # Should be readable/writable by your user
   ```

3. **Test connection:**
   ```bash
   python -c "
   from sqlalchemy import create_engine
   engine = create_engine('duckdb:///path/to/file.duckdb')
   with engine.connect() as conn:
       print(conn.execute('SELECT 1').fetchone())
   "
   ```

### DuckDB Package Missing

**Problem:** `ModuleNotFoundError: No module named 'duckdb'`

**Solution:**
```bash
pip install duckdb duckdb-engine
```

---

## Windows-Specific Issues

### python-geohash Build Failure

**Problem:** `error: Microsoft Visual C++ 14.0 or greater is required`

This occurs because `python-geohash` has no pre-built wheel for Windows.

**Solutions:**

1. **Install via conda (recommended):**
   ```powershell
   conda install -y -c conda-forge python-geohash
   ```

2. **Install Microsoft Visual C++ Build Tools:**
   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++" workload
   - Retry the build

### Node.js/npm Commands Fail in Build

**Problem:** `npm` or `node` commands fail with "not found" even though they work in terminal

On Windows, `npm` and `node` are `.cmd` wrapper scripts that require `shell=True` in subprocess calls.

**Solution:** This is fixed in the build scripts. If you encounter this with custom scripts, use:
```python
subprocess.run(["npm", "..."], shell=(os.name == "nt"))
```

### Path Too Long

**Problem:** Build fails with path length errors

**Solution:**
```powershell
# Enable long paths in Windows
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or clone to shorter path (e.g., C:\dev\pas)
```

### PowerShell Execution Policy

**Problem:** `Scripts disabled on this system`

**Solution:**
```powershell
# For current session only:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Or run script with bypass:
powershell -ExecutionPolicy Bypass -File .\tools\prereqs.ps1
```

### Line Ending Issues

**Problem:** Scripts fail with `\r` errors

**Solution:**
```bash
# Configure Git to handle line endings
git config --global core.autocrlf true

# Or convert files
dos2unix tools/*.sh
```

---

## Frozen Build (PyInstaller) Issues

### Migrations Not Found

**Problem:** `Path doesn't exist: .../superset/extensions/../migrations`

This occurs when PyInstaller's bundled paths don't match what Superset expects.

**Solution:**
This is fixed in the latest version. If you encounter it with a custom build:
1. Ensure `build_exe.spec` includes the migrations directory:
   ```python
   datas = [(str(SUPERSET_DIR / "migrations"), "superset/migrations"), ...]
   ```
2. Verify migrations are bundled: check `dist/pyPASreporterGUI/_internal/superset/migrations/versions/`

### ModuleNotFoundError in Frozen Build

**Problem:** `ModuleNotFoundError: No module named 'X'` when running the frozen executable

Common missing modules and fixes:

| Module | Add to hiddenimports |
|--------|---------------------|
| `logging.config` | `"logging", "logging.config", "logging.handlers"` |
| `isodate` | `"isodate"` |
| `sqlalchemy_utils` | `"sqlalchemy_utils"` |
| `flask_appbuilder.models.mixins` | `"flask_appbuilder", "flask_appbuilder.models", "flask_appbuilder.models.mixins"` |

**Solution:**
Add the missing module to `hiddenimports` in `tools/build_exe.spec` and rebuild.

### Flask-Limiter Errors

**Problem:** `AttributeError: 'NoneType' object has no attribute '__module__'`

This occurs when Flask's `create_app()` is called multiple times in frozen mode.

**Solution:**
This is fixed in the latest version. The runtime now caches the Flask app globally to prevent re-initialization issues.

### Shebang/PATH Issues (Linux/Snap)

**Problem:** Executable tries to use wrong Python interpreter (e.g., Snap's Python)

**Symptoms:**
- Errors mentioning `/snap/...` paths
- `env: python: No such file or directory`

**Solution:**
1. The frozen executable should not use shebangs at all - it's self-contained
2. If building from source, ensure you're using a clean virtualenv:
   ```bash
   python -m venv .venv-build
   source .venv-build/bin/activate
   pip install pyinstaller
   pip install dist/wheels/*.whl
   pyinstaller tools/build_exe.spec
   ```

### Doctor Command for Frozen Builds

Run the doctor command to check frozen build status:
```bash
./pyPASreporterGUI doctor
```

This will show:
- Execution mode (Frozen vs Normal)
- `sys._MEIPASS` location
- Bundled asset verification
- Environment variables

### Validating Frozen Builds

Use the validation script to smoke test builds:
```bash
bash scripts/validate_linux.sh
```

This verifies:
- Bundled migrations exist (300+ files expected)
- Static assets and templates bundled
- `doctor` command works
- `init` command completes successfully
- `run` command starts and binds to port

---

## Getting Help

### Collecting Debug Info

When reporting issues, include:

```bash
# Version info
pypasreportergui doctor

# System info
python --version
node --version
npm --version
uname -a  # or systeminfo on Windows

# Error logs
cat logs/superset.log | tail -100
```

### Log Locations

| Log | Location |
|-----|----------|
| Application | `~/.pypasreportergui/logs/superset.log` |
| Build | Console output / `logs/` directory |
| PyInstaller | `build/pyinstaller/warn-*.txt` |

### Reporting Bugs

1. Check existing issues first
2. Include version info from `pypasreportergui doctor`
3. Include relevant log excerpts
4. Describe steps to reproduce
