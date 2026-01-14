# pyPASreporterGUI Build System

This document describes the build system architecture and how each component works.

## Repository Structure

```
pyPASreporterGUI/
├── pyproject.toml              # Package metadata and dependencies
├── README.md                   # Quick start guide
├── LICENSE                     # Apache 2.0 license
│
├── src/pypasreportergui/       # Main Python package
│   ├── __init__.py             # Version and app name
│   ├── cli.py                  # Typer CLI entrypoint
│   ├── runtime.py              # Environment setup helpers
│   └── branding/               # Custom branding
│       ├── __init__.py
│       ├── blueprint.py        # Flask blueprint
│       └── static/             # Logo, favicon assets
│
├── tools/                      # Build and utility scripts
│   ├── prereqs.sh              # Linux/macOS prerequisites
│   ├── prereqs.ps1             # Windows prerequisites
│   ├── pin_superset.py         # Clone/pin Superset
│   ├── build_superset.py       # Build frontend/backend
│   ├── build_wheels.py         # Build wheel packages
│   ├── build_exe.ps1           # Windows executable
│   ├── build_exe.spec          # PyInstaller config
│   ├── run_app.py              # Low-level runner
│   ├── detect_support.py       # Feature detection
│   └── verify.py               # Smoke tests
│
├── scripts/                    # Orchestration scripts
│   ├── build_all.py            # Full build pipeline
│   └── test_all.py             # Test runner
│
├── docs/                       # Documentation
│   ├── INSTALL.md
│   ├── BUILD.md                # This file
│   ├── RELEASE.md
│   ├── TROUBLESHOOTING.md
│   └── VERSION_MATRIX.md       # Auto-generated
│
├── tests/                      # Unit tests
│   └── test_core.py
│
├── superset-src/               # Pinned Superset checkout (gitignored)
│
└── dist/                       # Build outputs (gitignored)
    ├── wheels/                 # Wheel packages
    └── exe/                    # Windows executable
```

---

## Build Pipeline

The build process follows these stages:

```
┌─────────────────┐
│   Prerequisites │  tools/prereqs.sh
│   (Python, npm) │  tools/prereqs.ps1
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pin Superset   │  tools/pin_superset.py
│  (clone/update) │  Creates: superset-src/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Superset  │  tools/build_superset.py
│ (frontend+back) │  npm ci, npm run build
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Wheels   │  tools/build_wheels.py
│ (superset+app)  │  Creates: dist/wheels/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Build Exe     │  tools/build_exe.ps1
│  (Windows only) │  Creates: dist/exe/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Verify       │  tools/verify.py
│  (smoke tests)  │  tests/test_core.py
└─────────────────┘
```

---

## Tool Reference

### `tools/prereqs.sh` / `tools/prereqs.ps1`

Sets up the development environment:
- Creates `.venv` virtual environment
- Installs `uv` package manager
- Installs DuckDB, Typer, Rich, and other dependencies
- Ensures Node.js and npm are available

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `USE_CONDA` | `0` | Use Conda environment |
| `CONDA_ENV` | `pypasreportergui` | Conda environment name |
| `PY_VERSION` | `3.11` | Python version |
| `PYTHON_BIN` | auto | Python interpreter path |

---

### `tools/pin_superset.py`

Clones or updates the Superset repository and pins to a specific version.

**Options:**
| Option | Description |
|--------|-------------|
| `--latest-tag` | Pin to latest release tag (e.g., 4.0.0) |
| `--sha <SHA>` | Pin to specific commit |
| `--branch <name>` | Pin to branch tip |
| `--write-version` | Write VERSION_MATRIX.json |

**Examples:**
```bash
# Pin to latest stable release
python tools/pin_superset.py --latest-tag --write-version

# Pin to specific commit
python tools/pin_superset.py --sha abc123def --write-version

# Pin to master branch tip
python tools/pin_superset.py --branch master --write-version
```

---

### `tools/build_superset.py`

Builds Superset frontend and installs backend.

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-frontend` | Don't build frontend (use existing) |
| `--skip-backend` | Don't install backend |
| `--skip-packages` | Don't install DuckDB, etc. |
| `--verify-sha` | Verify checkout matches VERSION_MATRIX |

**What it does:**
1. Runs `npm ci` in `superset-frontend/`
2. Runs `npm run build` to generate static assets
3. Installs Superset in editable mode
4. Installs DuckDB and other packages

---

### `tools/build_wheels.py`

Builds wheel packages for distribution.

**Options:**
| Option | Description |
|--------|-------------|
| `--output <dir>` | Output directory (default: `dist/wheels`) |
| `--superset-only` | Build only Superset wheel |
| `--app-only` | Build only pyPASreporterGUI wheel |

**Output:**
- `dist/wheels/apache_superset-*.whl`
- `dist/wheels/pyPASreporterGUI-*.whl`

---

### `tools/build_exe.ps1` (Windows)

Creates a standalone Windows executable using PyInstaller.

**Requirements:**
- Must run on Windows
- Wheels must be built first
- PyInstaller installed in build environment

**Output:**
- `dist/exe/pyPASreporterGUI/pyPASreporterGUI.exe`

---

### `scripts/build_all.py`

Orchestrates the complete build pipeline.

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-pin` | Skip Superset pinning |
| `--skip-frontend` | Skip frontend build |
| `--skip-wheels` | Skip wheel building |
| `--skip-exe` | Skip executable build |
| `--skip-verify` | Skip verification |
| `--latest-tag` | Pin to latest tag |
| `--sha <SHA>` | Pin to specific SHA |

**Example:**
```bash
# Full build with latest Superset
python scripts/build_all.py --latest-tag

# Rebuild without re-pinning
python scripts/build_all.py --skip-pin

# Quick rebuild (existing frontend)
python scripts/build_all.py --skip-pin --skip-frontend
```

---

## Configuration Files

### `pyproject.toml`

Main package configuration:
- Package metadata
- Dependencies
- Build backend (hatchling)
- CLI entry point

### `VERSION_MATRIX.json`

Auto-generated by `pin_superset.py`:
```json
{
  "superset_sha": "abc123...",
  "superset_version": "4.0.0",
  "superset_branch": "4.0.0",
  "python_version": "3.11.7",
  "node_version": "v20.10.0",
  "npm_version": "10.8.2",
  "app_version": "0.1.0"
}
```

### `tools/build_exe.spec`

PyInstaller configuration for Windows builds.

---

## Development Workflow

### Adding a New Feature

1. Make changes in `src/pypasreportergui/`
2. Run tests: `pytest tests/`
3. Rebuild wheel: `python tools/build_wheels.py --app-only`

### Updating Superset Version

1. Check available versions:
   ```bash
   cd superset-src && git fetch --tags && git tag -l | tail -20
   ```

2. Pin to new version:
   ```bash
   python tools/pin_superset.py --latest-tag --write-version
   ```

3. Rebuild:
   ```bash
   python tools/build_superset.py
   python tools/build_wheels.py
   ```

### Testing Changes

```bash
# Unit tests
pytest tests/

# With server running:
python tools/verify.py

# Full test suite
python scripts/test_all.py
```

---

## Troubleshooting Builds

### Frontend Build Fails

```bash
# Clear node_modules and rebuild
cd superset-src/superset-frontend
rm -rf node_modules
npm ci
npm run build
```

### Wheel Build Fails

```bash
# Check for build artifacts
ls -la superset-src/build superset-src/*.egg-info

# Clean and retry
rm -rf superset-src/build superset-src/*.egg-info
python tools/build_wheels.py
```

### PyInstaller Issues

- Ensure all hidden imports are listed in `build_exe.spec`
- Check that static assets are included in `datas`
- See PyInstaller logs in `build/pyinstaller/`
