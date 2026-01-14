#!/usr/bin/env python3
"""Build Superset frontend and install backend into the venv.

This script:
1. Verifies superset-src exists (run pin_superset.py first)
2. Builds the frontend (npm ci + npm run build)
3. Installs the backend in editable mode
4. Installs DuckDB and other required packages
"""
from __future__ import annotations

import argparse
import json
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


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    """Run a command and check for errors."""
    print(f"+ {' '.join(cmd)}")
    # Use shell=True on Windows for commands like npm which are actually .cmd files
    use_shell = os.name == "nt" and cmd and cmd[0] in ("npm", "npx", "node")
    subprocess.run(cmd, cwd=cwd, check=True, env=env, shell=use_shell)


def read_version_matrix(base_dir: Path) -> dict:
    """Read VERSION_MATRIX.json if it exists."""
    path = base_dir / "VERSION_MATRIX.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_git_head(repo_root: Path) -> str:
    """Get the current HEAD SHA of the repository."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def pick_build_script(package_json: Path) -> str:
    """Determine which npm script to use for building."""
    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})

    # Prefer 'build' script
    if "build" in scripts:
        return "build"

    # Try common alternatives
    for candidate in ("build-prod", "build:prod", "build:production"):
        if candidate in scripts:
            return candidate

    # Fall back to any build-related script
    for name in scripts:
        if "build" in name.lower():
            return name

    raise RuntimeError("No build script found in superset-frontend/package.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-frontend", action="store_true",
                        help="Skip frontend build (use existing assets)")
    parser.add_argument("--skip-backend", action="store_true",
                        help="Skip backend installation")
    parser.add_argument("--skip-packages", action="store_true",
                        help="Skip package installation (DuckDB, etc.)")
    parser.add_argument("--verify-sha", action="store_true",
                        help="Verify repo SHA matches VERSION_MATRIX.json")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    repo_root = base_dir / "superset-src"

    if not repo_root.exists():
        print("Error: superset-src not found.")
        print("Run: python tools/pin_superset.py first")
        return 1

    # Verify SHA if requested
    if args.verify_sha:
        version_matrix = read_version_matrix(base_dir)
        expected_sha = version_matrix.get("superset_sha")
        actual_sha = get_git_head(repo_root)
        if expected_sha and actual_sha != expected_sha:
            print(f"Error: superset-src is at {actual_sha[:12]}, expected {expected_sha[:12]}")
            print("Run: python tools/pin_superset.py --sha <sha> to update")
            return 1

    env = venv_env(base_dir)

    # Print environment info
    print("\n" + "=" * 60)
    print("Build Environment")
    print("=" * 60)
    run(["python", "--version"], env=env)
    run(["node", "--version"], env=env)
    run(["npm", "--version"], env=env)

    # Build frontend
    if not args.skip_frontend:
        print("\n" + "=" * 60)
        print("Building Frontend")
        print("=" * 60)

        frontend_root = repo_root / "superset-frontend"
        package_json = frontend_root / "package.json"

        if not package_json.exists():
            print("Error: superset-frontend/package.json not found")
            return 1

        build_script = pick_build_script(package_json)
        print(f"Using npm script: {build_script}")

        # Install dependencies
        print("\nInstalling npm dependencies...")
        run(["npm", "ci"], cwd=frontend_root, env=env)

        # Build
        print(f"\nBuilding frontend with 'npm run {build_script}'...")
        run(["npm", "run", build_script], cwd=frontend_root, env=env)

    # Install backend
    if not args.skip_backend:
        print("\n" + "=" * 60)
        print("Installing Backend")
        print("=" * 60)

        # Use uv if available
        if subprocess.run(["uv", "--version"], capture_output=True).returncode == 0:
            run(["uv", "pip", "install", "-e", str(repo_root)], env=env)
        else:
            run(["pip", "install", "-e", str(repo_root)], env=env)

    # Install additional packages
    if not args.skip_packages:
        print("\n" + "=" * 60)
        print("Installing Additional Packages")
        print("=" * 60)

        packages = [
            "duckdb>=0.10.0",
            "duckdb-engine>=0.10.0",
            "typer>=0.9.0",
            "rich>=13.0.0",
            "requests>=2.28.0",
        ]

        if subprocess.run(["uv", "--version"], capture_output=True).returncode == 0:
            run(["uv", "pip", "install"] + packages, env=env)
        else:
            run(["pip", "install"] + packages, env=env)

    # Summary
    print("\n" + "=" * 60)
    print("Build Complete")
    print("=" * 60)
    print(f"Superset repo: {repo_root}")
    print(f"Current SHA: {get_git_head(repo_root)[:12]}")

    frontend_assets = repo_root / "superset" / "static" / "assets"
    if frontend_assets.exists():
        print(f"Frontend assets: {frontend_assets}")
    else:
        print("Warning: Frontend assets not found at expected location")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
