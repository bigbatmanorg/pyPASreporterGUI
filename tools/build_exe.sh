#!/bin/bash
# Build Linux executable for pyPASreporterGUI
# This script creates a standalone binary using PyInstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

log() {
    echo "[build_exe] $1"
}

error() {
    echo "[build_exe] ERROR: $1" >&2
    exit 1
}

cd "$ROOT"

# Check for required files
if [[ ! -d "dist/wheels" ]]; then
    error "dist/wheels not found. Run 'python scripts/build_all.py' first"
fi

# Find wheel (case-insensitive)
APP_WHEEL=$(find dist/wheels -maxdepth 1 -iname "pypasreportergui*.whl" 2>/dev/null | head -1)
if [[ -z "$APP_WHEEL" ]]; then
    error "pyPASreporterGUI wheel not found in dist/wheels"
fi

log "Found app wheel: $(basename "$APP_WHEEL")"

# Activate venv if it exists
if [[ -d ".venv" ]]; then
    log "Activating virtual environment"
    source .venv/bin/activate
fi

# Verify pyinstaller is available
if ! command -v pyinstaller &> /dev/null; then
    log "Installing PyInstaller"
    pip install pyinstaller
fi

# Verify our package is installed
log "Verifying pypasreportergui installation"
python -c "from pypasreportergui import __version__; print(f'pyPASreporterGUI version: {__version__}')"

# Create output directory
EXE_DIR="dist/exe"
mkdir -p "$EXE_DIR"

# Clean previous builds
log "Cleaning previous builds"
rm -rf build/pyPASreporterGUI dist/pyPASreporterGUI

# Build with PyInstaller using spec file
SPEC_FILE="$ROOT/tools/build_exe.spec"
if [[ -f "$SPEC_FILE" ]]; then
    log "Building executable with PyInstaller using spec file"
    pyinstaller --clean --noconfirm "$SPEC_FILE"
else
    error "Spec file not found: $SPEC_FILE"
fi

# Move output to dist/exe
if [[ -d "dist/pyPASreporterGUI" ]]; then
    log "Moving executable to $EXE_DIR"
    rm -rf "$EXE_DIR/pyPASreporterGUI"
    mv dist/pyPASreporterGUI "$EXE_DIR/"
    
    # Make main executable file executable
    chmod +x "$EXE_DIR/pyPASreporterGUI/pyPASreporterGUI"
    
    log "Build complete!"
    log "Executable: $EXE_DIR/pyPASreporterGUI/pyPASreporterGUI"
    
    # Show size
    SIZE=$(du -sh "$EXE_DIR/pyPASreporterGUI" | cut -f1)
    log "Total size: $SIZE"
else
    error "Build output not found"
fi
