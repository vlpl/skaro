#!/bin/sh
# ──────────────────────────────────────────────────────────────
# Skaro installer for Linux & macOS
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/skarodev/skaro/main/install.sh | sh
#
# What it does:
#   1. Finds Python 3.11+
#   2. Creates isolated venv at ~/.skaro/venv
#   3. Installs (or upgrades) the 'skaro' package from PyPI
#   4. Symlinks 'skaro' binary into ~/.local/bin
#
# Uninstall:
#   rm -rf ~/.skaro/venv ~/.local/bin/skaro
# ──────────────────────────────────────────────────────────────
set -e

# ── Config ──────────────────────────────────────
SKARO_HOME="${SKARO_HOME:-$HOME/.skaro}"
VENV_DIR="$SKARO_HOME/venv"
BIN_DIR="${SKARO_BIN:-$HOME/.local/bin}"
PACKAGE="skaro"
MIN_PYTHON_MINOR=11

# ── Colors (if terminal supports them) ──────────
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

info()  { printf "${CYAN}▸${RESET} %s\n" "$1"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$1"; }
warn()  { printf "${YELLOW}⚠${RESET} %s\n" "$1"; }
fail()  { printf "${RED}✗ %s${RESET}\n" "$1" >&2; exit 1; }

# ── Find Python 3.11+ ──────────────────────────
find_python() {
    # Try specific versions first (highest to lowest), then generic names
    for cmd in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -eq 3 ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# ── Check venv module is available ──────────────
check_venv_module() {
    "$1" -m venv --help >/dev/null 2>&1
}

# ── Main ────────────────────────────────────────
main() {
    printf "\n${BOLD}Skaro Installer${RESET}\n\n"

    # 1. Find Python
    info "Looking for Python 3.${MIN_PYTHON_MINOR}+..."
    PYTHON=$(find_python) || fail "Python 3.${MIN_PYTHON_MINOR}+ not found. Install it first: https://www.python.org/downloads/"
    py_version=$("$PYTHON" --version 2>&1)
    ok "Found: $py_version ($(command -v "$PYTHON"))"

    # 2. Check venv module
    if ! check_venv_module "$PYTHON"; then
        fail "Python venv module not available. On Debian/Ubuntu run: sudo apt install python3-venv"
    fi

    # 3. Create or reuse venv
    if [ -d "$VENV_DIR" ]; then
        info "Existing venv found at $VENV_DIR — upgrading..."
    else
        info "Creating venv at $VENV_DIR..."
        mkdir -p "$SKARO_HOME"
        "$PYTHON" -m venv "$VENV_DIR"
        ok "Venv created"
    fi

    # 4. Install / upgrade skaro
    info "Installing $PACKAGE (this may take a moment)..."
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
    "$VENV_DIR/bin/pip" install --upgrade "$PACKAGE" 2>&1 | tail -1
    installed_version=$("$VENV_DIR/bin/pip" show "$PACKAGE" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
    ok "Installed $PACKAGE $installed_version"

    # 5. Symlink into BIN_DIR
    mkdir -p "$BIN_DIR"
    SKARO_BIN_SRC="$VENV_DIR/bin/skaro"

    if [ ! -f "$SKARO_BIN_SRC" ]; then
        fail "Binary not found at $SKARO_BIN_SRC — package may have failed to install."
    fi

    ln -sf "$SKARO_BIN_SRC" "$BIN_DIR/skaro"
    ok "Linked: $BIN_DIR/skaro"

    # 6. Verify PATH
    case ":$PATH:" in
        *":$BIN_DIR:"*) ;;
        *)
            warn "$BIN_DIR is not in your PATH"
            printf "\n  Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):\n"
            printf "    ${CYAN}export PATH=\"%s:\$PATH\"${RESET}\n" "$BIN_DIR"
            printf "  Then restart your terminal or run:\n"
            printf "    ${CYAN}source ~/.bashrc${RESET}  (or ~/.zshrc)\n"
            ;;
    esac

    # 7. Done
    printf "\n${GREEN}${BOLD}Done!${RESET} Run ${CYAN}skaro${RESET} to get started.\n"
    printf "  ${CYAN}cd my-project && skaro init && skaro ui${RESET}\n\n"
}

main "$@"
