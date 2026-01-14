"""Flask blueprint for serving pyPASreporterGUI branding assets.

This blueprint serves static assets (logo, favicon) from the branding/static
directory without requiring modifications to Superset's core code.
"""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, send_from_directory

# Get the static directory path relative to this file
STATIC_DIR = Path(__file__).parent / "static"

# Create the blueprint
branding_bp = Blueprint(
    "pypasreportergui_branding",
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path="/pypasreportergui_static",
)


@branding_bp.route("/pypasreportergui_static/<path:filename>")
def serve_branding_static(filename: str):
    """Serve static files from the branding static directory."""
    return send_from_directory(STATIC_DIR, filename)


@branding_bp.route("/api/pypasreportergui/ping")
def ping():
    """Health check endpoint for pyPASreporterGUI.

    Returns basic information about the pyPASreporterGUI installation.
    Used by smoke tests to verify the branding extension is loaded.
    """
    from pypasreportergui import __app_name__, __version__

    return jsonify({
        "status": "ok",
        "app_name": __app_name__,
        "version": __version__,
        "message": f"{__app_name__} is running!",
    })


@branding_bp.route("/api/pypasreportergui/info")
def info():
    """Get detailed information about pyPASreporterGUI configuration.

    Returns version info, paths, and feature status for diagnostic purposes.
    """
    from pypasreportergui import __app_name__, __version__
    from pypasreportergui.runtime import get_superset_home, get_branding_static_dir

    home_dir = get_superset_home()
    branding_dir = get_branding_static_dir()

    return jsonify({
        "app_name": __app_name__,
        "version": __version__,
        "home_dir": str(home_dir),
        "branding_dir": str(branding_dir),
        "branding_assets": {
            "logo": "/pypasreportergui_static/logo-horiz.png",
            "favicon": "/pypasreportergui_static/favicon.png",
        },
        "features": {
            "duckdb_support": True,
            "celery_required": False,
            "redis_required": False,
            "postgres_required": False,
        },
    })
