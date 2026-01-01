"""
Script de build de PyInstaller fuera de OneDrive.

Este script ejecuta PyInstaller usando main.spec y fija rutas de salida (dist/work)
en %LOCALAPPDATA% para evitar bloqueos de OneDrive/antivirus sobre dist\\main.
"""

import os
import sys
from pathlib import Path


def main() -> int:
    # Obtener directorios seguros en LOCALAPPDATA (no sincronizados)
    local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    base = Path(local_appdata) / "ClarityDesk" / "pyinstaller"
    dist = base / "dist"
    work = base / "build"
    dist.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    # Construir argumentos para PyInstaller
    args = [
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "main.spec",
    ]

    try:
        # Ejecutar PyInstaller mediante el módulo
        from PyInstaller.__main__ import run  # type: ignore
        run(args)
        return 0
    except ImportError:
        # Fallback: intentar invocar pyinstaller desde Scripts si el módulo no está disponible
        import subprocess
        cmd = ["pyinstaller"] + args
        proc = subprocess.run(cmd, cwd=str(Path(__file__).resolve().parents[1]))
        return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

