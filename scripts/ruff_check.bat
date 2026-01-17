@echo off
REM Ruff Code Quality and Formatting Script
REM This script runs ruff checks and formatting on the project

echo Running ruff check with auto-fix...
uv run ruff check --fix core

echo.
echo Running ruff format...
uv run ruff format core

echo.
echo Done!
pause