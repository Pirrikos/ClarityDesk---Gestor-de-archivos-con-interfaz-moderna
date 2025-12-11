@echo off
setlocal enabledelayedexpansion

set DEBUG_MODE=0
if "%1"=="debug" set DEBUG_MODE=1

echo ========================================
echo ClarityDesk Pro - Build Release Script
echo ========================================
echo.

REM 1. Run pytest
echo [1/5] Running tests...
python -m pytest
if errorlevel 1 (
    echo.
    echo ========================================
    echo TEST FAILED - BUILD ABORTED
    echo ========================================
    exit /b 1
)
echo Tests passed!
echo.

REM 2. Clean build directories
echo [2/5] Cleaning build directories...
if exist build\ (
    rmdir /s /q build\
    echo Removed build\
)
if %DEBUG_MODE%==0 (
    if exist dist\ (
        rmdir /s /q dist\
        echo Removed dist\
    )
) else (
    echo Debug mode: Keeping dist\ folder
)
echo.

REM 3. Run PyInstaller
echo [3/5] Running PyInstaller...
pyinstaller --noconfirm --clean main.py
if errorlevel 1 (
    echo.
    echo ========================================
    echo BUILD FAILED - PyInstaller error
    echo ========================================
    exit /b 1
)
echo.

REM 4. Verify executable
echo [4/5] Verifying executable...
if exist dist\main\main.exe (
    echo Executable found: dist\main\main.exe
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL
    echo ========================================
    echo Executable location: dist\main\main.exe
    exit /b 0
) else (
    echo Executable not found: dist\main\main.exe
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    exit /b 1
)

