#!/usr/bin/env python3
"""Build Python wheel packages for Superset and pyPASreporterGUI.

This script builds distribution-ready wheel packages:
- apache-superset (from superset-src/)
- pyPASreporterGUI (from this repository)

Output is placed in dist/wheels/ for offline installation.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a command and check for errors."""
    print(f"+ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def build_wheel(package_dir: Path, output_dir: Path, package_name: str) -> Path | None:
    """Build a wheel for a Python package.

    Args:
        package_dir: Directory containing pyproject.toml
        output_dir: Directory to output wheels
        package_name: Expected package name (for identification)

    Returns:
        Path to built wheel, or None if skipped
    """
    print(f"\n{'='*60}")
    print(f"Building wheel: {package_name}")
    print(f"{'='*60}")

    pyproject = package_dir / "pyproject.toml"
    setup_py = package_dir / "setup.py"

    if not pyproject.exists() and not setup_py.exists():
        print(f"Warning: No pyproject.toml or setup.py in {package_dir}, skipping")
        return None

    # Record existing wheels before build
    existing_wheels = set(output_dir.glob("*.whl"))

    # Clean previous builds
    for pattern in ["build", "*.egg-info", "dist"]:
        for path in package_dir.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)

    # Build wheel using uv or pip
    uv_available = subprocess.run(["uv", "--version"], capture_output=True).returncode == 0

    if uv_available:
        run(["uv", "build", "--wheel", "--out-dir", str(output_dir)], cwd=package_dir)
    else:
        run(["python", "-m", "build", "--wheel", "--outdir", str(output_dir)], cwd=package_dir)

    # Find newly created wheel
    new_wheels = set(output_dir.glob("*.whl")) - existing_wheels
    if new_wheels:
        wheel = max(new_wheels, key=lambda p: p.stat().st_mtime)
        print(f"✓ Built: {wheel.name}")
        return wheel

    # Fallback: search by package name pattern
    normalized = package_name.lower().replace("-", "_")
    for wheel in output_dir.glob("*.whl"):
        if normalized in wheel.name.lower():
            print(f"✓ Found: {wheel.name}")
            return wheel

    print(f"Warning: No wheel found for {package_name}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist/wheels",
                        help="Output directory for wheels")
    parser.add_argument("--superset-only", action="store_true",
                        help="Build only apache-superset wheel")
    parser.add_argument("--app-only", action="store_true",
                        help="Build only pyPASreporterGUI wheel")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    superset_src = base_dir / "superset-src"
    output_dir = base_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    built_wheels: list[Path] = []

    # Build Superset wheel
    if not args.app_only:
        if not superset_src.exists():
            print("Error: superset-src not found.")
            print("Run: python tools/pin_superset.py first")
            return 1

        # Check for sub-packages first (newer Superset versions)
        sub_packages = [
            (superset_src / "superset-core", "apache-superset-core"),
            (superset_src / "superset-extensions-cli", "superset-extensions-cli"),
        ]

        for pkg_dir, pkg_name in sub_packages:
            if pkg_dir.exists():
                wheel = build_wheel(pkg_dir, output_dir, pkg_name)
                if wheel:
                    built_wheels.append(wheel)

        # Build main Superset package
        wheel = build_wheel(superset_src, output_dir, "apache-superset")
        if wheel:
            built_wheels.append(wheel)

    # Build pyPASreporterGUI wheel
    if not args.superset_only:
        wheel = build_wheel(base_dir, output_dir, "pyPASreporterGUI")
        if wheel:
            built_wheels.append(wheel)

    # Summary
    print(f"\n{'='*60}")
    print("WHEEL BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print()
    print("Built wheels:")
    for wheel in built_wheels:
        size_mb = wheel.stat().st_size / (1024 * 1024)
        print(f"  📦 {wheel.name} ({size_mb:.1f} MB)")

    print()
    print("Installation commands:")
    print(f"  # Standard install:")
    print(f"  pip install {output_dir / 'pyPASreporterGUI-*.whl'}")
    print()
    print(f"  # Offline install:")
    print(f"  pip install --no-index --find-links {output_dir} pyPASreporterGUI")

    return 0


if __name__ == "__main__":
    sys.exit(main())
