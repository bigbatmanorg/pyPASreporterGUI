#!/usr/bin/env python3
"""Runtime helpers for pyPASreporterGUI.

This module provides functions for:
- Setting up the application environment
- Generating configuration files
- Running Superset commands (db upgrade, init, run)
"""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Optional

from pypasreportergui import __app_name__, __version__


def get_superset_home() -> Path:
    """Get the pyPASreporterGUI home directory.

    Uses PYPASREPORTERGUI_HOME environment variable if set,
    otherwise defaults to ~/.pypasreportergui
    """
    home_env = os.environ.get("PYPASREPORTERGUI_HOME")
    if home_env:
        return Path(home_env).expanduser().resolve()
    return Path.home() / ".pypasreportergui"


def ensure_home_dir() -> Path:
    """Ensure the home directory exists and return its path."""
    home_dir = get_superset_home()
    home_dir.mkdir(parents=True, exist_ok=True)
    return home_dir


def get_branding_static_dir() -> Path:
    """Get the path to branding static assets."""
    return Path(__file__).parent / "branding" / "static"


def generate_secret_key() -> str:
    """Generate a random secret key for Flask."""
    return secrets.token_hex(32)


def generate_config(home_dir: Path, force: bool = False) -> Path:
    """Generate the Superset configuration file.

    Args:
        home_dir: The pyPASreporterGUI home directory
        force: If True, regenerate even if config exists

    Returns:
        Path to the configuration file
    """
    config_path = home_dir / "superset_config.py"

    if config_path.exists() and not force:
        return config_path

    # Get or generate secret key
    secret_key = os.environ.get("SUPERSET_SECRET_KEY")
    if not secret_key:
        secret_key_file = home_dir / ".secret_key"
        if secret_key_file.exists():
            secret_key = secret_key_file.read_text().strip()
        else:
            secret_key = generate_secret_key()
            secret_key_file.write_text(secret_key)

    # Get branding static directory (for blueprint)
    branding_static = get_branding_static_dir()

    # Convert paths to forward slashes for cross-platform config (Python strings)
    home_dir_str = str(home_dir).replace("\\", "/")
    branding_static_str = str(branding_static).replace("\\", "/")

    config_content = f'''# pyPASreporterGUI Superset Configuration
# Generated automatically - edit with care
# Version: {__version__}

import os
from pathlib import Path

# =============================================================================
# Application Identity
# =============================================================================
APP_NAME = "{__app_name__}"
APP_ICON = "/pypasreportergui_static/logo-horiz.png"
FAVICONS = [
    {{"href": "/pypasreportergui_static/favicon.png", "sizes": "16x16", "type": "image/png"}},
]

# =============================================================================
# Flask Configuration
# =============================================================================
SECRET_KEY = "{secret_key}"
FLASK_USE_RELOAD = True

# =============================================================================
# Database Configuration (SQLite - no Postgres required)
# =============================================================================
SQLALCHEMY_DATABASE_URI = "sqlite:///{home_dir_str}/superset.db?check_same_thread=false"

# =============================================================================
# Feature Flags
# =============================================================================
FEATURE_FLAGS = {{
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "EMBEDDED_SUPERSET": True,
    # Disable features requiring Celery/Redis
    "ALERT_REPORTS": False,
    "SCHEDULED_QUERIES": False,
}}

# =============================================================================
# Cache Configuration (Filesystem - no Redis required)
# =============================================================================
CACHE_CONFIG = {{
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "{home_dir_str}/cache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_THRESHOLD": 100,
}}

DATA_CACHE_CONFIG = {{
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "{home_dir_str}/data_cache",
    "CACHE_DEFAULT_TIMEOUT": 86400,  # 24 hours
    "CACHE_THRESHOLD": 100,
}}

FILTER_STATE_CACHE_CONFIG = {{
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "{home_dir_str}/filter_cache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_THRESHOLD": 100,
}}

EXPLORE_FORM_DATA_CACHE_CONFIG = {{
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": "{home_dir_str}/explore_cache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_THRESHOLD": 100,
}}

# =============================================================================
# Celery Configuration (Disabled - no Redis/broker required)
# =============================================================================
class CeleryConfig:
    broker_url = None
    result_backend = None

CELERY_CONFIG = CeleryConfig

# Disable async queries (requires Celery)
SQLLAB_ASYNC_TIME_LIMIT_SEC = 0

# =============================================================================
# Security Configuration
# =============================================================================
WTF_CSRF_ENABLED = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set True if using HTTPS
TALISMAN_ENABLED = False  # Disable for local development

# =============================================================================
# SQL Lab Configuration
# =============================================================================
SQLLAB_TIMEOUT = 300
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000

# =============================================================================
# Upload Configuration
# =============================================================================
UPLOAD_FOLDER = "{home_dir_str}/uploads"
ALLOWED_EXTENSIONS = {{"csv", "xlsx", "xls", "json", "parquet"}}

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL = "INFO"
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = "INFO"
FILENAME = "{home_dir_str}/logs/superset.log"

# =============================================================================
# Blueprint Registration (for custom branding)
# =============================================================================
def FLASK_APP_MUTATOR(app):
    """Register the pyPASreporterGUI branding blueprint."""
    try:
        from pypasreportergui.branding.blueprint import branding_bp
        app.register_blueprint(branding_bp)
    except ImportError:
        # Fallback: serve static files directly
        import os
        branding_dir = "{branding_static_str}"
        if os.path.isdir(branding_dir):
            from flask import send_from_directory
            @app.route("/pypasreportergui_static/<path:filename>")
            def pypasreportergui_static(filename):
                return send_from_directory(branding_dir, filename)

# =============================================================================
# DuckDB Configuration
# =============================================================================
# DuckDB is supported via duckdb-engine
# Connection string format: duckdb:///path/to/file.duckdb
# Or in-memory: duckdb:///:memory:

# Default allowed database drivers
PREFERRED_DATABASES = [
    "DuckDB",
    "SQLite",
    "PostgreSQL",
    "MySQL",
]

# =============================================================================
# Additional Settings
# =============================================================================
SUPERSET_WEBSERVER_PORT = int(os.environ.get("PYPASREPORTERGUI_PORT", 8088))
SUPERSET_WEBSERVER_TIMEOUT = 60

# Enable data upload
CSV_UPLOAD = True
EXCEL_UPLOAD = True

# Prevent loading examples (faster startup)
SUPERSET_LOAD_EXAMPLES = False
'''

    config_path.write_text(config_content)

    # Ensure cache and log directories exist
    (home_dir / "cache").mkdir(exist_ok=True)
    (home_dir / "data_cache").mkdir(exist_ok=True)
    (home_dir / "filter_cache").mkdir(exist_ok=True)
    (home_dir / "explore_cache").mkdir(exist_ok=True)
    (home_dir / "uploads").mkdir(exist_ok=True)
    (home_dir / "logs").mkdir(exist_ok=True)

    return config_path


def is_frozen() -> bool:
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def run_superset_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a Superset CLI command.

    Args:
        args: Arguments to pass to the superset command
        check: If True, raise on non-zero exit code

    Returns:
        CompletedProcess instance (or simulated one for frozen apps)
    """
    if is_frozen():
        # In a PyInstaller bundle, we must call Superset's CLI directly
        # because sys.executable is the bundle, not Python
        return _run_superset_command_frozen(args, check)
    else:
        # Normal Python execution - use subprocess
        cmd = [sys.executable, "-m", "superset.cli.main"] + args
        print(f"+ {' '.join(cmd)}")
        return subprocess.run(cmd, check=check)


def _run_superset_command_frozen(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run Superset CLI command directly when frozen (PyInstaller).

    This imports and calls Superset's CLI functions directly instead of
    spawning a subprocess, since sys.executable is the bundle itself.
    """
    import click
    from click.testing import CliRunner
    from superset.cli.main import superset as superset_cli

    print(f"+ [frozen] superset {' '.join(args)}")

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(superset_cli, args, catch_exceptions=False)

    # Print output
    if result.output:
        print(result.output, end='')
    if result.stderr_bytes:
        print(result.stderr_bytes.decode('utf-8', errors='replace'), end='', file=sys.stderr)

    # Create a CompletedProcess-like result
    completed = subprocess.CompletedProcess(
        args=["superset"] + args,
        returncode=result.exit_code,
        stdout=result.output,
        stderr=result.stderr_bytes.decode('utf-8', errors='replace') if result.stderr_bytes else '',
    )

    if check and result.exit_code != 0:
        raise subprocess.CalledProcessError(
            result.exit_code,
            ["superset"] + args,
            output=result.output,
            stderr=completed.stderr,
        )

    return completed


def init_database() -> None:
    """Initialize the Superset database (run migrations)."""
    run_superset_command(["db", "upgrade"])
    run_superset_command(["init"])


def create_admin_user(
    username: str = "admin",
    password: str = "admin",
    email: str = "admin@pypasreportergui.local",
    firstname: str = "pyPASreporterGUI",
    lastname: str = "Admin",
) -> None:
    """Create an admin user if one doesn't exist."""
    # Use environment variables if set
    username = os.environ.get("SUPERSET_ADMIN_USERNAME", username)
    password = os.environ.get("SUPERSET_ADMIN_PASSWORD", password)
    email = os.environ.get("SUPERSET_ADMIN_EMAIL", email)

    cmd = [
        "fab",
        "create-admin",
        "--username", username,
        "--firstname", firstname,
        "--lastname", lastname,
        "--email", email,
        "--password", password,
    ]

    result = run_superset_command(cmd, check=False)
    if result.returncode != 0:
        print("Admin user may already exist or creation failed; continuing.")


def run_superset_server(
    host: str = "127.0.0.1",
    port: int = 8088,
    reload: bool = False,
    debug: bool = False,
) -> None:
    """Start the Superset development server."""
    if is_frozen():
        # In frozen mode, run the Flask app directly
        _run_superset_server_frozen(host, port, debug)
    else:
        # Normal mode - use subprocess
        cmd = [
            "run",
            "-h", host,
            "-p", str(port),
            "--with-threads",
        ]

        if reload:
            cmd.append("--reload")

        if debug:
            cmd.append("--debugger")

        run_superset_command(cmd)


def _run_superset_server_frozen(
    host: str = "127.0.0.1",
    port: int = 8088,
    debug: bool = False,
) -> None:
    """Run Superset server directly when frozen (PyInstaller)."""
    from superset.app import create_app

    # Create the Flask application
    app = create_app()

    # Register our branding blueprint
    try:
        from pypasreportergui.branding.blueprint import branding_bp
        app.register_blueprint(branding_bp)
    except Exception as e:
        print(f"Warning: Could not register branding blueprint: {e}")

    # Run with the built-in Flask server (threaded for better performance)
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=False,  # Reloader doesn't work in frozen apps
    )


def get_superset_env() -> dict:
    """Get environment variables configured for Superset."""
    home_dir = get_superset_home()
    config_path = home_dir / "superset_config.py"

    env = os.environ.copy()
    env["SUPERSET_HOME"] = str(home_dir)
    env["SUPERSET_CONFIG_PATH"] = str(config_path)
    env.setdefault("FLASK_ENV", "production")

    return env
