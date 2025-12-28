@echo off
REM Auto-restart ClarityDesk Pro with verbose output to debug what files trigger restarts
REM Usage: watch_verbose.bat

echo Starting ClarityDesk Pro with auto-restart (VERBOSE MODE)...
echo Watching for changes in *.py files...
echo This will show which files trigger restarts
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
python -m watchdog.watchmedo auto-restart --verbose --patterns="*.py" --ignore-patterns="*/storage/*;*/__pycache__/*;*/.venv/*;*.db;*.json;*.log;*.pyc;*.pyo" --recursive --debounce-interval=2 -- .venv\Scripts\python.exe main.py

