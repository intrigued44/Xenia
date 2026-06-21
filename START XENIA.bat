@echo off
setlocal

set "ROOT=%~dp0"
set "EXE=%ROOT%ui\dist\win-unpacked\Xenia.exe"

echo.
echo  Xenia Intelligence Platform
echo  ============================
echo.

if not exist "%EXE%" (
    echo  ERROR: Xenia.exe not found at:
    echo  %EXE%
    echo.
    echo  Press any key to close.
    pause >nul
    exit /b 1
)

echo  Starting Xenia...
echo  Path: %EXE%
echo.

start "" "%EXE%"

echo  Xenia is launching! This window will close in 3 seconds.
timeout /t 3 /nobreak >nul
exit /b 0
