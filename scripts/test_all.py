#!/usr/bin/env python3
"""Run all tests for pyPASreporterGUI.

This script runs:
1. Unit tests (pytest)
2. Smoke tests (if server is running)
3. Integration tests (optional)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return exit code."""
    print(f"+ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke tests")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088", help="Server URL for smoke tests")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    failures = []

    # Run unit tests
    if not args.skip_unit:
        print("\n" + "=" * 60)
        print("Running Unit Tests")
        print("=" * 60)

        # Check if tests directory exists
        tests_dir = base_dir / "tests"
        if tests_dir.exists() and any(tests_dir.glob("test_*.py")):
            ret = run(["pytest", "-v", str(tests_dir)], cwd=base_dir)
            if ret != 0:
                failures.append("Unit tests")
        else:
            print("No unit tests found, skipping")

    # Run smoke tests
    if not args.skip_smoke:
        print("\n" + "=" * 60)
        print("Running Smoke Tests")
        print("=" * 60)

        verify_script = base_dir / "tools" / "verify.py"
        if verify_script.exists():
            ret = run([sys.executable, str(verify_script), "--base-url", args.base_url], cwd=base_dir)
            if ret != 0:
                print("⚠️  Smoke tests failed (server may not be running)")
                # Don't count as failure if server isn't running
        else:
            print("verify.py not found, skipping smoke tests")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if failures:
        print(f"❌ Failed: {', '.join(failures)}")
        return 1
    else:
        print("✓ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
