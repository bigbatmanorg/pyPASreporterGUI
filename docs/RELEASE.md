# pyPASreporterGUI Release Guide

This document describes how to create releases and manage versions.

## Version Numbering

pyPASreporterGUI uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes or major UI/UX changes
- **MINOR**: New features, compatible with previous versions
- **PATCH**: Bug fixes, security updates

Example: `1.2.3` = Major.Minor.Patch

---

## Files That Contain Version

| File | Line | Update Method |
|------|------|---------------|
| `pyproject.toml` | `version = "X.Y.Z"` | Manual |
| `src/pypasreportergui/__init__.py` | `__version__ = "X.Y.Z"` | Manual |
| `VERSION_MATRIX.json` | `app_version` | Auto-generated |

---

## Release Checklist

### 1. Update Version Numbers

```bash
# Edit pyproject.toml
version = "1.2.0"

# Edit src/pypasreportergui/__init__.py
__version__ = "1.2.0"
```

### 2. Update Superset Pin (if needed)

```bash
# Check for new Superset releases
cd superset-src
git fetch --tags
git tag -l '4.*' | sort -V | tail -5

# Pin to specific version
python tools/pin_superset.py --sha <latest-stable-sha> --write-version
```

### 3. Build Everything

```bash
# Full build
python scripts/build_all.py

# Or step by step:
python tools/build_superset.py
python tools/build_wheels.py
```

### 4. Run Tests

```bash
# Unit tests
pytest tests/

# Start server and run smoke tests
pypasreportergui run --port 8088 &
sleep 30
python tools/verify.py
```

### 5. Build Windows Executable (on Windows)

```powershell
.\tools\build_exe.ps1
```

### 6. Create Git Tag

```bash
git add -A
git commit -m "Release v1.2.0"
git tag -a v1.2.0 -m "pyPASreporterGUI v1.2.0"
git push origin main --tags
```

---

## Building Against New Superset

When Apache Superset releases a new version:

### 1. Evaluate Compatibility

```bash
# Pin to new version
python tools/pin_superset.py --latest-tag --write-version

# Check for breaking changes
python tools/detect_support.py
```

### 2. Update Dependencies

Review `pyproject.toml` dependencies if Superset's requirements changed.

### 3. Test Thoroughly

```bash
# Fresh build
rm -rf superset-src/.venv
python scripts/build_all.py --latest-tag

# Run all tests
python scripts/test_all.py
```

### 4. Update Documentation

- Update `docs/VERSION_MATRIX.md` (auto-generated)
- Note any breaking changes in release notes

---

## Release Artifacts

A complete release includes:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Source | GitHub release | Development |
| Wheel | `dist/wheels/pyPASreporterGUI-*.whl` | pip install |
| Superset Wheel | `dist/wheels/apache_superset-*.whl` | Dependency |
| Windows Exe | `dist/exe/pyPASreporterGUI/` | Windows users |
| VERSION_MATRIX | `VERSION_MATRIX.json` | Reproducibility |

### Creating a Release Archive

```bash
# Create release directory
mkdir -p release/v1.2.0

# Copy artifacts
cp dist/wheels/*.whl release/v1.2.0/
cp VERSION_MATRIX.json release/v1.2.0/
cp -r docs release/v1.2.0/

# On Windows: copy exe
# copy dist\exe\pyPASreporterGUI release\v1.2.0\

# Create archive
cd release
tar -czvf pyPASreporterGUI-v1.2.0.tar.gz v1.2.0/
```

---

## Reproducible Builds

To reproduce an exact build:

```bash
# Get VERSION_MATRIX.json from release
# Extract superset_sha

python tools/pin_superset.py --sha <superset_sha_from_matrix>
python tools/build_superset.py --verify-sha
python tools/build_wheels.py
```

---

## Hotfix Releases

For urgent bug fixes:

### 1. Create Hotfix Branch

```bash
git checkout v1.2.0  # From last release tag
git checkout -b hotfix/1.2.1
```

### 2. Apply Fix

Make minimal changes to fix the issue.

### 3. Bump Patch Version

```bash
# Update version to 1.2.1
```

### 4. Test and Release

```bash
python tools/build_wheels.py --app-only
pytest tests/
git tag -a v1.2.1 -m "Hotfix v1.2.1"
```

### 5. Merge Back

```bash
git checkout main
git merge hotfix/1.2.1
```

---

## Publishing to PyPI (Future)

When ready for public release:

```bash
# Build distribution
python -m build

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

---

## Version Matrix History

Keep track of release history:

| pyPASreporterGUI | Superset | Python | Notes |
|------------------|----------|--------|-------|
| 0.1.0 | 4.0.0 | 3.10-3.12 | Initial release |

---

## Changelog Format

Use [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.2.0] - 2024-01-15

### Added
- DuckDB connection helper CLI
- Custom branding support

### Changed
- Updated to Superset 4.0.0

### Fixed
- Config generation on Windows paths
```
