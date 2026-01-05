@echo off
REM DocDiff Backend Startup Script (Windows)
REM Run with: .\run.bat or just run.bat

echo Starting DocDiff Backend Server...
echo.

REM Check if using UV
if exist ".venv\Scripts\activate.bat" (
    echo Using UV virtual environment
    call .venv\Scripts\activate.bat
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo Using UV directly
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
