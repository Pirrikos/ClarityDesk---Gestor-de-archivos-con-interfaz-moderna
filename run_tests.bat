@echo off
chcp 65001 >nul 2>&1
echo ==============================================
echo   ClarityDesk Pro - Ejecutar Tests
echo ==============================================
echo.

REM Verificar si pytest está instalado
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pytest no está instalado.
    echo.
    echo Instalar con: pip install pytest pytest-qt
    echo.
    pause
    exit /b 1
)

echo [INFO] Ejecutando tests con pytest...
echo.

REM Ejecutar tests con pytest
python -m pytest tests/ app/tests/ -v --tb=short

echo.
echo ==============================================
echo   Tests completados
echo ==============================================
pause

