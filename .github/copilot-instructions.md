# pyPASreporterGUI - AI Coding Instructions

## Project Overview
pyPASreporterGUI is a **standalone Apache Superset wrapper** that eliminates the need for Postgres, Redis, Celery, or Docker. It uses SQLite + filesystem cache and adds DuckDB support with custom branding.

## Architecture
- **src/pypasreportergui/** - Main package: CLI (Typer), runtime helpers, Flask branding blueprint
- **superset-src/** - Pinned Apache Superset checkout (gitignored, created by build)
- **tools/** - Individual build scripts (`pin_superset.py`, `build_superset.py`, `build_wheels.py`)
- **scripts/** - Orchestration (`build_all.py` runs the full pipeline)

### Key Design Decisions
- **No external services**: SQLite replaces Postgres, FileSystemCache replaces Redis
- **Branding via Flask Blueprint**: [src/pypasreportergui/branding/blueprint.py](src/pypasreportergui/branding/blueprint.py) injects custom assets without patching Superset
- **Config generation**: Runtime generates `~/.pypasreportergui/superset_config.py` with all required settings

## Developer Workflows

### First-time setup
```bash
bash tools/prereqs.sh && source .venv/bin/activate
python scripts/build_all.py  # Full build (frontend takes ~15 min)
```

### Running the app
```bash
pypasreportergui run --port 8088
```

### Quick rebuild (skip frontend)
```bash
python scripts/build_all.py --skip-frontend --skip-wheels
```

### Testing
```bash
pytest tests/  # Unit tests only
python tools/verify.py  # Smoke tests (requires running server)
```

## Code Conventions

### Python
- **Type hints required** on all functions
- **Typer** for CLI commands in [cli.py](src/pypasreportergui/cli.py)
- **Rich** for console output formatting
- Use `from __future__ import annotations` for forward references

### Adding CLI Commands
Add to [src/pypasreportergui/cli.py](src/pypasreportergui/cli.py) as `@app.command()` decorated functions. Follow existing patterns like `run()` and `init()`.

### Configuration Changes
Modify the config template in [src/pypasreportergui/runtime.py](src/pypasreportergui/runtime.py) `generate_config()` function. Changes affect all new installations.

### Branding Assets
Place in [src/pypasreportergui/branding/static/](src/pypasreportergui/branding/static/). Referenced via `/pypasreportergui_static/` URL path.

## Version Tracking
- **VERSION_MATRIX.json** - Auto-generated build metadata (Superset SHA, Python/Node versions)
- Pin specific Superset version: `python tools/pin_superset.py --sha <commit>`

## What Won't Work
These Superset features require Redis/Celery and are **disabled**:
- Scheduled reports/alerts (`ALERT_REPORTS: False`)
- Async query execution
- Distributed caching

## Superset-Specific Guidance
When modifying anything in **superset-src/**, refer to [superset-src/AGENTS.md](superset-src/AGENTS.md) for Superset-specific conventions (TypeScript patterns, testing strategy, etc.).
