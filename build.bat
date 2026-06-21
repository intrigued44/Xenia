@echo off
echo ============================================
echo Building Xenia for Windows
echo ============================================

echo.
echo [1/4] Checking dependencies...
python --version >nul 2>&1 || (
    echo ERROR: Python not found. 
    echo Install Python 3.9+ from python.org
    
    exit /b 1
)

node --version >nul 2>&1 || (
    echo ERROR: Node.js not found.
    echo Install Node.js from nodejs.org
    
    exit /b 1
)

echo.
echo [2/4] Installing Python build dependencies...
pip install pyinstaller pillow -q

echo.
echo [2b/4] Generating icon...
python generate_icon.py

echo.
echo [3/4] Bundling Python server...
pyinstaller xenia_server.spec  --noconfirm
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller failed
    
    exit /b 1
)
echo Server bundled successfully.

echo.
echo [4/4] Building Electron installer...
cd ui
call npm install --silent
call npm run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: Electron build failed
    exit /b %ERRORLEVEL%
)
cd ..

echo.
echo [4b/4] Cleaning up intermediate Python builds...
rmdir /S /Q build\xenia_server
rmdir /S /Q dist\xenia_server

echo.
echo ============================================
echo BUILD COMPLETE
echo Installer: ui\dist\Xenia Setup.exe

