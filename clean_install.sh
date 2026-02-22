#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# LangPedia — Clean Install (Linux / macOS)
#
# Usage:
#   ./clean_install.sh                   # Full install
#   ./clean_install.sh --skip-studio     # Skip npm install
#   ./clean_install.sh --skip-precommit  # Skip pre-commit hooks
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

SKIP_STUDIO=false
SKIP_PRECOMMIT=false

for arg in "$@"; do
    case "$arg" in
        --skip-studio)     SKIP_STUDIO=true ;;
        --skip-precommit)  SKIP_PRECOMMIT=true ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR="$PROJECT_ROOT/.venv-langpedia"

echo ""
echo "  LangPedia - Clean Install"
echo ""

# ── Step 1: Clean existing venv ──────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[1/5] Removing existing .venv-langpedia..."
    rm -rf "$VENV_DIR"
else
    echo "[1/5] No existing .venv-langpedia found, starting fresh."
fi

# ── Step 2: Create virtual environment ───────────────────────────────────
echo "[2/5] Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate venv
source "$VENV_DIR/bin/activate"

# ── Step 3: Install Python dependencies ──────────────────────────────────
echo "[3/5] Upgrading pip and installing project..."
python -m pip install --upgrade pip --quiet
python -m pip install -e ".[dev]" --quiet
echo "       Python dependencies installed."

# ── Step 4: Pre-commit hooks ─────────────────────────────────────────────
if [ "$SKIP_PRECOMMIT" = false ]; then
    echo "[4/5] Installing pre-commit hooks..."
    pre-commit install
    echo "       Pre-commit hooks installed."
else
    echo "[4/5] Skipping pre-commit hooks (--skip-precommit)."
fi

# ── Step 5: Studio (Next.js) dependencies ────────────────────────────────
if [ "$SKIP_STUDIO" = false ]; then
    if [ -f "$PROJECT_ROOT/studio/package.json" ]; then
        echo "[5/5] Installing Studio (Next.js) dependencies..."
        cd "$PROJECT_ROOT/studio"
        npm install --silent
        cd "$PROJECT_ROOT"
        echo "       Studio dependencies installed."
    else
        echo "[5/5] Studio package.json not found, skipping."
    fi
else
    echo "[5/5] Skipping Studio install (--skip-studio)."
fi

# ── Done ─────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To activate the environment:"
echo "  source .venv-langpedia/bin/activate"
echo ""
echo "Quick commands:"
echo "  pytest                        # Run tests"
echo "  pre-commit run --all-files    # Run linters"
echo "  uvicorn backend.app.api.main:app --reload  # Start backend"
echo "  cd studio && npm run dev      # Start Studio UI"
echo ""
