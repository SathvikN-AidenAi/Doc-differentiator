# DocDiff Backend Startup Script (PowerShell)
# Run with: .\run.ps1

Write-Host "Starting DocDiff Backend Server..." -ForegroundColor Green
Write-Host ""

# Check if UV is installed
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Using UV to run the server" -ForegroundColor Cyan
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment" -ForegroundColor Cyan
    & .venv\Scripts\Activate.ps1
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} else {
    Write-Host "Error: UV not found and virtual environment doesn't exist" -ForegroundColor Red
    Write-Host "Please run 'uv sync' first to set up the environment" -ForegroundColor Yellow
    exit 1
}
