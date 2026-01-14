#!/usr/bin/env python3
"""
yt-music: A terminal-based YouTube Music player for Linux
Uses yt-dlp for stream extraction and mpv for playback
"""

import subprocess
import sys
import os
import json
import threading
import time
import signal

try:
    from ytmusicapi import YTMusic
except ImportError:
    print("Installing ytmusicapi...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ytmusicapi", "-q", "--break-system-packages"])
    from ytmusicapi import YTMusic


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


class YTMusicPlayer:
    def __init__(self):
        self.ytmusic = YTMusic()
        self.queue = []
        self.current_index = 0
        self.mpv_process = None
        self.is_playing = False
        self.is_paused = False
        self.current_track = None
        self.mpv_socket = f"/tmp/ytmusic_mpv_{os.getpid()}"
        self.playback_thread = None
        self.stop_event = threading.Event()
        
    def clear_screen(self):
        os.system('clear')
        
    def print_header(self):
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("  ╔═══════════════════════════════════════════════════════╗")
        print("  ║           🎵  YouTube Music CLI Player  🎵            ║")
        print("  ╚═══════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}")
        
    def print_now_playing(self):
        if self.current_track:
            status = "▶ Playing" if self.is_playing and not self.is_paused else "⏸ Paused" if self.is_paused else "⏹ Stopped"
            print(f"\n{Colors.GREEN}{Colors.BOLD}  {status}:{Colors.RESET}")
            print(f"  {Colors.YELLOW}♪{Colors.RESET} {self.current_track['title']}")
            print(f"  {Colors.DIM}  by {self.current_track['artist']}{Colors.RESET}")
            if 'duration' in self.current_track:
                print(f"  {Colors.DIM}  Duration: {self.current_track['duration']}{Colors.RESET}")
        print()
        
    def search(self, query, filter_type='songs'):
        """Search YouTube Music"""
        print(f"\n{Colors.CYAN}  Searching for '{query}'...{Colors.RESET}")
        try:
            results = self.ytmusic.search(query, filter=filter_type, limit=10)
            return results
        except Exception as e:
            print(f"{Colors.RED}  Error searching: {e}{Colors.RESET}")
            return []
    
    def display_results(self, results, result_type='songs'):
        """Display search results"""
        if not results:
            print(f"{Colors.YELLOW}  No results found.{Colors.RESET}")
            return
            
        print(f"\n{Colors.BOLD}  Search Results:{Colors.RESET}\n")
        
        for i, item in enumerate(results, 1):
            if result_type == 'songs':
                title = item.get('title', 'Unknown')
                artists = ', '.join([a['name'] for a in item.get('artists', [])]) or 'Unknown Artist'
                duration = item.get('duration', '')
                print(f"  {Colors.CYAN}{i:2}.{Colors.RESET} {title}")
                print(f"      {Colors.DIM}{artists} • {duration}{Colors.RESET}")
            elif result_type == 'playlists':
                title = item.get('title', 'Unknown')
                author = item.get('author', 'Unknown')
                print(f"  {Colors.CYAN}{i:2}.{Colors.RESET} {title}")
                print(f"      {Colors.DIM}by {author}{Colors.RESET}")
            elif result_type == 'albums':
                title = item.get('title', 'Unknown')
                artists = ', '.join([a['name'] for a in item.get('artists', [])]) or 'Unknown Artist'
                year = item.get('year', '')
                print(f"  {Colors.CYAN}{i:2}.{Colors.RESET} {title}")
                print(f"      {Colors.DIM}{artists} • {year}{Colors.RESET}")
        print()
        
    def get_stream_url(self, video_id):
        """Get audio stream URL using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio',
                '-g',
                '--no-warnings',
                f'https://music.youtube.com/watch?v={video_id}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                cmd[-1] = f'https://www.youtube.com/watch?v={video_id}'
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            print(f"{Colors.RED}  Error getting stream: {e}{Colors.RESET}")
            return None
    
    def play_track(self, track_info):
        """Play a single track"""
        self.stop_playback()
        
        video_id = track_info.get('videoId')
        if not video_id:
            print(f"{Colors.RED}  No video ID found for this track.{Colors.RESET}")
            return False
            
        title = track_info.get('title', 'Unknown')
        artists = ', '.join([a['name'] for a in track_info.get('artists', [])]) or 'Unknown Artist'
        duration = track_info.get('duration', '')
        
        self.current_track = {
            'title': title,
            'artist': artists,
            'duration': duration,
            'videoId': video_id
        }
        
        print(f"\n{Colors.CYAN}  Loading: {title}...{Colors.RESET}")
        
        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            
            cmd = [
                'mpv',
                '--no-video',
                '--really-quiet',
                f'--input-ipc-server={self.mpv_socket}',
                '--terminal=no',
                url
            ]
            
            self.mpv_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.is_playing = True
            self.is_paused = False
            
            self.stop_event.clear()
            self.playback_thread = threading.Thread(target=self._monitor_playback, daemon=True)
            self.playback_thread.start()
            
            return True
            
        except FileNotFoundError:
            print(f"{Colors.RED}  Error: mpv not found. Install with: sudo apt install mpv{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.RED}  Error playing track: {e}{Colors.RESET}")
            return False
    
    def _monitor_playback(self):
        """Monitor mpv process and auto-play next in queue"""
        while not self.stop_event.is_set() and self.mpv_process:
            if self.mpv_process.poll() is not None:
                self.is_playing = False
                if not self.stop_event.is_set() and self.current_index < len(self.queue) - 1:
                    self.current_index += 1
                    self.play_track(self.queue[self.current_index])
                break
            time.sleep(0.5)
    
    def send_mpv_command(self, command):
        """Send command to mpv via IPC socket"""
        if not os.path.exists(self.mpv_socket):
            return False
        try:
            import socket
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.mpv_socket)
            client.send((json.dumps({"command": command}) + '\n').encode())
            client.close()
            return True
        except:
            return False
    
    def toggle_pause(self):
        """Toggle pause/play"""
        if self.mpv_process and self.is_playing:
            self.send_mpv_command(["cycle", "pause"])
            self.is_paused = not self.is_paused
            return True
        return False
    
    def stop_playback(self):
        """Stop current playback"""
        self.stop_event.set()
        if self.mpv_process:
            self.mpv_process.terminate()
            try:
                self.mpv_process.wait(timeout=2)
            except:
                self.mpv_process.kill()
            self.mpv_process = None
        self.is_playing = False
        self.is_paused = False
        if os.path.exists(self.mpv_socket):
            try:
                os.remove(self.mpv_socket)
            except:
                pass
    
    def add_to_queue(self, track_info):
        """Add track to queue"""
        self.queue.append(track_info)
        title = track_info.get('title', 'Unknown')
        print(f"{Colors.GREEN}  Added to queue: {title}{Colors.RESET}")
    
    def show_queue(self):
        """Display current queue"""
        if not self.queue:
            print(f"\n{Colors.YELLOW}  Queue is empty.{Colors.RESET}")
            return
            
        print(f"\n{Colors.BOLD}  Current Queue:{Colors.RESET}\n")
        for i, track in enumerate(self.queue):
            prefix = "▶ " if i == self.current_index and self.is_playing else "  "
            color = Colors.GREEN if i == self.current_index else Colors.RESET
            title = track.get('title', 'Unknown')
            artists = ', '.join([a['name'] for a in track.get('artists', [])]) or 'Unknown Artist'
            print(f"  {color}{prefix}{i+1}. {title}{Colors.RESET}")
            print(f"      {Colors.DIM}{artists}{Colors.RESET}")
        print()
    
    def clear_queue(self):
        """Clear the queue"""
        self.queue = []
        self.current_index = 0
        print(f"{Colors.YELLOW}  Queue cleared.{Colors.RESET}")
    
    def next_track(self):
        """Skip to next track in queue"""
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
            self.play_track(self.queue[self.current_index])
        else:
            print(f"{Colors.YELLOW}  End of queue.{Colors.RESET}")
    
    def prev_track(self):
        """Go to previous track in queue"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play_track(self.queue[self.current_index])
        else:
            print(f"{Colors.YELLOW}  Beginning of queue.{Colors.RESET}")
    
    def seek(self, seconds):
        """Seek forward/backward"""
        if self.is_playing:
            self.send_mpv_command(["seek", str(seconds)])
    
    def set_volume(self, volume):
        """Set volume (0-100)"""
        if self.is_playing:
            self.send_mpv_command(["set_property", "volume", volume])
    
    def print_help(self):
        """Print help message"""
        print(f"""
{Colors.BOLD}  Commands:{Colors.RESET}

  {Colors.CYAN}s, search <query>{Colors.RESET}    - Search for songs
  {Colors.CYAN}sa <query>{Colors.RESET}           - Search for albums  
  {Colors.CYAN}sp <query>{Colors.RESET}           - Search for playlists
  
  {Colors.CYAN}p, play <number>{Colors.RESET}     - Play track from results
  {Colors.CYAN}a, add <number>{Colors.RESET}      - Add track to queue
  {Colors.CYAN}pa, playall{Colors.RESET}          - Add all results to queue and play
  
  {Colors.CYAN}space, pause{Colors.RESET}         - Toggle pause/play
  {Colors.CYAN}n, next{Colors.RESET}              - Next track
  {Colors.CYAN}b, prev{Colors.RESET}              - Previous track
  {Colors.CYAN}stop{Colors.RESET}                 - Stop playback
  
  {Colors.CYAN}q, queue{Colors.RESET}             - Show queue
  {Colors.CYAN}cq, clear{Colors.RESET}            - Clear queue
  
  {Colors.CYAN}+, -{Colors.RESET}                 - Seek forward/backward 10s
  {Colors.CYAN}v <0-100>{Colors.RESET}            - Set volume
  
  {Colors.CYAN}h, help{Colors.RESET}              - Show this help
  {Colors.CYAN}x, exit{Colors.RESET}              - Exit player
""")

    def run(self):
        """Main loop"""
        self.clear_screen()
        self.print_header()
        self.print_help()
        
        results = []
        result_type = 'songs'
        
        while True:
            try:
                self.print_now_playing()
                cmd = input(f"{Colors.BOLD}  >{Colors.RESET} ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split(maxsplit=1)
                action = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if action in ['x', 'exit', 'quit']:
                    self.stop_playback()
                    print(f"\n{Colors.CYAN}  Goodbye! 🎵{Colors.RESET}\n")
                    break
                    
                elif action in ['h', 'help']:
                    self.print_help()
                    
                elif action in ['s', 'search']:
                    if arg:
                        results = self.search(arg, 'songs')
                        result_type = 'songs'
                        self.display_results(results, result_type)
                    else:
                        print(f"{Colors.YELLOW}  Usage: search <query>{Colors.RESET}")
                        
                elif action == 'sa':
                    if arg:
                        results = self.search(arg, 'albums')
                        result_type = 'albums'
                        self.display_results(results, result_type)
                    else:
                        print(f"{Colors.YELLOW}  Usage: sa <query>{Colors.RESET}")
                        
                elif action == 'sp':
                    if arg:
                        results = self.search(arg, 'playlists')
                        result_type = 'playlists'
                        self.display_results(results, result_type)
                    else:
                        print(f"{Colors.YELLOW}  Usage: sp <query>{Colors.RESET}")
                        
                elif action in ['p', 'play']:
                    if arg.isdigit():
                        idx = int(arg) - 1
                        if 0 <= idx < len(results):
                            if result_type == 'songs':
                                self.queue = [results[idx]]
                                self.current_index = 0
                                self.play_track(results[idx])
                            else:
                                print(f"{Colors.YELLOW}  Can only play songs directly. Use search first.{Colors.RESET}")
                        else:
                            print(f"{Colors.RED}  Invalid selection.{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}  Usage: play <number>{Colors.RESET}")
                        
                elif action in ['a', 'add']:
                    if arg.isdigit():
                        idx = int(arg) - 1
                        if 0 <= idx < len(results) and result_type == 'songs':
                            self.add_to_queue(results[idx])
                        else:
                            print(f"{Colors.RED}  Invalid selection.{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}  Usage: add <number>{Colors.RESET}")
                        
                elif action in ['pa', 'playall']:
                    if results and result_type == 'songs':
                        self.queue = results.copy()
                        self.current_index = 0
                        print(f"{Colors.GREEN}  Added {len(results)} tracks to queue.{Colors.RESET}")
                        self.play_track(self.queue[0])
                    else:
                        print(f"{Colors.YELLOW}  No songs to add.{Colors.RESET}")
                        
                elif action in ['space', 'pause']:
                    if self.toggle_pause():
                        status = "Paused" if self.is_paused else "Resumed"
                        print(f"{Colors.GREEN}  {status}{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}  Nothing playing.{Colors.RESET}")
                        
                elif action in ['n', 'next']:
                    self.next_track()
                    
                elif action in ['b', 'prev']:
                    self.prev_track()
                    
                elif action == 'stop':
                    self.stop_playback()
                    print(f"{Colors.YELLOW}  Playback stopped.{Colors.RESET}")
                    
                elif action in ['q', 'queue']:
                    self.show_queue()
                    
                elif action in ['cq', 'clear']:
                    self.stop_playback()
                    self.clear_queue()
                    
                elif action == '+':
                    self.seek(10)
                    print(f"{Colors.DIM}  >> 10s{Colors.RESET}")
                    
                elif action == '-':
                    self.seek(-10)
                    print(f"{Colors.DIM}  << 10s{Colors.RESET}")
                    
                elif action == 'v':
                    if arg.isdigit():
                        vol = max(0, min(100, int(arg)))
                        self.set_volume(vol)
                        print(f"{Colors.DIM}  Volume: {vol}%{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}  Usage: v <0-100>{Colors.RESET}")
                        
                elif action == 'cls':
                    self.clear_screen()
                    self.print_header()
                    
                else:
                    # Treat as search if no command matched
                    results = self.search(cmd, 'songs')
                    result_type = 'songs'
                    self.display_results(results, result_type)
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}  Use 'exit' to quit.{Colors.RESET}")
            except EOFError:
                break
            except Exception as e:
                print(f"{Colors.RED}  Error: {e}{Colors.RESET}")


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        subprocess.run(['mpv', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        missing.append('mpv')
    
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        missing.append('yt-dlp')
    
    if missing:
        print(f"{Colors.RED}Missing dependencies: {', '.join(missing)}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Install with:{Colors.RESET}")
        if 'mpv' in missing:
            print("  sudo apt install mpv")
        if 'yt-dlp' in missing:
            print("  pip install yt-dlp --break-system-packages")
        return False
    return True


def main():
    """Entry point for the yt-music command"""
    if not check_dependencies():
        sys.exit(1)
    
    player = YTMusicPlayer()
    
    def signal_handler(sig, frame):
        player.stop_playback()
        print(f"\n{Colors.CYAN}  Goodbye! 🎵{Colors.RESET}\n")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    player.run()


if __name__ == "__main__":
    main()
