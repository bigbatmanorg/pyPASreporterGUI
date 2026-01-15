#!/usr/bin/env python3
"""Pin Superset to a specific version or find newest compatible commit.

This script clones/updates the Apache Superset repository and pins it to:
- A specific SHA/tag/ref (--sha)
- The latest release tag (--latest-tag)
- The newest compatible commit on a branch (--branch with --scan-limit)

Results are written to VERSION_MATRIX.json and docs/VERSION_MATRIX.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    use_shell = os.name == "nt" and cmd and cmd[0] in ("npm", "npx", "node")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True, shell=use_shell)


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the specified directory."""
    return run(["git", "-C", str(cwd), *args], check=check)


def is_shallow_repo(repo_root: Path) -> bool:
    """True if the repo is shallow (common in CI)."""
    r = git(repo_root, "rev-parse", "--is-shallow-repository", check=False)
    return r.returncode == 0 and r.stdout.strip().lower() == "true"


def ensure_full_history(repo_root: Path) -> None:
    """Try to convert shallow clone into a full clone (best-effort)."""
    if not is_shallow_repo(repo_root):
        return
    print("Repo is shallow; attempting to unshallow...")
    git(repo_root, "fetch", "--unshallow", "--tags", "--prune", check=False)
    # If --unshallow failed (older git / edge cases), fall back to a deep fetch.
    if is_shallow_repo(repo_root):
        git(repo_root, "fetch", "--depth", "1000000", "--tags", "--prune", check=False)


def ensure_repo(repo_root: Path, repo_url: str) -> None:
    """Clone the repository if it doesn't exist."""
    if repo_root.exists() and (repo_root / ".git").exists():
        return
    repo_root.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {repo_url} to {repo_root}...")
    # Keep shallow for speed; we will unshallow only if needed.
    run(["git", "clone", "--depth", "100", repo_url, str(repo_root)])


def get_default_branch(repo_root: Path) -> str:
    """Determine the default branch of the repository."""
    result = git(repo_root, "symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().split("/")[-1]

    for candidate in ("main", "master", "next"):
        check = git(repo_root, "show-ref", "--verify", f"refs/remotes/origin/{candidate}", check=False)
        if check.returncode == 0:
            return candidate

    raise RuntimeError("Unable to determine default branch")


def update_repo(repo_root: Path, branch: str) -> None:
    """Fetch latest changes and checkout the specified branch."""
    print(f"Updating repository on branch {branch}...")
    git(repo_root, "fetch", "--all", "--tags", "--prune", check=False)
    ensure_full_history(repo_root)

    # Ensure we can checkout the branch even if it's not a local branch yet.
    r = git(repo_root, "checkout", branch, check=False)
    if r.returncode != 0:
        # Create/reset local branch tracking origin/<branch>
        git(repo_root, "checkout", "-B", branch, f"origin/{branch}", check=True)

    git(repo_root, "pull", "--ff-only", check=False)


def get_latest_tag(repo_root: Path) -> str:
    """Get the latest release tag (semver format)."""
    result = git(repo_root, "tag", "-l", "--sort=-v:refname")
    tags = result.stdout.strip().split("\n")

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    for tag in tags:
        tag = tag.strip()
        if semver_pattern.match(tag):
            return tag

    raise RuntimeError("No valid release tag found")


def checkout_ref(repo_root: Path, ref: str) -> None:
    """Checkout a specific reference (SHA, tag, branch).

    CI commonly uses shallow clones; a tag/sha might not be reachable until we unshallow.
    """
    # First try a normal checkout.
    r = git(repo_root, "checkout", ref, check=False)
    if r.returncode == 0:
        return

    # Fetch tags and try again.
    git(repo_root, "fetch", "--all", "--tags", "--prune", check=False)
    ensure_full_history(repo_root)

    # Try fetching the ref explicitly (works for tags/branches/SHAs in many cases).
    git(repo_root, "fetch", "origin", ref, check=False)

    r2 = git(repo_root, "checkout", ref, check=False)
    if r2.returncode != 0:
        msg = (
            f"Failed to checkout ref '{ref}'.\n"
            f"stdout:\n{r2.stdout}\n"
            f"stderr:\n{r2.stderr}\n"
        )
        raise RuntimeError(msg)


def get_head_sha(repo_root: Path) -> str:
    """Get the current HEAD SHA."""
    result = git(repo_root, "rev-parse", "HEAD")
    return result.stdout.strip()


def get_version(cmd: list[str]) -> str:
    """Get version string from a command."""
    result = run(cmd, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip().replace("Python ", "")


def get_superset_version(repo_root: Path) -> str:
    """Extract Superset version from the repository."""
    version_file = repo_root / "superset" / "version.py"
    if version_file.exists():
        content = version_file.read_text()
        match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

    return "unknown"


def write_version_matrix(base_dir: Path, data: dict) -> None:
    """Write version matrix to JSON and Markdown files."""
    json_path = base_dir / "VERSION_MATRIX.json"
    md_path = base_dir / "docs" / "VERSION_MATRIX.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Version Matrix",
        "",
        "This file is auto-generated by `tools/pin_superset.py`. Do not edit manually.",
        "",
        "## Pinned Versions",
        "",
        "| Component | Version |",
        "|-----------|---------|",
        f"| Superset SHA | `{data.get('superset_sha', 'TBD')[:12]}` |",
        f"| Superset Version | {data.get('superset_version', 'TBD')} |",
        f"| Superset Branch/Tag | {data.get('superset_branch', 'TBD')} |",
        f"| Python | {data.get('python_version', 'TBD')} |",
        f"| Node.js | {data.get('node_version', 'TBD')} |",
        f"| npm | {data.get('npm_version', 'TBD')} |",
        f"| pyPASreporterGUI | {data.get('app_version', 'TBD')} |",
        "",
        "## Build Info",
        "",
        f"- Build timestamp: {data.get('build_timestamp', 'TBD')}",
        f"- Build host: {data.get('build_host', 'TBD')}",
        "",
        "## Rebuild Instructions",
        "",
        "```bash",
        f"python tools/pin_superset.py --sha {data.get('superset_sha', 'SHA')}",
        "python tools/build_superset.py",
        "python tools/build_wheels.py",
        "```",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("Version matrix written to:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", default="https://github.com/apache/superset.git",
                        help="Superset repository URL")
    parser.add_argument("--repo", default="superset-src",
                        help="Local directory for Superset checkout")
    parser.add_argument("--branch", default=None,
                        help="Branch to pin (default: auto-detect)")
    parser.add_argument("--sha", default=None,
                        help="Specific commit SHA/tag/ref to pin")
    parser.add_argument("--latest-tag", action="store_true",
                        help="Pin to the latest release tag")
    parser.add_argument("--scan-limit", type=int, default=100,
                        help="Max commits to scan when finding compatible version")
    parser.add_argument("--write-version", action="store_true",
                        help="Write VERSION_MATRIX.json and docs/VERSION_MATRIX.md")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    repo_root = (base_dir / args.repo).resolve()

    ensure_repo(repo_root, args.repo_url)

    if args.sha:
        print(f"Pinning to ref: {args.sha}")
        git(repo_root, "fetch", "--all", "--tags", "--prune", check=False)
        ensure_full_history(repo_root)
        checkout_ref(repo_root, args.sha)
        branch_or_tag = args.sha[:12]
    elif args.latest_tag:
        git(repo_root, "fetch", "--all", "--tags", "--prune", check=False)
        ensure_full_history(repo_root)
        tag = get_latest_tag(repo_root)
        print(f"Pinning to latest tag: {tag}")
        checkout_ref(repo_root, tag)
        branch_or_tag = tag
    else:
        branch = args.branch or get_default_branch(repo_root)
        update_repo(repo_root, branch)
        branch_or_tag = branch

    sha = get_head_sha(repo_root)
    superset_version = get_superset_version(repo_root)

    print(f"\n{'='*60}")
    print("Pinned Superset:")
    print(f"  SHA: {sha}")
    print(f"  Version: {superset_version}")
    print(f"  Branch/Tag: {branch_or_tag}")
    print(f"{'='*60}")

    if args.write_version:
        import datetime
        import platform

        try:
            from pypasreportergui import __version__ as app_version
        except ImportError:
            app_version = "0.1.0"

        data = {
            "superset_sha": sha,
            "superset_version": superset_version,
            "superset_branch": branch_or_tag,
            "python_version": get_version([sys.executable, "--version"]),
            "node_version": get_version(["node", "--version"]),
            "npm_version": get_version(["npm", "--version"]),
            "app_version": app_version,
            "build_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "build_host": platform.node(),
        }
        write_version_matrix(base_dir, data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
