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


def build_wheel(package_dir: Path, output_dir: Path, package_name: str) -> list[Path]:
    """Build a wheel for a Python package.

    Args:
        package_dir: Directory containing pyproject.toml
        output_dir: Directory to output wheels
        package_name: Expected package name (for identification)

    Returns:
        List of paths to built wheels (can be multiple or empty)
    """
    print(f"\n{'='*60}")
    print(f"Building wheel: {package_name}")
    print(f"{'='*60}")

    pyproject = package_dir / "pyproject.toml"
    setup_py = package_dir / "setup.py"

    if not pyproject.exists() and not setup_py.exists():
        print(f"Warning: No pyproject.toml or setup.py in {package_dir}, skipping")
        return []

    # Record existing wheels before build
    existing_wheels = set(output_dir.glob("*.whl"))

    # Clean previous builds in package directory (but not output_dir)
    for pattern in ["build", "*.egg-info"]:
        for path in package_dir.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
    
    # Clean dist only in package_dir, but NEVER delete output_dir or its parent
    pkg_dist = package_dir / "dist"
    if pkg_dist.exists():
        # Resolve both paths to compare properly
        pkg_dist_resolved = pkg_dist.resolve()
        output_dir_resolved = output_dir.resolve()
        # Don't delete if it's the output directory or its parent
        if (pkg_dist_resolved != output_dir_resolved and 
            pkg_dist_resolved != output_dir_resolved.parent and
            not str(output_dir_resolved).startswith(str(pkg_dist_resolved))):
            shutil.rmtree(pkg_dist)

    # Build wheel using uv or pip
    uv_available = subprocess.run(["uv", "--version"], capture_output=True).returncode == 0

    try:
        if uv_available:
            run(["uv", "build", "--wheel", "--out-dir", str(output_dir)], cwd=package_dir)
        else:
            run(["python", "-m", "build", "--wheel", "--outdir", str(output_dir)], cwd=package_dir)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Build failed for {package_name}: {e}")
        return []

    # Find newly created wheels
    new_wheels = list(set(output_dir.glob("*.whl")) - existing_wheels)
    if new_wheels:
        for wheel in new_wheels:
            print(f"✓ Built: {wheel.name}")
        return new_wheels

    print(f"Warning: No new wheel found for {package_name}")
    return []


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

        # Build main Superset package first
        wheels = build_wheel(superset_src, output_dir, "apache-superset")
        built_wheels.extend(wheels)

        # Check for sub-packages (newer Superset versions may have these)
        sub_packages = [
            (superset_src / "superset-core", "apache-superset-core"),
            (superset_src / "superset-extensions-cli", "superset-extensions-cli"),
        ]

        for pkg_dir, pkg_name in sub_packages:
            # Only build if it has its own pyproject.toml/setup.py
            if pkg_dir.exists() and (
                (pkg_dir / "pyproject.toml").exists() or 
                (pkg_dir / "setup.py").exists()
            ):
                wheels = build_wheel(pkg_dir, output_dir, pkg_name)
                built_wheels.extend(wheels)

    # Build pyPASreporterGUI wheel
    if not args.superset_only:
        wheels = build_wheel(base_dir, output_dir, "pyPASreporterGUI")
        built_wheels.extend(wheels)

    # Summary
    print(f"\n{'='*60}")
    print("WHEEL BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Show all wheels in output directory
    all_wheels = list(output_dir.glob("*.whl"))
    if all_wheels:
        print("Wheels in output directory:")
        for wheel in sorted(all_wheels):
            try:
                size_mb = wheel.stat().st_size / (1024 * 1024)
                print(f"  📦 {wheel.name} ({size_mb:.1f} MB)")
            except FileNotFoundError:
                print(f"  📦 {wheel.name} (file missing)")
    else:
        print("No wheels found in output directory!")
        return 1

    print()
    print("Installation commands:")
    print(f"  # Standard install:")
    print(f"  pip install {output_dir}/*.whl")
    print()
    print(f"  # Offline install:")
    print(f"  pip install --no-index --find-links {output_dir} pypasreportergui")

    return 0


if __name__ == "__main__":
    sys.exit(main())
