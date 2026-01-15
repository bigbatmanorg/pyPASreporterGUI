# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for pyPASreporterGUI.

This spec file configures PyInstaller to build a standalone executable
that includes all necessary dependencies and assets.
"""
import os
import sys
from pathlib import Path

# Get paths
ROOT = Path(SPECPATH).parent
SRC_DIR = ROOT / "src" / "pypasreportergui"
BRANDING_STATIC = SRC_DIR / "branding" / "static"

# Find superset installation
import importlib.util
superset_spec = importlib.util.find_spec("superset")
if superset_spec and superset_spec.origin:
    SUPERSET_DIR = Path(superset_spec.origin).parent
else:
    SUPERSET_DIR = None

block_cipher = None

# Data files to include
datas = [
    # Branding assets
    (str(BRANDING_STATIC), "pypasreportergui/branding/static"),
]

# Add Superset assets if found
if SUPERSET_DIR:
    superset_static = SUPERSET_DIR / "static"
    if superset_static.exists():
        datas.append((str(superset_static), "superset/static"))

    superset_templates = SUPERSET_DIR / "templates"
    if superset_templates.exists():
        datas.append((str(superset_templates), "superset/templates"))

    # FIX: Superset DB migrations (required for `superset db upgrade`)
    superset_migrations = SUPERSET_DIR / "migrations"
    if superset_migrations.exists():
        datas.append((str(superset_migrations), "superset/migrations"))

    # Strongly recommended: translations (Superset imports these dynamically)
    superset_translations = SUPERSET_DIR / "translations"
    if superset_translations.exists():
        datas.append((str(superset_translations), "superset/translations"))

# Add Flask-AppBuilder templates (required for login/security pages)
import flask_appbuilder
fab_dir = Path(flask_appbuilder.__file__).parent
fab_templates = fab_dir / "templates"
if fab_templates.exists():
    datas.append((str(fab_templates), "flask_appbuilder/templates"))
fab_static = fab_dir / "static"
if fab_static.exists():
    datas.append((str(fab_static), "flask_appbuilder/static"))

# Add package metadata for SQLAlchemy dialect entry points
# This is required for Superset to detect available database drivers
from PyInstaller.utils.hooks import copy_metadata
datas += copy_metadata("duckdb-engine")
datas += copy_metadata("sqlalchemy")

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # Core app
    "pypasreportergui",
    "pypasreportergui.cli",
    "pypasreportergui.runtime",
    "pypasreportergui.branding",
    "pypasreportergui.branding.blueprint",

    # CLI framework
    "typer",
    "typer.main",
    "click",
    "click.testing",
    "rich",
    "rich.console",
    "rich.table",

    # Logging (required by alembic env.py)
    "logging",
    "logging.config",
    "logging.handlers",

    # Database - DuckDB support
    "duckdb",
    "duckdb.typing",
    "duckdb.functional",
    "duckdb.value",
    "_duckdb",  # Native extension module
    "duckdb_engine",
    "duckdb_engine.datatypes",
    "duckdb_engine.config",
    "duckdb_engine._supports",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.postgresql",  # duckdb_engine uses PG dialect as base

    # Flask/Web
    "flask",
    "flask_appbuilder",
    "flask_caching",
    "flask_compress",
    "flask_login",
    "flask_migrate",
    "flask_sqlalchemy",
    "flask_wtf",
    "wtforms",
    "jinja2",
    "werkzeug",

    # Alembic (database migrations)
    "alembic",
    "alembic.config",
    "alembic.script",
    "alembic.runtime",
    "alembic.runtime.migration",
    "alembic.command",
    "alembic.operations",
    "alembic.ddl",
    "alembic.ddl.impl",

    # Migration script dependencies (dynamically loaded by Alembic)
    "isodate",
    "sqlalchemy_utils",
    "flask_appbuilder",
    "flask_appbuilder.models",
    "flask_appbuilder.models.mixins",
    "importlib",

    # Superset (main modules)
    "superset",
    "superset.app",
    "superset.config",
    "superset.cli",
    "superset.cli.main",
    "superset.views",
    "superset.models",
    "superset.connectors",
    "superset.db_engine_specs",
    "superset.security",
    "superset.utils",
    "superset.migrations",  # (folder still must be in datas)

    # Celery (required by Superset even when disabled)
    "celery",
    "celery.fixups",
    "celery.fixups.django",
    "celery.loaders",
    "celery.loaders.app",
    "celery.loaders.default",
    "celery.loaders.base",
    "celery.backends",
    "celery.backends.base",
    "celery.backends.cache",
    "celery.backends.database",
    "celery.backends.redis",
    "celery.backends.rpc",
    "celery.app",
    "celery.app.defaults",
    "celery.app.task",
    "celery.app.log",
    "celery.app.control",
    "celery.app.events",
    "celery.app.amqp",
    "celery.concurrency",
    "celery.concurrency.prefork",
    "celery.concurrency.thread",
    "celery.worker",
    "celery.bin",
    "celery.utils",
    "celery.utils.log",
    "celery.utils.time",
    "celery.utils.dispatch",
    "celery.events",
    "kombu",
    "kombu.transport",
    "kombu.transport.virtual",
    "kombu.transport.memory",
    "kombu.utils",
    "kombu.utils.compat",
    "kombu.utils.encoding",
    "billiard",
    "vine",
    "amqp",

    # Data processing
    "pandas",
    "numpy",
    "sqlparse",

    # Image processing
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",

    # Other common dependencies
    "email_validator",
    "marshmallow",
    "apispec",
]

a = Analysis(
    [str(SRC_DIR / "cli.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "tkinter",
        "test",
        "tests",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pyPASreporterGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(BRANDING_STATIC / "favicon.png") if (BRANDING_STATIC / "favicon.png").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pyPASreporterGUI",
)
