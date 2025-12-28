@echo off
REM Auto-restart ClarityDesk Pro when Python files change using watchdog
REM Usage: watch.bat
REM Watches only Python source files, excludes storage/log/cache files

echo Starting ClarityDesk Pro with auto-restart...
echo Watching for changes in *.py files...
echo Excluding: storage/, __pycache__/, .venv/, *.db, *.json, *.log, *.pyc
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
python -m watchdog.watchmedo auto-restart --patterns="*.py" --ignore-patterns="*/storage/*;*/__pycache__/*;*/.venv/*;*.db;*.json;*.log;*.pyc;*.pyo" --recursive --debounce-interval=2 -- .venv\Scripts\python.exe main.py

