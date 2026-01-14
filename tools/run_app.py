#!/usr/bin/env python3
"""Initialize and run Superset with pyPASreporterGUI config.

This is the low-level runner that:
1. Sets up environment variables
2. Runs database migrations
3. Creates admin user
4. Starts the Superset server

For normal usage, prefer the `pypasreportergui run` CLI command.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def venv_env(base_dir: Path) -> dict[str, str]:
    """Get environment with venv activated."""
    env = os.environ.copy()
    venv_root = base_dir / ".venv"
    if venv_root.exists():
        bin_dir = venv_root / ("Scripts" if os.name == "nt" else "bin")
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(venv_root)
    return env


def run(cmd: list[str], env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command with the given environment."""
    print(f"+ {' '.join(cmd)}")
    return subprocess.run(cmd, env=env, check=check)


def create_admin(env: dict[str, str], username: str, password: str, email: str) -> None:
    """Create an admin user if one doesn't exist."""
    cmd = [
        "superset", "fab", "create-admin",
        "--username", username,
        "--firstname", "pyPASreporterGUI",
        "--lastname", "Admin",
        "--email", email,
        "--password", password,
    ]
    result = run(cmd, env, check=False)
    if result.returncode != 0:
        print("Admin user may already exist; continuing.")


def find_config(base_dir: Path) -> Path:
    """Find the Superset configuration file."""
    # Try generated config in home dir
    home_dir = Path.home() / ".pypasreportergui"
    if (home_dir / "superset_config.py").exists():
        return home_dir / "superset_config.py"

    # Try local config
    if (base_dir / "superset_config.py").exists():
        return base_dir / "superset_config.py"

    # Generate config
    print("Generating default configuration...")
    home_dir.mkdir(parents=True, exist_ok=True)

    try:
        from pypasreportergui.runtime import generate_config
        return generate_config(home_dir)
    except ImportError:
        # Minimal fallback config
        config_path = home_dir / "superset_config.py"
        import secrets
        config_path.write_text(f'''
import os
SECRET_KEY = "{secrets.token_hex(32)}"
SQLALCHEMY_DATABASE_URI = "sqlite:///{home_dir}/superset.db"
APP_NAME = "pyPASreporterGUI"
''')
        return config_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="8088", help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--init-only", action="store_true", help="Only initialize, don't start server")
    parser.add_argument("--no-init", action="store_true", help="Skip initialization")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    config_path = find_config(base_dir)

    env = venv_env(base_dir)
    env["SUPERSET_CONFIG_PATH"] = str(config_path)
    env.setdefault("FLASK_ENV", "development")

    # Get credentials from environment or use defaults
    username = env.get("SUPERSET_ADMIN_USERNAME", "admin")
    password = env.get("SUPERSET_ADMIN_PASSWORD", "admin")
    email = env.get("SUPERSET_ADMIN_EMAIL", "admin@pypasreportergui.local")

    # Initialize database and admin user
    if not args.no_init:
        print("\nInitializing database...")
        run(["superset", "db", "upgrade"], env)
        run(["superset", "init"], env)
        create_admin(env, username, password, email)

    if args.init_only:
        print("\nInitialization complete.")
        return 0

    # Start server
    print(f"\nStarting pyPASreporterGUI server...")
    print(f"  Config: {config_path}")
    print(f"  URL: http://{args.host}:{args.port}")
    print("  Press Ctrl+C to stop\n")

    cmd = [
        "superset", "run",
        "-h", args.host,
        "-p", str(args.port),
        "--with-threads",
    ]

    if args.reload:
        cmd.append("--reload")

    run(cmd, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
