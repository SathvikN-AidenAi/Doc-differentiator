#!/usr/bin/env bash
# DocDiff Backend Startup Script (Unix/Linux/macOS/Git Bash)
# Run with: ./run.sh or bash run.sh

set -e
export PYTHONUNBUFFERED=1

echo "Starting DocDiff Backend Server..."
echo ""

# Check if UV is available
if command -v uv &> /dev/null; then
    echo "Using UV to run the server"
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment"
    source .venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Error: UV not found and virtual environment doesn't exist"
    echo "Please run 'uv sync' first to set up the environment"
    exit 1
fi
