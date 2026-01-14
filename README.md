# 🎵 yt-music-cli

A terminal-based YouTube Music player for Linux. Search, queue, and play music directly from your terminal.

![Terminal Demo](https://img.shields.io/badge/platform-Linux-blue) ![Python](https://img.shields.io/badge/python-3.8+-green)

## Features

- 🔍 Search songs, albums, and playlists from YouTube Music
- ▶️ Stream audio directly (no downloads)
- 📋 Queue management with auto-play
- ⏯️ Playback controls (pause, seek, volume, skip)
- 🎨 Colorful terminal interface
- ⌨️ Simple keyboard commands

## Requirements

- Python 3.8+
- mpv (audio player)
- yt-dlp (stream extraction)

## Installation

### Quick Install

```bash
git clone <this repo>
cd yt-music-cli
chmod +x install.sh
./install.sh
```

### Manual Install

1. Install system dependencies:
```bash
# Debian/Ubuntu
sudo apt install mpv

# Fedora
sudo dnf install mpv

# Arch
sudo pacman -S mpv
```

2. Install the package:
```bash
cd yt-music-cli
pip install --break-system-packages --user .
```

### Alternative: Install with pipx (recommended)

```bash
sudo apt install mpv
pipx install .
```

## Usage

```bash
yt-music-cli
```

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `search <query>` | `s` | Search for songs |
| `sa <query>` | | Search for albums |
| `sp <query>` | | Search for playlists |
| `play <num>` | `p` | Play track from results |
| `add <num>` | `a` | Add track to queue |
| `playall` | `pa` | Queue all results and play |
| `pause` | `space` | Toggle pause/play |
| `next` | `n` | Next track |
| `prev` | `b` | Previous track |
| `stop` | | Stop playback |
| `queue` | `q` | Show current queue |
| `clear` | `cq` | Clear queue |
| `+` | | Seek forward 10s |
| `-` | | Seek backward 10s |
| `v <0-100>` | | Set volume |
| `help` | `h` | Show help |
| `exit` | `x` | Exit player |

### Quick Start Example

```
$ yt-music-cli

> search daft punk
  1. Get Lucky
     Daft Punk • 6:09
  2. Around The World
     Daft Punk • 7:09
  ...

> play 1
  Loading: Get Lucky...

> add 2
  Added to queue: Around The World

> queue
  ▶ 1. Get Lucky
    2. Around The World

> next
```

## Tips

- Just type anything to search (no need to type `search`)
- Use `cls` to clear the screen
- Press Ctrl+C and then type `exit` to quit cleanly
- The player auto-advances through your queue

## Uninstall

```bash
pip uninstall yt-music-cli-cli
```

## Troubleshooting

**"mpv not found"**: Install mpv with your package manager

**"yt-dlp not found"**: 
```bash
pip install yt-dlp --break-system-packages
```

**"yt-music-cli: command not found"**: Add `~/.local/bin` to your PATH:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Playback issues**: Make sure you have a working internet connection and that YouTube isn't blocking your region

## License

MIT License - feel free to modify and share!
