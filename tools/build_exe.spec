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

# Analysis
block_cipher = None

# Data files to include
datas = [
    # Branding assets
    (str(BRANDING_STATIC), "pypasreportergui/branding/static"),
]

# Add Superset static assets if found
if SUPERSET_DIR:
    superset_static = SUPERSET_DIR / "static"
    if superset_static.exists():
        datas.append((str(superset_static), "superset/static"))
    
    superset_templates = SUPERSET_DIR / "templates"
    if superset_templates.exists():
        datas.append((str(superset_templates), "superset/templates"))

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
    "click.testing",  # Needed for frozen CLI execution
    "rich",
    "rich.console",
    "rich.table",
    
    # Database
    "duckdb",
    "duckdb_engine",
    "duckdb_engine.datatypes",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    
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
    
    # Superset (main modules)
    "superset",
    "superset.app",
    "superset.config",
    "superset.cli",
    "superset.cli.main",  # Needed for frozen CLI execution
    "superset.views",
    "superset.models",
    "superset.connectors",
    "superset.db_engine_specs",
    "superset.security",
    "superset.utils",
    
    # Data processing
    "pandas",
    "numpy",
    "sqlparse",
    
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
        # Exclude unnecessary large packages
        "matplotlib",
        "PIL",
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
    console=True,  # Console app for CLI
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
