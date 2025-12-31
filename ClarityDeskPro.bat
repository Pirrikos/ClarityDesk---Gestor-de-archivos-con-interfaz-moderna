@echo off
setlocal EnableExtensions

rem 1. Fijar directorio de trabajo en raiz del proyecto
rem    %~dp0 obtiene el directorio donde esta el .bat
set "APPDIR=%~dp0"
cd /d "%APPDIR%"

rem 2. Verificar que existe el virtualenv
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: No se encontro el entorno virtual .venv
    echo.
    echo Cree el entorno con:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

rem 3. Activar el virtualenv explicitamente
rem    Replica exactamente el entorno de desarrollo
call ".venv\Scripts\activate.bat"

rem 4. Ejecutar la aplicacion usando python.exe (CON consola)
rem    Permite ver errores en stdout/stderr si fallan imports o excepciones
python main.py

rem 5. Pausa para ver errores antes de cerrar
rem    Solo se ejecuta si python termina (incluso con error)
echo.
echo La aplicacion se ha cerrado.
pause

