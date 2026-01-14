# pyPASreporterGUI Installation Guide

This guide covers installing pyPASreporterGUI on Windows, Linux, and macOS.

## Prerequisites

Before installing pyPASreporterGUI, ensure you have:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Python 3.11 recommended |
| Node.js | 18+ | Required for building frontend |
| npm | 10+ | Comes with Node.js |
| Git | Any | Required for cloning Superset |

### Checking Prerequisites

```bash
python --version   # Should be 3.10+
node --version     # Should be 18+
npm --version      # Should be 10+
git --version      # Any version
```

---

## Quick Install (Linux/macOS)

```bash
# Clone the repository
git clone https://github.com/yourorg/pyPASreporterGUI.git
cd pyPASreporterGUI

# Run prerequisites script
bash tools/prereqs.sh

# Activate virtual environment
source .venv/bin/activate

# Build everything
python scripts/build_all.py

# Start the application
pypasreportergui run --port 8088
```

Open your browser to http://127.0.0.1:8088 and login with `admin`/`admin`.

---

## Quick Install (Windows)

```powershell
# Clone the repository
git clone https://github.com/yourorg/pyPASreporterGUI.git
cd pyPASreporterGUI

# Run prerequisites script (auto-installs Node.js via conda if needed)
.\tools\prereqs.ps1

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Build everything (frontend takes ~10-15 minutes)
python scripts\build_all.py

# Initialize database and admin user
pypasreportergui init

# Start the application
pypasreportergui run --port 8088
```

Open your browser to http://127.0.0.1:8088 and login with `admin`/`admin`.

> **Note:** If Node.js is not found, the prereqs script will attempt to install it via conda. If conda is not available, install Node.js 18+ manually from https://nodejs.org/ or via `conda install -c conda-forge nodejs=20`.

---

## Detailed Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourorg/pyPASreporterGUI.git
cd pyPASreporterGUI
```

### Step 2: Set Up Environment

**Option A: Using prereqs script (recommended)**

```bash
# Linux/macOS
bash tools/prereqs.sh

# Windows PowerShell
.\tools\prereqs.ps1 -UseConda:$false
```

**Option B: Manual setup**

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows

# Install base packages
pip install uv
uv pip install duckdb duckdb-engine typer rich requests pytest
```

### Step 3: Build Superset

```bash
# Pin to latest Superset release
python tools/pin_superset.py --latest-tag --write-version

# Build frontend and backend
python tools/build_superset.py
```

### Step 4: Build Wheels (Optional)

```bash
python tools/build_wheels.py
```

This creates wheel packages in `dist/wheels/` for offline installation.

### Step 5: Run the Application

```bash
pypasreportergui run --port 8088
```

---

## Installation from Wheel

If you have pre-built wheels:

```bash
# Create a fresh virtual environment
python -m venv myenv
source myenv/bin/activate  # Linux/macOS

# Install from wheel
pip install path/to/pyPASreporterGUI-*.whl

# Run
pypasreportergui run --port 8088
```

### Offline Installation

```bash
pip install --no-index --find-links dist/wheels pyPASreporterGUI
```

---

## Windows Executable

On Windows, you can build a standalone executable:

```powershell
# After completing the build
.\tools\build_exe.ps1

# Run the executable
.\dist\exe\pyPASreporterGUI\pyPASreporterGUI.exe run --port 8088
```

---

## Using Conda (Optional)

If you prefer Conda for environment management:

```bash
# Linux/macOS
USE_CONDA=1 CONDA_ENV=pypasreportergui bash tools/prereqs.sh

# Windows
.\tools\prereqs.ps1 -UseConda -CondaEnv pypasreportergui
```

---

## Post-Installation

### First Run

1. Start the application: `pypasreportergui run`
2. Open http://127.0.0.1:8088
3. Login with default credentials: `admin` / `admin`
4. **Important**: Change the admin password immediately

### Configuration

pyPASreporterGUI stores its configuration in `~/.pypasreportergui/`:

| File | Purpose |
|------|---------|
| `superset_config.py` | Main configuration |
| `superset.db` | SQLite metadata database |
| `.secret_key` | Flask secret key |

### Adding DuckDB Databases

```bash
# Via CLI
pypasreportergui add-duckdb --path /path/to/data.duckdb --name "My Data"

# Or manually in the UI:
# 1. Go to Data → Databases → + Database
# 2. Select "Other"
# 3. Enter: duckdb:///path/to/file.duckdb
```

---

## Troubleshooting

### Common Issues

**Node.js not found**
```bash
# Install Node.js 18+ from https://nodejs.org/
# Or use nvm: nvm install 18
```

**npm version too old**
```bash
npm install -g npm@latest
```

**Permission errors on Linux**
```bash
# Don't use sudo with pip/npm in venv
# If needed, fix permissions:
sudo chown -R $USER:$USER ~/.pypasreportergui
```

**Port already in use**
```bash
pypasreportergui run --port 9090  # Use different port
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

---

## Next Steps

- [BUILD.md](BUILD.md) - Understanding the build system
- [RELEASE.md](RELEASE.md) - Creating releases
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
