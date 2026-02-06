#!/bin/bash

# Build script for Linux
# Creates a standalone executable using PyInstaller

echo "Building yt-dlp GUI for Linux..."

# Install PyInstaller if not already installed
echo "Checking for PyInstaller..."
pip3 install pyinstaller

# Run PyInstaller
echo "Running PyInstaller..."
pyinstaller --onefile \
    --windowed \
    --add-data "assets:assets" \
    --icon="assets/logo.ico" \
    --name "yt-dlp-gui" \
    yt-dlp-gui.py

echo ""
echo "Build complete!"
echo "Executable location: ./dist/yt-dlp-gui"
