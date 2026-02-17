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
echo "[1/4] Installing system dependencies..."

case "$OS" in
    ubuntu|debian)
        echo "Installing via apt..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-tk python3-pip ffmpeg curl
        ;;
    arch)
        echo "Installing via pacman..."
        sudo pacman -S --noconfirm python tk ffmpeg curl
        ;;
    fedora|rhel|centos)
        echo "Installing via dnf..."
        sudo dnf install -y python3 python3-tkinter python3-pip ffmpeg curl
        ;;
    opensuse*)
        echo "Installing via zypper..."
        sudo zypper install -y python3 python3-tk python3-pip ffmpeg curl
        ;;
    alpine)
        echo "Installing via apk..."
        sudo apk add --no-cache python3 py3-tkinter py3-pip ffmpeg curl
        ;;
    *)
        echo "Unsupported distribution: $OS"
        echo "Please install manually:"
        echo "  - Python 3.6+"
        echo "  - Python3-tk (tkinter)"
        echo "  - ffmpeg"
        echo "  - Node.js (https://nodejs.org)"
        echo "  - yt-dlp (via pip)"
        exit 1
        ;;
esac

echo "System dependencies installed!"
echo ""

# Install Python dependencies
echo "[2/4] Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

echo "Python dependencies installed!"
echo ""

# Check and install Node.js
echo "[3/4] Checking Node.js (required for YouTube downloads)..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node.js $NODE_VERSION is already installed."
else
    echo "Node.js is not installed. Installing..."
    case "$OS" in
        ubuntu|debian)
            # Use NodeSource for up-to-date LTS
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        arch)
            sudo pacman -S --noconfirm nodejs npm
            ;;
        fedora|rhel|centos)
            sudo dnf install -y nodejs npm
            ;;
        opensuse*)
            sudo zypper install -y nodejs npm
            ;;
        alpine)
            sudo apk add --no-cache nodejs npm
            ;;
        *)
            echo "Please install Node.js manually from https://nodejs.org"
            ;;
    esac
    
    if command -v node &> /dev/null; then
        echo "Node.js $(node --version) installed successfully!"
    else
        echo "WARNING: Node.js installation may have failed."
        echo "Please install manually from https://nodejs.org"
    fi
fi

echo ""

# Optional: Download local yt-dlp binary
echo "[4/4] Checking yt-dlp..."

YT_DLP_PATH="$DEPS_DIR/yt-dlp"

if [ -f "$YT_DLP_PATH" ]; then
    echo "yt-dlp is already installed locally."
    chmod +x "$YT_DLP_PATH"
elif command -v yt-dlp &> /dev/null; then
    echo "yt-dlp is available on system PATH."
else
    echo "Downloading yt-dlp..."
    curl -L "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp" -o "$YT_DLP_PATH"
    if [ -f "$YT_DLP_PATH" ]; then
        chmod +x "$YT_DLP_PATH"
        echo "yt-dlp installed successfully!"
    else
        echo "Failed to download yt-dlp. Trying pip..."
        pip3 install yt-dlp
    fi
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  python3 yt-dlp-gui.py"
echo ""
