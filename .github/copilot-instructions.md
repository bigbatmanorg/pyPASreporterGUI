# pyPASreporterGUI - AI Coding Instructions

## Project Overview
pyPASreporterGUI is a **standalone Apache Superset wrapper** that eliminates Postgres, Redis, Celery, and Docker dependencies. Uses SQLite + filesystem cache with DuckDB support and custom branding.

## Architecture

### Directory Structure
- **src/pypasreportergui/** - Main package (CLI, runtime, branding)
- **superset-src/** - Pinned Superset checkout (gitignored, created by `pin_superset.py`)
- **tools/** - Build scripts: `pin_superset.py` → `build_superset.py` → `build_wheels.py`
- **scripts/** - Orchestration (`build_all.py` runs full pipeline)

### Key Design Decisions
- **No external services**: SQLite replaces Postgres; `FileSystemCache` replaces Redis
- **Branding via Flask Blueprint**: [branding/blueprint.py](src/pypasreportergui/branding/blueprint.py) registers at `/pypasreportergui_static/` without patching Superset
- **Runtime config generation**: `~/.pypasreportergui/superset_config.py` created via `generate_config()` with `FLASK_APP_MUTATOR` to inject the branding blueprint
- **PyInstaller support**: `is_frozen()` detection + path patching in `runtime.py` for bundled executables

### Data Flow
1. CLI (`cli.py`) calls `ensure_home_dir()` → `generate_config()` → sets `SUPERSET_CONFIG_PATH` env var
2. `init_database()` runs Flask-Migrate; `create_admin_user()` uses FAB security manager
3. `run_superset_server()` starts Gunicorn/Flask with branding blueprint auto-registered

## Developer Workflows

### First-time setup
```bash
bash tools/prereqs.sh && source .venv/bin/activate
python scripts/build_all.py  # Full build (~15 min for frontend)
```

### Quick iteration
```bash
python scripts/build_all.py --skip-frontend --skip-wheels  # Backend only
pypasreportergui run --port 8088 --reload --debug
```

### Testing
```bash
pytest tests/              # Unit tests (no server needed)
python tools/verify.py     # Smoke tests (requires running server)
```

### Pin specific Superset version
```bash
python tools/pin_superset.py --sha <commit>  # Or --latest-tag
```

## Code Conventions

### Python
- **Type hints required** on all functions
- Use `from __future__ import annotations` at top of every file
- **Typer** for CLI with `@app.command()` decorators
- **Rich** `Console` for formatted output (see `console.print()` patterns)

### Adding CLI Commands
Add to [cli.py](src/pypasreportergui/cli.py) following existing patterns:
```python
@app.command()
def my_command(
    option: str = typer.Option("default", "--option", "-o", help="Description"),
) -> None:
    """Docstring becomes CLI help text."""
    console.print("[bold blue]Starting...[/bold blue]")
```

### Modifying Superset Config
Edit the config template string in `generate_config()` in [runtime.py](src/pypasreportergui/runtime.py). Key sections:
- `FEATURE_FLAGS` - Enable/disable Superset features
- `CACHE_CONFIG` / `DATA_CACHE_CONFIG` - Filesystem cache settings
- `FLASK_APP_MUTATOR` - Blueprint registration hook

### Branding Assets
Place in [branding/static/](src/pypasreportergui/branding/static/) (logo-horiz.png, favicon.png). Referenced in config as `/pypasreportergui_static/<filename>`.

## Disabled Superset Features
These require Redis/Celery and are explicitly disabled in config:
- `ALERT_REPORTS: False` - Scheduled reports/alerts
- `SCHEDULED_QUERIES: False` - Async query scheduling
- `SQLLAB_ASYNC_TIME_LIMIT_SEC = 0` - Async SQL Lab queries

## Extensions Support (.supx)
- **Extensions directory**: `~/.pypasreportergui/supx/` (auto-created on init/run)
- **Detection**: `detect_superset_extensions_support()` checks if pinned Superset has extension runtime signals
- **CLI**: `pypasreportergui extensions status` shows support state and bundle counts
- **CSP**: Talisman enabled with relaxed CSP (`'unsafe-eval'`, `'unsafe-inline'`) for Module Federation

## Build Outputs
| Output | Location |
|--------|----------|
| Python wheels | `dist/wheels/` |
| Executable | `build/build_exe/pyPASreporterGUI` |
| Version metadata | `VERSION_MATRIX.json` |
