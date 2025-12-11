@echo off
echo ========================================
echo DIAGNOSTICO DE PYTHON
echo ========================================
echo.

echo [1] Comando 'python':
python --version 2>&1
where.exe python 2>nul
echo.

echo [2] Comando 'py':
py --version 2>&1
py -0 2>&1
echo.

echo [3] Verificando PySide6 en cada Python:
echo.
echo --- Python por defecto (python) ---
python -c "import sys; print('Path:', sys.executable); import PySide6; print('PySide6:', PySide6.__version__)" 2>&1
if errorlevel 1 echo PySide6 NO disponible en 'python'
echo.

echo --- Python 3.13 (py -3.13) ---
py -3.13 -c "import sys; print('Path:', sys.executable); import PySide6; print('PySide6:', PySide6.__version__)" 2>&1
if errorlevel 1 echo PySide6 NO disponible en 'py -3.13'
echo.

echo ========================================
echo FIN DEL DIAGNOSTICO
echo ========================================
pause

