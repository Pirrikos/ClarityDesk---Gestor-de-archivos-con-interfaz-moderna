@echo off
REM Run ClarityDesk Pro - Try Python 3.13 first (where PySide6 is installed)
REM If that fails, try default python

echo Checking Python installations...
py -3.13 -c "import PySide6" 2>nul
if %errorlevel% equ 0 (
    echo Using Python 3.13 (PySide6 available)
    py -3.13 main.py
) else (
    echo Python 3.13 not available or PySide6 missing, trying default python...
    REM Check if venv is active and install dependencies if needed
    python -c "import PySide6" 2>nul
    if errorlevel 1 (
        echo Installing missing dependencies...
        python -m pip install -r requirements.txt
    )
    python main.py
)
