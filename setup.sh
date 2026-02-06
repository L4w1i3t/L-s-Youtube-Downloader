#!/bin/bash

# YouTube Downloader Setup Script for Linux
# This script will install all required dependencies

echo "========================================"
echo "  YouTube Downloader - Setup Wizard"
echo "========================================"
echo ""

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS_DIR="$SCRIPT_DIR/dependencies"

# Create dependencies directory if it doesn't exist
mkdir -p "$DEPS_DIR"

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Error: Cannot detect Linux distribution"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Install system dependencies based on distribution
echo "[1/3] Installing system dependencies..."

case "$OS" in
    ubuntu|debian)
        echo "Installing via apt..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-tk python3-pip ffmpeg
        ;;
    arch)
        echo "Installing via pacman..."
        sudo pacman -S --noconfirm python tk ffmpeg
        ;;
    fedora|rhel|centos)
        echo "Installing via dnf..."
        sudo dnf install -y python3 python3-tkinter python3-pip ffmpeg
        ;;
    opensuse*)
        echo "Installing via zypper..."
        sudo zypper install -y python3 python3-tk python3-pip ffmpeg
        ;;
    alpine)
        echo "Installing via apk..."
        sudo apk add --no-cache python3 py3-tkinter py3-pip ffmpeg
        ;;
    *)
        echo "Unsupported distribution: $OS"
        echo "Please install manually:"
        echo "  - Python 3.6+"
        echo "  - Python3-tk (tkinter)"
        echo "  - ffmpeg"
        echo "  - yt-dlp (via pip)"
        exit 1
        ;;
esac

echo "System dependencies installed!"
echo ""

# Install Python dependencies
echo "[2/3] Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

echo "Python dependencies installed!"
echo ""

# Optional: Download local yt-dlp binary
echo "[3/3] Checking yt-dlp..."

YT_DLP_PATH="$DEPS_DIR/yt-dlp"

if [ -f "$YT_DLP_PATH" ]; then
    echo "yt-dlp is already installed."
    chmod +x "$YT_DLP_PATH"
else
    echo "yt-dlp not found in dependencies directory."
    echo ""
    echo "The application will use the system yt-dlp installation."
    echo "If you want a local copy, run:"
    echo "  pip3 install yt-dlp"
    echo ""
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  python3 yt-dlp-gui.py"
echo ""
