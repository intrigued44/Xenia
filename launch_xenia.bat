@echo off
title Xenia Launcher
echo =============================================
echo  Starting Xenia
echo =============================================

:: Kill any old instances
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM Xenia.exe /T 2>nul
timeout /t 2 /nobreak >nul

:: Check if packaged exe exists and is recent
if exist "ui\dist\win-unpacked\Xenia.exe" (
    echo [1/2] Starting backend server...
    start /B "" python start_server.py >nul 2>&1
    
    echo [2/2] Waiting for server to start...
    timeout /t 4 /nobreak >nul
    
    echo Launching Xenia...
    start "" "ui\dist\win-unpacked\Xenia.exe"
) else (
    echo [1/2] Starting backend server...
    start /B "" python start_server.py >nul 2>&1
    
    echo [2/2] Waiting for server...
    timeout /t 5 /nobreak >nul
    
    echo Launching in dev mode...
    cd ui
    start "" node_modules\.bin\electron.cmd .
    cd ..
)

echo Xenia launched! You can close this window.
timeout /t 3 /nobreak >nul
