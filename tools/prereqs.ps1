# pyPASreporterGUI Prerequisites Script (Windows PowerShell)
# Sets up the development environment with Python, Node.js, and required packages

Param(
    [string]$PythonVersion = "3.11",
    [string]$CondaEnv = "pypasreportergui",
    [switch]$UseConda,
    [string]$PythonBin = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Log($msg) {
    Write-Host "[prereqs] $msg"
}

function Error($msg) {
    Write-Host "[prereqs] ERROR: $msg" -ForegroundColor Red
    exit 1
}

# Conda environment setup (optional)
function Setup-Conda {
    if (-not $UseConda) { return }

    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Error "conda requested but not found; install conda or omit -UseConda"
    }

    & conda shell.powershell hook | Out-String | Invoke-Expression

    $envExists = conda env list | Select-String "^$CondaEnv\s"
    if (-not $envExists) {
        Log "Creating conda env $CondaEnv (python=$PythonVersion, nodejs=20)"
        conda create -y -n $CondaEnv "python=$PythonVersion" nodejs=20 git pip
    }

    Log "Activating conda env $CondaEnv"
    conda activate $CondaEnv
}

# Find Python interpreter
function Find-Python {
    if ($PythonBin) { return $PythonBin }

    # Try version-specific first
    $candidate = Get-Command "python$PythonVersion" -ErrorAction SilentlyContinue
    if ($candidate) {
        return $candidate.Source
    }

    # Try py launcher
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return "py -$PythonVersion"
    }

    # Fall back to python
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    Error "No Python interpreter found. Install Python $PythonVersion+ first."
}

# Install uv package manager
function Install-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Log "uv already installed: $(uv --version)"
        return
    }

    Log "Installing uv"
    & $script:PythonExe -m pip install --upgrade pip
    & $script:PythonExe -m pip install --user uv
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        # Try PowerShell installation
        irm https://astral.sh/uv/install.ps1 | iex
        $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    }
}

# Create virtual environment
function Create-Venv {
    $venvPath = "$Root\.venv"

    if (Test-Path $venvPath) {
        Log ".venv already exists"
        return
    }

    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Log "Creating .venv with uv"
        uv venv --python $script:PythonExe $venvPath
    } else {
        Log "Creating .venv with python -m venv"
        & $script:PythonExe -m venv $venvPath
    }
}

# Ensure npm is new enough
function Ensure-Npm {
    param([string]$Min = "10.8.2")

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Error "npm not found. Install Node.js 18+ first."
    }

    $current = ""
    try { $current = (npm --version) 2>$null } catch {}

    if ($current) {
        try {
            $cmp = [version]$current -ge [version]$Min
            if ($cmp) {
                Log "npm $current satisfies >= $Min"
                return
            }
        } catch {
            # Version comparison failed, try upgrade anyway
        }
    }

    Log "Upgrading npm to $Min in $env:USERPROFILE\.npm-global"
    npm config set prefix "$env:USERPROFILE\.npm-global"
    npm install -g "npm@$Min" --prefix "$env:USERPROFILE\.npm-global"
    $env:PATH = "$env:USERPROFILE\.npm-global\bin;$env:PATH"
}

# Check Node.js version
function Check-Node {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Error "node not found. Install Node.js 18+ first."
    }

    $nodeVersion = (node --version) -replace 'v', ''
    Log "Node.js version: $nodeVersion"

    $major = [int]($nodeVersion.Split('.')[0])
    if ($major -lt 18) {
        Error "Node.js 18+ required, found $nodeVersion"
    }
}

# Install Python packages in venv
function Install-Packages {
    Log "Activating venv and installing packages"

    . "$Root\.venv\Scripts\Activate.ps1"

    $pkgInstaller = { param($args) python -m pip @args }
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv pip install --upgrade pip setuptools wheel build
        $pkgInstaller = { param($args) uv pip @args }
    } else {
        python -m pip install --upgrade pip setuptools wheel build
    }

    # Install core dependencies
    & $pkgInstaller "install" "duckdb>=0.10.0" "duckdb-engine>=0.10.0"
    & $pkgInstaller "install" "typer>=0.9.0" "rich>=13.0.0"
    & $pkgInstaller "install" "requests>=2.28.0"

    # Install dev dependencies
    & $pkgInstaller "install" "pytest>=7.0.0" "pytest-cov>=4.0.0"
}

# Main
function Main {
    Log "=== pyPASreporterGUI Prerequisites Setup ==="
    Log "Working directory: $Root"

    Setup-Conda

    $script:PythonExe = Find-Python
    Log "Python selected: $script:PythonExe"

    Install-Uv
    Check-Node
    Ensure-Npm
    Create-Venv
    Install-Packages

    Log ""
    Log "=== Setup Complete ==="
    Log ""
    Log "To activate the environment:"
    Log "  .\.venv\Scripts\Activate.ps1"
    Log ""
    Log "Next steps:"
    Log "  python scripts\build_all.py"
    Log ""
}

Main
