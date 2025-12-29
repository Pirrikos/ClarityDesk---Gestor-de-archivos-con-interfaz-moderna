@echo off
echo ========================================
echo    LIMPIEZA DE ARCHIVOS TEMPORALES
echo    ClarityDesk Project
echo ========================================
echo.

echo [1/7] Eliminando backups (617 MB)...
rmdir /s /q backups 2>nul
if exist backups (
    echo    X ERROR: No se pudo eliminar backups
) else (
    echo    OK Eliminado
)

echo [2/7] Eliminando build (24 MB)...
rmdir /s /q build 2>nul
if exist build (
    echo    X ERROR: No se pudo eliminar build
) else (
    echo    OK Eliminado
)

echo [3/7] Eliminando dist (173 MB)...
rmdir /s /q dist 2>nul
if exist dist (
    echo    X ERROR: No se pudo eliminar dist
) else (
    echo    OK Eliminado
)

echo [4/7] Eliminando __pycache__...
rmdir /s /q __pycache__ 2>nul
if exist __pycache__ (
    echo    X ERROR: No se pudo eliminar __pycache__
) else (
    echo    OK Eliminado
)

echo [5/7] Eliminando .pytest_cache...
rmdir /s /q .pytest_cache 2>nul
if exist .pytest_cache (
    echo    X ERROR: No se pudo eliminar .pytest_cache
) else (
    echo    OK Eliminado
)

echo [6/7] Eliminando output.log...
del /f /q output.log 2>nul
if exist output.log (
    echo    X ERROR: No se pudo eliminar output.log
) else (
    echo    OK Eliminado
)

echo [7/7] Eliminando arbol.txt...
del /f /q arbol.txt 2>nul
if exist arbol.txt (
    echo    X ERROR: No se pudo eliminar arbol.txt
) else (
    echo    OK Eliminado
)

echo.
echo ========================================
echo    LIMPIEZA COMPLETADA
echo    Espacio liberado: ~814 MB
echo ========================================
echo.
pause
