#!/bin/bash
# Installation script for yt-music

set -e

echo "🎵 Installing yt-music..."
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Install with: sudo apt install python3 python3-pip"
    exit 1
fi

# Install system dependencies (mpv)
echo "📦 Installing system dependencies..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y mpv
elif command -v dnf &> /dev/null; then
    sudo dnf install -y mpv
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm mpv
elif command -v brew &> /dev/null; then
    brew install mpv
else
    echo "⚠️  Please install mpv manually for your distribution"
fi

# Install the package
echo "🐍 Installing yt-music..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip install --break-system-packages --user "$SCRIPT_DIR"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  yt-music            # Launch from anywhere"
echo ""
echo "If 'yt-music' command is not found, add this to your ~/.bashrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo "Then restart your terminal or run: source ~/.bashrc"
echo ""
