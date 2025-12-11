@echo off
echo ========================================
echo VERIFICACION DE DEPENDENCIAS
echo ========================================
echo.

echo Verificando dependencias...
python -c "import PySide6; print('✅ PySide6:', PySide6.__version__)" 2>nul || echo ❌ PySide6 NO instalado
python -c "import docx; print('✅ python-docx instalado')" 2>nul || echo ❌ python-docx NO instalado
python -c "import pdf2image; print('✅ pdf2image instalado')" 2>nul || echo ❌ pdf2image NO instalado
python -c "from PIL import Image; print('✅ Pillow instalado')" 2>nul || echo ❌ Pillow NO instalado
python -c "import win32gui; print('✅ pywin32 instalado')" 2>nul || echo ❌ pywin32 NO instalado

echo.
echo ========================================
echo Si alguna dependencia falta, ejecuta:
echo python -m pip install -r requirements.txt
echo ========================================
pause

