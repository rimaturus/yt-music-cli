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

# Ask user about virtual environment
echo ""
read -p "Do you want to create a virtual environment for installation? (y/n): " use_venv
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$use_venv" =~ ^[Yy]$ ]]; then
    # Create and use virtual environment
    VENV_DIR="$HOME/.yt-music-venv"
    echo "📁 Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"

    echo "🐍 Installing yt-music in virtual environment..."
    "$VENV_DIR/bin/pip" install "$SCRIPT_DIR"

    # Create wrapper script in ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/yt-music" << 'WRAPPER'
#!/bin/bash
exec "$HOME/.yt-music-venv/bin/yt-music" "$@"
WRAPPER
    chmod +x "$HOME/.local/bin/yt-music"

    echo ""
    echo "✅ Installation complete (using virtual environment at $VENV_DIR)!"
else
    # Install without virtual environment
    echo "🐍 Installing yt-music..."
    pip install --break-system-packages --user "$SCRIPT_DIR"

    echo ""
    echo "✅ Installation complete!"
fi

echo ""
echo "Usage:"
echo "  yt-music            # Launch from anywhere"
echo ""
echo "If 'yt-music' command is not found, add this to your ~/.bashrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo "Then restart your terminal or run: source ~/.bashrc"
echo ""
