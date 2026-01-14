# Build Windows executable for pyPASreporterGUI
# This script creates a standalone .exe using PyInstaller

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Log($msg) {
    Write-Host "[build_exe] $msg"
}

function Error($msg) {
    Write-Host "[build_exe] ERROR: $msg" -ForegroundColor Red
    exit 1
}

# Ensure we're in the right directory
Set-Location $Root

# Check for required files
if (-not (Test-Path "dist/wheels")) {
    Error "dist/wheels not found. Run 'python scripts/build_all.py' first"
}

$wheelsDir = "dist/wheels"
$appWheel = Get-ChildItem "$wheelsDir/pyPASreporterGUI*.whl" | Select-Object -First 1
if (-not $appWheel) {
    Error "pyPASreporterGUI wheel not found in $wheelsDir"
}

Log "Found app wheel: $($appWheel.Name)"

# Create build environment
$buildEnv = "$Root/.build_exe_env"
if (Test-Path $buildEnv) {
    Log "Removing existing build environment"
    Remove-Item -Recurse -Force $buildEnv
}

Log "Creating clean build environment"
python -m venv $buildEnv
. "$buildEnv/Scripts/Activate.ps1"

# Install from wheelhouse (offline-style)
Log "Installing packages from wheelhouse"
pip install --upgrade pip setuptools wheel
pip install pyinstaller

# Install all wheels from dist/wheels
$wheels = Get-ChildItem "$wheelsDir/*.whl"
foreach ($wheel in $wheels) {
    Log "Installing: $($wheel.Name)"
    pip install $wheel.FullName
}

# Check installation
Log "Verifying installation"
python -c "from pypasreportergui import __version__; print(f'pyPASreporterGUI version: {__version__}')"

# Create output directory
$exeDir = "dist/exe"
if (-not (Test-Path $exeDir)) {
    New-Item -ItemType Directory -Path $exeDir | Out-Null
}

# Build with PyInstaller
Log "Building executable with PyInstaller"

$specFile = "$Root/tools/build_exe.spec"
if (Test-Path $specFile) {
    # Use existing spec file
    pyinstaller --clean --noconfirm $specFile
} else {
    # Generate spec on the fly
    $brandingStatic = "$Root/src/pypasreportergui/branding/static"
    
    pyinstaller --clean --noconfirm `
        --name "pyPASreporterGUI" `
        --onedir `
        --console `
        --add-data "$brandingStatic;pypasreportergui/branding/static" `
        --hidden-import "pypasreportergui" `
        --hidden-import "pypasreportergui.cli" `
        --hidden-import "pypasreportergui.runtime" `
        --hidden-import "pypasreportergui.branding" `
        --hidden-import "pypasreportergui.branding.blueprint" `
        --hidden-import "superset" `
        --hidden-import "duckdb" `
        --hidden-import "duckdb_engine" `
        --hidden-import "typer" `
        --hidden-import "rich" `
        --collect-all "superset" `
        --collect-data "superset" `
        --distpath $exeDir `
        --workpath "$Root/build/pyinstaller" `
        --specpath "$Root/build" `
        "$Root/src/pypasreportergui/cli.py"
}

# Check output
$exePath = "$exeDir/pyPASreporterGUI/pyPASreporterGUI.exe"
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Log "SUCCESS: Built executable"
    Log "  Path: $exePath"
    Log "  Size: $([math]::Round($size, 1)) MB"
    
    # Test the executable
    Log "Testing executable..."
    & $exePath --version
} else {
    Error "Executable not found at expected path: $exePath"
}

# Cleanup
Log "Cleaning up build environment"
deactivate
# Remove-Item -Recurse -Force $buildEnv

Log "Build complete!"
Log ""
Log "To run:"
Log "  $exePath run --port 8088"
