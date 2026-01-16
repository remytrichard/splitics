#!/bin/bash
# Hook that runs pytest after Python file edits
# This provides a feedback loop during implementation

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Parse the file path from hook input (JSON via stdin)
# If jq is not available, fall back to grep/sed
if command -v jq &> /dev/null; then
    file_path=$(cat | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
    file_path=$(cat | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*: *"//' | sed 's/"$//')
fi

# Only run tests if a Python file was edited
if [[ "$file_path" == *.py ]]; then
    cd "$PROJECT_DIR"

    # Check if tests directory exists
    if [[ ! -d "tests" ]]; then
        echo "[hook] No tests directory yet - skipping pytest"
        exit 0
    fi

    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        echo "[hook] uv not installed - skipping tests"
        echo "[hook] Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 0
    fi

    echo ""
    echo "=========================================="
    echo "[hook] Running pytest after edit to: $(basename "$file_path")"
    echo "=========================================="

    # Run pytest via uv (handles venv and dependencies automatically)
    uv run pytest -v --tb=short
    exit_code=$?

    echo ""
    if [ $exit_code -eq 0 ]; then
        echo "[hook] All tests passed"
    else
        echo "[hook] TESTS FAILED - please fix before continuing"
    fi
    echo "=========================================="

    exit $exit_code
fi

exit 0
