@echo off
echo Building StopeForge executable...

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found.
    echo Run: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

pip install -r requirements.txt

pyinstaller --noconfirm --onefile --windowed --name StopeForge run.py

echo.
echo Build complete.
echo Executable location: dist\StopeForge.exe
pause
