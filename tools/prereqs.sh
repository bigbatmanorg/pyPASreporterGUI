#!/usr/bin/env bash
# pyPASreporterGUI Prerequisites Script
# Sets up the development environment with Python, Node.js, and required packages
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_VERSION="${PY_VERSION:-3.11}"
CONDA_ENV="${CONDA_ENV:-pypasreportergui}"
USE_CONDA="${USE_CONDA:-0}"
PYTHON_BIN="${PYTHON_BIN:-}"

log() {
    echo "[prereqs] $*"
}

error() {
    echo "[prereqs] ERROR: $*" >&2
    exit 1
}

# Check if running on supported OS
check_os() {
    case "$(uname -s)" in
        Linux*)     OS=Linux;;
        Darwin*)    OS=macOS;;
        MINGW*|MSYS*|CYGWIN*) OS=Windows;;
        *)          OS="Unknown";;
    esac
    log "Detected OS: $OS"
}

# Conda environment setup (optional)
setup_conda() {
    if [[ "${USE_CONDA}" == "0" ]]; then
        return
    fi

    if ! command -v conda >/dev/null 2>&1; then
        error "conda requested but not found; install conda or unset USE_CONDA"
    fi

    # shellcheck disable=SC1091
    eval "$(conda shell.bash hook)"

    if ! conda env list | grep -q "^${CONDA_ENV}\s"; then
        log "Creating conda env ${CONDA_ENV} (python=${PY_VERSION}, nodejs=20)"
        conda create -y -n "${CONDA_ENV}" "python=${PY_VERSION}" nodejs=20 git pip
    fi

    log "Activating conda env ${CONDA_ENV}"
    conda activate "${CONDA_ENV}"
}

# Find Python interpreter
find_python() {
    if [[ -n "${PYTHON_BIN}" ]]; then
        return
    fi

    # Try version-specific first
    PYTHON_BIN="$(command -v "python${PY_VERSION}" 2>/dev/null || true)"

    # Fall back to python3
    if [[ -z "${PYTHON_BIN}" ]]; then
        PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
    fi

    # Fall back to python
    if [[ -z "${PYTHON_BIN}" ]]; then
        PYTHON_BIN="$(command -v python 2>/dev/null || true)"
    fi

    if [[ -z "${PYTHON_BIN}" ]]; then
        error "No Python interpreter found. Install Python ${PY_VERSION}+ first."
    fi

    log "Python selected: ${PYTHON_BIN}"

    # Verify version
    PY_ACTUAL=$("${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log "Python version: ${PY_ACTUAL}"
}

# Install uv package manager
install_uv() {
    if command -v uv >/dev/null 2>&1; then
        log "uv already installed: $(uv --version)"
        return
    fi

    log "Installing uv (user)"
    "${PYTHON_BIN}" -m pip install --upgrade pip
    "${PYTHON_BIN}" -m pip install --user uv
    export PATH="${HOME}/.local/bin:${PATH}"

    if ! command -v uv >/dev/null 2>&1; then
        # Try alternate installation
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="${HOME}/.cargo/bin:${PATH}"
    fi
}

# Create virtual environment
create_venv() {
    if [[ -d "${ROOT}/.venv" ]]; then
        log ".venv already exists"
        return
    fi

    if command -v uv >/dev/null 2>&1; then
        log "Creating .venv with uv"
        uv venv --python "${PYTHON_BIN}" "${ROOT}/.venv"
    else
        log "Creating .venv with python -m venv"
        "${PYTHON_BIN}" -m venv "${ROOT}/.venv"
    fi
}

# Ensure npm is new enough
ensure_npm() {
    local min="10.8.2"

    if ! command -v npm >/dev/null 2>&1; then
        error "npm not found. Install Node.js 18+ first."
    fi

    local current
    current=$(npm --version 2>/dev/null || echo "0.0.0")

    if [[ "$(printf '%s\n%s' "$min" "$current" | sort -V | head -n1)" == "$min" ]]; then
        log "npm ${current} satisfies >= ${min}"
        return
    fi

    log "Upgrading npm to ${min} in ${HOME}/.npm-global"
    npm config set prefix "${HOME}/.npm-global"
    npm install -g "npm@${min}" --prefix "${HOME}/.npm-global"
    export PATH="${HOME}/.npm-global/bin:${PATH}"
}

# Check Node.js version
check_node() {
    if ! command -v node >/dev/null 2>&1; then
        error "node not found. Install Node.js 18+ first."
    fi

    local node_version
    node_version=$(node --version | sed 's/v//')
    log "Node.js version: ${node_version}"

    local major
    major=$(echo "${node_version}" | cut -d. -f1)
    if [[ "${major}" -lt 18 ]]; then
        error "Node.js 18+ required, found ${node_version}"
    fi
}

# Install Python packages in venv
install_packages() {
    log "Activating venv and installing packages"

    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"

    local PKG_INSTALLER="python -m pip"
    if command -v uv >/dev/null 2>&1; then
        PKG_INSTALLER="uv pip"
        uv pip install --upgrade pip setuptools wheel build
    else
        python -m pip install --upgrade pip setuptools wheel build
    fi

    # Install core dependencies
    ${PKG_INSTALLER} install "duckdb>=0.10.0" "duckdb-engine>=0.10.0"
    ${PKG_INSTALLER} install "typer>=0.9.0" "rich>=13.0.0"
    ${PKG_INSTALLER} install "requests>=2.28.0"

    # Install dev dependencies
    ${PKG_INSTALLER} install "pytest>=7.0.0" "pytest-cov>=4.0.0"
}

# Main
main() {
    log "=== pyPASreporterGUI Prerequisites Setup ==="
    log "Working directory: ${ROOT}"

    check_os
    setup_conda
    find_python
    install_uv
    check_node
    ensure_npm
    create_venv
    install_packages

    log ""
    log "=== Setup Complete ==="
    log ""
    log "To activate the environment:"
    log "  source ${ROOT}/.venv/bin/activate"
    log ""
    log "Next steps:"
    log "  python scripts/build_all.py"
    log ""
}

main "$@"
