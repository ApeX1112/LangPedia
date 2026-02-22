#!/usr/bin/env bash
# Run the LangPedia test suite.
# Usage: ./tests/run_tests.sh [-v] [-k FILTER]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Activate venv if it exists
if [ -f "$PROJECT_ROOT/.venv-langpedia/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv-langpedia/bin/activate"
fi

# Build pytest arguments
PYTEST_ARGS=("-v" "--tb=short")

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose) PYTEST_ARGS+=("-s"); shift ;;
        -k|--filter)  PYTEST_ARGS+=("-k" "$2"); shift 2 ;;
        *)            PYTEST_ARGS+=("$1"); shift ;;
    esac
done

echo ""
echo "Running LangPedia tests..."
echo "pytest ${PYTEST_ARGS[*]}"
echo ""

cd "$PROJECT_ROOT"
pytest "${PYTEST_ARGS[@]}"
