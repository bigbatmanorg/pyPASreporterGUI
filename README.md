# pyPASreporterGUI

**A branded, standalone Superset-based data analytics GUI with DuckDB support.**

pyPASreporterGUI wraps Apache Superset into a simple, self-contained application that:
- Runs **without Postgres, Redis, Celery, or Docker** (uses SQLite + filesystem cache)
- Provides native **DuckDB** support for analytics workloads
- Ships with custom **pyPASreporterGUI branding** (logo, favicon, app name)
- Builds to a **Python wheel** and optional **Windows executable**

---

## Quick Start

### Prerequisites
- Python 3.10+ 
- Node.js 18+ with npm 10+
- Git

### Installation (from source)

**Linux/macOS:**
```bash
cd pyPASreporterGUI
bash tools/prereqs.sh
source .venv/bin/activate

python scripts/build_all.py
pypasreportergui run --port 8088
```

**Windows (PowerShell):**
```powershell
cd pyPASreporterGUI
.\tools\prereqs.ps1 -UseConda:$false
.\.venv\Scripts\Activate.ps1

python scripts\build_all.py
pypasreportergui run --port 8088
```

### Installation (from wheel)

```bash
pip install dist/wheels/pyPASreporterGUI-*.whl
pypasreportergui run --port 8088
```

### Offline Installation

```bash
pip install --no-index --find-links dist/wheels pyPASreporterGUI
pypasreportergui run
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `pypasreportergui run` | Start the pyPASreporterGUI server |
| `pypasreportergui init` | Initialize database + create admin user |
| `pypasreportergui doctor` | Print version info and sanity checks |
| `pypasreportergui add-duckdb` | Register a DuckDB database connection |

### Examples

```bash
# Start on custom port with auto-reload
pypasreportergui run --port 9090 --reload

# Initialize without starting server
pypasreportergui init --admin-password secretpass

# Check installation health
pypasreportergui doctor

# Add a DuckDB database
pypasreportergui add-duckdb --path /data/analytics.duckdb --name "Analytics DB"
```

---

## Build Outputs

After running `python scripts/build_all.py`:

| Output | Location |
|--------|----------|
| Python wheels | `dist/wheels/` |
| Windows executable | `dist/exe/pyPASreporterGUI.exe` |
| Build logs | `logs/` |

---

## Architecture

```
pyPASreporterGUI/
├── src/pypasreportergui/     # Main Python package
│   ├── cli.py                # Typer CLI entrypoint
│   ├── runtime.py            # Environment setup + run helpers
│   ├── superset_config.py    # Default Superset config template
│   └── branding/             # Custom branding assets
├── tools/                    # Build + utility scripts
├── scripts/                  # Orchestration scripts
├── superset-src/             # Pinned Superset checkout (gitignored)
└── dist/                     # Build outputs
```

---

## DuckDB Support

pyPASreporterGUI includes DuckDB and duckdb-engine. To use DuckDB:

1. **Via CLI:**
   ```bash
   pypasreportergui add-duckdb --path /path/to/data.duckdb
   ```

2. **Via Superset UI:**
   - Go to **Data → Databases → + Database**
   - Select "Other" and use SQLAlchemy URI:
     ```
     duckdb:////absolute/path/to/file.duckdb
     ```

---

## Configuration

pyPASreporterGUI stores its configuration in `~/.pypasreportergui/`:

| File | Purpose |
|------|---------|
| `superset_config.py` | Superset configuration |
| `superset.db` | SQLite metadata database |
| `superset_home/` | Superset data directory |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYPASREPORTERGUI_HOME` | `~/.pypasreportergui` | Config/data directory |
| `PYPASREPORTERGUI_PORT` | `8088` | Default server port |
| `SUPERSET_SECRET_KEY` | (generated) | Flask secret key |

---

## Documentation

- [INSTALL.md](docs/INSTALL.md) - Installation guide
- [BUILD.md](docs/BUILD.md) - Build system overview
- [RELEASE.md](docs/RELEASE.md) - Release workflow
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues
- [VERSION_MATRIX.md](docs/VERSION_MATRIX.md) - Pinned versions

---

## What Won't Work

The following Superset features require Redis/Celery and are **disabled**:

- Scheduled reports/alerts
- Async query execution (uses sync instead)
- Distributed caching

All other Superset features (dashboards, charts, SQL Lab, etc.) work normally.

---

## License

Apache License 2.0 - see [LICENSE](LICENSE)
