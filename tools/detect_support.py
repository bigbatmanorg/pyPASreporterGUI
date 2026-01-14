#!/usr/bin/env python3
"""Detect Superset features and compatibility.

This script analyzes a Superset checkout to detect:
- Extension support
- Feature flags
- Required dependencies

Used by pin_superset.py when scanning for compatible commits.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def collect_files(root: Path, globs: Iterable[str]) -> list[Path]:
    """Collect files matching glob patterns."""
    files: set[Path] = set()
    for pattern in globs:
        for path in root.rglob(pattern):
            if path.is_file():
                files.add(path)
    return sorted(files)


def search_with_rg(patterns: list[str], root: Path, globs: list[str], ignore_case: bool) -> list[Path]:
    """Search using ripgrep (fast)."""
    matches: set[Path] = set()
    rg = shutil.which("rg")
    if not rg:
        return []

    for pattern in patterns:
        cmd = [rg, "--files-with-matches", "--no-messages"]
        if ignore_case:
            cmd.append("-i")
        for glob in globs:
            cmd.extend(["-g", glob])
        cmd.append(pattern)
        cmd.append(str(root))
        result = run(cmd, check=False)
        if result.stdout:
            for line in result.stdout.splitlines():
                matches.add(Path(line))
    return sorted(matches)


def search_with_python(patterns: list[str], root: Path, globs: list[str], ignore_case: bool) -> list[Path]:
    """Search using Python (fallback)."""
    files = collect_files(root, globs)
    matches: set[Path] = set()
    flags = re.IGNORECASE if ignore_case else 0
    regexes = [re.compile(p, flags=flags) for p in patterns]

    for path in files:
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(r.search(data) for r in regexes):
            matches.add(path)
    return sorted(matches)


def search(patterns: list[str], root: Path, globs: list[str], ignore_case: bool = False) -> list[Path]:
    """Search for patterns in files matching globs."""
    matches = search_with_rg(patterns, root, globs, ignore_case)
    if matches:
        return matches
    return search_with_python(patterns, root, globs, ignore_case)


def extract_feature_flags(repo_root: Path) -> list[str]:
    """Extract feature flag names from Superset config files."""
    candidates = []
    config_paths = [
        repo_root / "superset" / "config.py",
        repo_root / "superset" / "constants.py",
        repo_root / "superset" / "default_config.py",
    ]

    # Look for feature flag patterns
    patterns = [
        re.compile(r"['\"]([A-Z0-9_]*EXTENSION[A-Z0-9_]*)['\"]"),
        re.compile(r"['\"]([A-Z0-9_]*DUCKDB[A-Z0-9_]*)['\"]"),
        re.compile(r"['\"]([A-Z_]*ENABLE_[A-Z_]+)['\"]"),
    ]

    for path in config_paths:
        if not path.exists():
            continue
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in patterns:
            candidates.extend(pattern.findall(data))

    return sorted(set(candidates))


def detect_support(repo_root: Path) -> dict:
    """Detect Superset features and compatibility.

    Returns a dict with:
    - signals: detected features and their locations
    - missing: features that weren't detected
    - feature_flags: available feature flags
    """
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    code_globs = [
        "superset/**/*.py",
        "superset_core/**/*.py",
        "superset-frontend/**/*.ts",
        "superset-frontend/**/*.tsx",
        "superset-frontend/**/*.js",
        "superset-frontend/**/*.jsx",
    ]

    # Check for various features
    signals = {
        "flask_app": search([r"create_app", r"Flask\("], repo_root, ["superset/**/*.py"]),
        "sqlalchemy": search([r"SQLAlchemy", r"SQLALCHEMY_DATABASE_URI"], repo_root, ["superset/**/*.py"]),
        "duckdb_mentions": search([r"duckdb", r"DuckDB"], repo_root, code_globs, ignore_case=True),
        "extensions_path": search([r"EXTENSIONS_PATH"], repo_root, code_globs),
        "extension_registry": search(
            [r"ExtensionRegistry", r"ExtensionsRegistry", r"extensionsRegistry"],
            repo_root,
            code_globs,
        ),
        "app_name_config": search([r"APP_NAME\s*="], repo_root, ["superset/**/*.py"]),
        "app_icon_config": search([r"APP_ICON\s*="], repo_root, ["superset/**/*.py"]),
        "favicons_config": search([r"FAVICONS\s*="], repo_root, ["superset/**/*.py"]),
    }

    # Check which signals are missing
    missing = [name for name, files in signals.items() if not files]

    # Extract feature flags
    feature_flags = extract_feature_flags(repo_root)

    return {
        "signals": {name: [str(p) for p in files] for name, files in signals.items()},
        "missing": missing,
        "feature_flags": feature_flags,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="superset-src",
                        help="Path to Superset repo")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    result = detect_support(repo_root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Superset Compatibility Check")
        print("=" * 40)
        for name, files in result["signals"].items():
            status = "✓ found" if files else "✗ missing"
            print(f"  {name}: {status}")

        if result["feature_flags"]:
            print("\nDetected feature flags:")
            for flag in result["feature_flags"]:
                print(f"  - {flag}")

        if result["missing"]:
            print(f"\nMissing signals: {', '.join(result['missing'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
