#!/usr/bin/env python3
"""Build complete pyPASreporterGUI distribution.

This is the main orchestration script that runs the full build pipeline:
1. Check prerequisites
2. Pin Superset (clone/update)
3. Build Superset (frontend + backend)
4. Build wheels (Superset + pyPASreporterGUI)
5. Build Windows executable (if on Windows)
6. Run verification

Usage:
    python scripts/build_all.py [options]

Options:
    --skip-pin          Skip pinning Superset (use existing checkout)
    --skip-frontend     Skip frontend build (use existing assets)
    --skip-wheels       Skip building wheel packages
    --skip-exe          Skip building Windows executable
    --skip-verify       Skip verification tests
    --latest-tag        Pin to latest Superset release tag
    --sha SHA           Pin to specific Superset commit
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> int:
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def venv_python(base_dir: Path) -> str:
    """Get the path to the venv Python interpreter."""
    if os.name == "nt":
        return str(base_dir / ".venv" / "Scripts" / "python.exe")
    return str(base_dir / ".venv" / "bin" / "python")


def check_prerequisites(base_dir: Path) -> bool:
    """Check that all prerequisites are available."""
    print("\n" + "=" * 60)
    print("Checking Prerequisites")
    print("=" * 60)

    issues = []

    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✓ Python: {result.stdout.strip()}")
    except Exception as e:
        issues.append(f"Python not available: {e}")

    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, shell=(os.name == "nt"))
        print(f"✓ Node.js: {result.stdout.strip()}")
    except Exception:
        issues.append("Node.js not found. Install Node.js 18+")

    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, shell=(os.name == "nt"))
        print(f"✓ npm: {result.stdout.strip()}")
    except Exception:
        issues.append("npm not found. Install Node.js with npm")

    # Check Git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, shell=(os.name == "nt"))
        print(f"✓ Git: {result.stdout.strip()}")
    except Exception:
        issues.append("git not found. Install Git")

    # Check venv
    venv_dir = base_dir / ".venv"
    if venv_dir.exists():
        print(f"✓ Virtual environment: {venv_dir}")
    else:
        issues.append(f"Virtual environment not found at {venv_dir}")
        issues.append("Run: bash tools/prereqs.sh  (or .\\tools\\prereqs.ps1 on Windows)")

    if issues:
        print("\n❌ Prerequisites check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("\n✓ All prerequisites satisfied")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-pin", action="store_true", help="Skip pinning Superset")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build")
    parser.add_argument("--skip-wheels", action="store_true", help="Skip building wheels")
    parser.add_argument("--skip-exe", action="store_true", help="Skip building executable")
    parser.add_argument("--skip-verify", action="store_true", help="Skip verification")
    parser.add_argument("--latest-tag", action="store_true", help="Pin to latest release tag")
    parser.add_argument("--sha", help="Pin to specific commit SHA")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    python_exe = venv_python(base_dir)

    # Check prerequisites
    if not check_prerequisites(base_dir):
        return 1

    # Step 1: Pin Superset
    if not args.skip_pin:
        cmd = [python_exe, "tools/pin_superset.py", "--write-version"]
        if args.latest_tag:
            cmd.append("--latest-tag")
        elif args.sha:
            cmd.extend(["--sha", args.sha])
        ret = run(cmd, cwd=base_dir)
        if ret != 0:
            print("❌ Failed to pin Superset")
            return ret
    else:
        print("\n⏭️  Skipping Superset pin (--skip-pin)")

    # Check superset-src exists
    superset_src = base_dir / "superset-src"
    if not superset_src.exists():
        print("❌ superset-src not found. Run without --skip-pin first.")
        return 1

    # Step 2: Build Superset
    cmd = [python_exe, "tools/build_superset.py"]
    if args.skip_frontend:
        cmd.append("--skip-frontend")
    ret = run(cmd, cwd=base_dir)
    if ret != 0:
        print("❌ Failed to build Superset")
        return ret

    # Step 3: Build wheels
    if not args.skip_wheels:
        ret = run([python_exe, "tools/build_wheels.py"], cwd=base_dir)
        if ret != 0:
            print("❌ Failed to build wheels")
            return ret
    else:
        print("\n⏭️  Skipping wheel build (--skip-wheels)")

    # Step 4: Build Windows executable (Windows only)
    if os.name == "nt" and not args.skip_exe:
        exe_script = base_dir / "tools" / "build_exe.ps1"
        if exe_script.exists():
            ret = run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(exe_script)], cwd=base_dir)
            if ret != 0:
                print("⚠️  Windows executable build failed (non-fatal)")
        else:
            print("⚠️  build_exe.ps1 not found, skipping exe build")
    elif not args.skip_exe:
        print("\n⏭️  Skipping exe build (not on Windows)")

    # Step 5: Verification
    if not args.skip_verify:
        print("\n" + "=" * 60)
        print("Running Verification")
        print("=" * 60)
        print("Note: Full verification requires a running server.")
        print("Start with: pypasreportergui run --port 8088")
        print("Then run: python tools/verify.py")
    else:
        print("\n⏭️  Skipping verification (--skip-verify)")

    # Summary
    print(f"\n{'='*60}")
    print("BUILD COMPLETE")
    print(f"{'='*60}")

    wheels_dir = base_dir / "dist" / "wheels"
    exe_dir = base_dir / "dist" / "exe"

    if wheels_dir.exists():
        print("\n📦 Wheel packages:")
        for wheel in sorted(wheels_dir.glob("*.whl")):
            size_mb = wheel.stat().st_size / (1024 * 1024)
            print(f"   {wheel.name} ({size_mb:.1f} MB)")

    if exe_dir.exists():
        print("\n🖥️  Executables:")
        for exe in sorted(exe_dir.glob("*.exe")):
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"   {exe.name} ({size_mb:.1f} MB)")

    print("\n🚀 Next steps:")
    print("   1. Start the app:")
    print("      pypasreportergui run --port 8088")
    print("   2. Open browser:")
    print("      http://127.0.0.1:8088")
    print("   3. Login with admin/admin")
    print()
    print("   For offline installation:")
    print(f"      pip install --no-index --find-links {wheels_dir} pyPASreporterGUI")

    return 0


if __name__ == "__main__":
    sys.exit(main())
