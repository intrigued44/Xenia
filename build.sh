#!/bin/bash
echo "Building Nous..."

echo "Installing Python dependencies..."
pip install pyinstaller -q
pip install -r requirements.txt -q

echo "Bundling Python server..."
pyinstaller nous_server.spec --clean --noconfirm

echo "Installing Node dependencies..."
cd ui
npm install

echo "Building Electron app..."
npx electron-builder --win --x64

echo "Done! Installer is in ui/dist/"
