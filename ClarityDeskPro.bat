@echo off
setlocal EnableExtensions

rem Directorio del proyecto (donde está este .bat)
set "APPDIR=%~dp0"
pushd "%APPDIR%"

rem Verificación: debe existir pythonw.exe del entorno (.venv)
if not exist ".venv\Scripts\pythonw.exe" (
  powershell -NoProfile -WindowStyle Hidden -Command ^
    "$ws=New-Object -ComObject WScript.Shell; $ws.Popup('No se encontró el entorno .venv.\nCree el entorno y instale dependencias:\n  python -m venv .venv\n  .venv\\Scripts\\pip install -r requirements.txt','ClarityDesk Pro',0,16)" >nul 2>&1
  popd
  exit /b 1
)

rem Activar el entorno virtual en silencio
call ".venv\Scripts\activate.bat" >nul 2>&1

rem Lanzar la app con pythonw (sin consola) y cerrar este .bat
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass ^
  -Command "Start-Process -FilePath '.venv\\Scripts\\pythonw.exe' -WorkingDirectory '%APPDIR%' -ArgumentList 'main.py'"

popd
exit /b 0

