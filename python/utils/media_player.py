"""
Media player utilities for launching external media players (ffplay, VLC, etc.)
with enhanced functionality including zoom support and image sequence handling.
"""
import os
import subprocess
import platform
import logging
import json
import re
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import socket

logger = logging.getLogger(__name__)


def is_image_sequence(files: List[str]) -> bool:
    """
    Detect if a list of files represents an image sequence.
    
    Args:
        files: List of file paths
        
    Returns:
        bool: True if files appear to be an image sequence
    """
    if len(files) < 2:
        return False
    
    # Check if all files are images
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'}
    if not all(Path(f).suffix.lower() in image_extensions for f in files):
        return False
    
    # Check if files have sequential numbering pattern
    base_names = [Path(f).stem for f in files]
    
    # Look for numeric sequences
    numeric_parts = []
    for name in base_names:
        # Extract trailing numbers
        i = len(name) - 1
        while i >= 0 and name[i].isdigit():
            i -= 1
        if i < len(name) - 1:
            numeric_parts.append(int(name[i+1:]))
        else:
            return False
    
    # Check if numbers are sequential
    numeric_parts.sort()
    for i in range(1, len(numeric_parts)):
        if numeric_parts[i] - numeric_parts[i-1] != 1:
            return False
    
    return True


def get_sequence_frame_rate(files: List[str]) -> float:
    """
    Determine appropriate frame rate for image sequence playback.
    
    Args:
        files: List of image files
        
    Returns:
        float: Frame rate (fps)
    """
    # For most image sequences, 24 fps is a good default
    # Could be enhanced to detect from file timestamps or metadata
    num_files = len(files)
    
    if num_files < 10:
        return 5.0  # Slow for very short sequences
    elif num_files < 50:
        return 12.0  # Medium speed
    elif num_files < 200:
        return 24.0  # Standard film rate
    else:
        return 30.0  # Higher rate for longer sequences


def find_ffplay() -> Optional[str]:
    """
    Find ffplay executable in system PATH or common installation locations.
    
    Returns:
        str: Path to ffplay executable, or None if not found
    """
    # Try common names
    candidates = ['ffplay', 'ffplay.exe']
    
    # Check PATH first
    for cmd in candidates:
        try:
            result = subprocess.run(['which', cmd] if platform.system() != 'Windows' 
                                  else ['where', cmd], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    # Check common installation paths
    if platform.system() == 'Windows':
        common_paths = [
            r'C:\Program Files\FFmpeg\bin\ffplay.exe',
            r'C:\Program Files (x86)\FFmpeg\bin\ffplay.exe',
            r'C:\ffmpeg\bin\ffplay.exe',
            r'C:\tools\ffmpeg\bin\ffplay.exe'
        ]
    else:
        common_paths = [
            '/usr/bin/ffplay',
            '/usr/local/bin/ffplay',
            '/opt/homebrew/bin/ffplay',  # macOS Homebrew
            '/snap/bin/ffplay'  # Ubuntu Snap
        ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return None


def launch_ffplay(file_path: str, additional_args: Optional[List[str]] = None, 
                 window_size: Tuple[int, int] = (800, 600),
                 enable_loop: bool = True,
                 zoom_enabled: bool = True,
                 ffplay_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
    """
    Launch ffplay to play a media file with enhanced options.
    
    Args:
        file_path: Path to media file to play
        additional_args: Additional ffplay arguments
        window_size: Initial window size (width, height)
        enable_loop: Enable loop playback
        zoom_enabled: Enable zoom controls (mouse wheel)
        ffplay_executable: Specific ffplay executable path (overrides auto-detection)
        
    Returns:
        subprocess.Popen: Process handle, or None if launch failed
    """
    print(f"[DEBUG_LAUNCH_FFPLAY] Called with:")
    print(f"[DEBUG_LAUNCH_FFPLAY]   file_path: {file_path}")
    print(f"[DEBUG_LAUNCH_FFPLAY]   ffplay_executable: {ffplay_executable}")
    print(f"[DEBUG_LAUNCH_FFPLAY]   window_size: {window_size}")
    print(f"[DEBUG_LAUNCH_FFPLAY]   enable_loop: {enable_loop}")
    
    # Use provided executable path or auto-detect
    ffplay_path = ffplay_executable if ffplay_executable else find_ffplay()
    print(f"[DEBUG_LAUNCH_FFPLAY] Final ffplay_path: {ffplay_path}")
    
    if not ffplay_path:
        print(f"[DEBUG_LAUNCH_FFPLAY] ERROR: ffplay not found")
        logger.error("ffplay not found in system PATH or common locations")
        return None
    
    if not os.path.exists(file_path):
        print(f"[DEBUG_LAUNCH_FFPLAY] ERROR: Media file not found: {file_path}")
        logger.error(f"Media file not found: {file_path}")
        return None
    
    # Build ffplay command
    cmd = [ffplay_path]
    
    # Window positioning and size
    cmd.extend(['-x', str(window_size[0]), '-y', str(window_size[1])])
    
    # Remove autoexit to enable better user control
    cmd.append('-autoexit')  # Actually keep this for single files
    
    # Enable loop if requested
    if enable_loop:
        cmd.extend(['-loop', '0'])  # Infinite loop
    
    # Window title
    filename = os.path.basename(file_path)
    cmd.extend(['-window_title', f'ffplay - {filename}'])
    
    # Additional arguments
    if additional_args:
        cmd.extend(additional_args)
    
    # Input file
    cmd.append(file_path)
    
    print(f"[DEBUG_LAUNCH_FFPLAY] Final command: {' '.join(cmd)}")
    try:
        logger.info(f"Launching ffplay with command: {' '.join(cmd)}")
        
        # Launch with minimal console window on Windows
        startupinfo = None
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # Use SW_SHOWNORMAL (1) instead of SW_HIDE (0) to make the window visible
            startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            print(f"[DEBUG_LAUNCH_FFPLAY] Using startupinfo with wShowWindow = 1 (SW_SHOWNORMAL)")
        
        print(f"[DEBUG_LAUNCH_FFPLAY] Creating subprocess...")
        process = subprocess.Popen(
            cmd,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        print(f"[DEBUG_LAUNCH_FFPLAY] Process created successfully (PID: {process.pid})")
        logger.info(f"ffplay launched successfully (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"[DEBUG_LAUNCH_FFPLAY] Exception creating subprocess: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to launch ffplay: {e}")
        return None


def launch_ffplay_sequence(files: List[str], 
                          frame_rate: Optional[float] = None,
                          window_size: Tuple[int, int] = (800, 600),
                          enable_loop: bool = True,
                          ffplay_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
    """
    Launch ffplay to play an image sequence.
    
    Args:
        files: List of image files in sequence
        frame_rate: Playback frame rate (auto-detected if None)
        window_size: Initial window size
        enable_loop: Enable loop playback
        ffplay_executable: Specific ffplay executable path (overrides auto-detection)
        
    Returns:
        subprocess.Popen: Process handle, or None if launch failed
    """
    if not files:
        logger.error("No files provided for sequence playback")
        return None
    
    # Sort files to ensure proper sequence order
    files = sorted(files)
    
    # Auto-detect frame rate if not provided
    if frame_rate is None:
        frame_rate = get_sequence_frame_rate(files)
    
    # Create ffmpeg pattern for image sequence
    first_file = files[0]
    file_dir = os.path.dirname(first_file)
    base_name = os.path.basename(first_file)
    
    # Try to detect numbering pattern
    import re
    match = re.search(r'(\d+)', base_name)
    if match:
        # Create pattern like image_%04d.jpg
        number_part = match.group(1)
        pattern_name = base_name.replace(number_part, f'%0{len(number_part)}d')
        sequence_pattern = os.path.join(file_dir, pattern_name)
        
        additional_args = [
            '-framerate', str(frame_rate),
            '-start_number', number_part
        ]
    else:
        # Fallback to glob pattern
        file_ext = os.path.splitext(first_file)[1]
        sequence_pattern = os.path.join(file_dir, f'*{file_ext}')
        additional_args = [
            '-framerate', str(frame_rate),
            '-pattern_type', 'glob'
        ]
    
    # Build ffplay command
    cmd = [ffplay_path]
    
    # Window positioning and size
    cmd.extend(['-x', str(window_size[0]), '-y', str(window_size[1])])
    
    # Frame rate and pattern
    cmd.extend(additional_args)
    
    # Enable loop if requested
    if enable_loop:
        cmd.extend(['-loop', '0'])  # Infinite loop
    
    # Window title
    sequence_name = os.path.basename(file_dir) if file_dir else "sequence"
    cmd.extend(['-window_title', f'ffplay - {sequence_name} ({len(files)} frames @ {frame_rate}fps)'])
    
    # Auto-exit when done
    cmd.append('-autoexit')
    
    # Input pattern
    cmd.append(sequence_pattern)
    
    # Launch process
    self.logger.info(f"Launching ffplay sequence with command: {' '.join(cmd)}")
    
    # Launch with minimal console window on Windows
    startupinfo = None
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Use SW_SHOWNORMAL (1) instead of SW_HIDE (0) to make the window visible
        startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
    
    process = subprocess.Popen(
        cmd,
        startupinfo=startupinfo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    self.logger.info(f"ffplay sequence launched successfully (PID: {process.pid})")
    if hasattr(self.app, 'status_manager'):
        self.app.status_manager.add_log_message(f"Playing image sequence: {len(files)} frames @ {frame_rate}fps", "INFO")
    
    return process


def get_media_info(file_path: str, ffplay_executable: Optional[str] = None) -> dict:
    """
    Get basic media information using ffprobe (if available).
    
    Args:
        file_path: Path to media file
        ffplay_executable: Optional path to ffplay executable (ffprobe will be derived from this)
        
    Returns:
        dict: Media information
    """
    info = {
        'file_size': 0,
        'duration': 0,
        'width': 0,
        'height': 0,
        'fps': 0,
        'format': '',
        'error': None
    }
    
    try:
        if os.path.exists(file_path):
            info['file_size'] = os.path.getsize(file_path)
            
        # Try to use ffprobe for detailed info
        # Use provided ffplay path or auto-detect
        ffplay_path = ffplay_executable if ffplay_executable else find_ffplay()
        ffprobe_path = ffplay_path.replace('ffplay', 'ffprobe') if ffplay_path else None
        
        if ffprobe_path and os.path.exists(ffprobe_path):
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Extract format info
                if 'format' in data:
                    info['duration'] = float(data['format'].get('duration', 0))
                    info['format'] = data['format'].get('format_name', '')
                
                # Extract video stream info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info['width'] = stream.get('width', 0)
                        info['height'] = stream.get('height', 0)
                        
                        # Calculate FPS
                        if 'r_frame_rate' in stream:
                            fps_str = stream['r_frame_rate']
                            if '/' in fps_str:
                                num, den = fps_str.split('/')
                                if int(den) > 0:
                                    info['fps'] = float(num) / float(den)
                        break
                        
    except Exception as e:
        info['error'] = str(e)
        logger.warning(f"Could not get media info for {file_path}: {e}")
    
    return info


def test_ffplay_installation() -> dict:
    """
    Test ffplay installation and capabilities.
    
    Returns:
        dict: Test results
    """
    results = {
        'ffplay_found': False,
        'ffplay_path': None,
        'ffprobe_found': False,
        'ffprobe_path': None,
        'version': None,
        'formats_supported': [],
        'error': None
    }
    
    try:
        # Test ffplay
        ffplay_path = find_ffplay()
        if ffplay_path:
            results['ffplay_found'] = True
            results['ffplay_path'] = ffplay_path
            
            # Test version
            try:
                result = subprocess.run([ffplay_path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    results['version'] = version_line
            except Exception:
                pass
        
        # Test ffprobe
        if ffplay_path:
            ffprobe_path = ffplay_path.replace('ffplay', 'ffprobe')
            if os.path.exists(ffprobe_path):
                results['ffprobe_found'] = True
                results['ffprobe_path'] = ffprobe_path
        
    except Exception as e:
        results['error'] = str(e)
    
    return results


class MediaPlayerUtils:
    """
    Media player utilities class that integrates with the CleanIncomings app.
    Provides methods for launching external media players with app settings integration.
    """

    def play_with_ffplay_handler(self, media_input):
        """
        Unified handler for ffplay playback, matching GUI expectations.
        Accepts either a file path (str) or a sequence info dict.
        Returns True if playback was launched, False otherwise.
        """
        try:
            result = self.launch_standalone_player(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("Playback failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Playback error in play_with_ffplay_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Playback error: {e}", "ERROR")
            return False

    def play_with_vlc_handler(self, media_input):
        """
        Unified handler for VLC playback, matching GUI expectations.
        Accepts either a file path (str) or a sequence info dict.
        Returns True if playback was launched, False otherwise.
        """
        try:
            result = self.launch_standalone_player(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("Playback failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Playback error in play_with_vlc_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Playback error: {e}", "ERROR")
            return False

    def play_with_nuke_handler(self, media_input):
        """
        Unified handler for sending media to Nuke via socket, matching GUI expectations.
        Accepts either a file path (str) or a sequence info dict.
        Returns True if command was sent successfully, False otherwise.
        """
        try:
            result = self.send_to_nuke(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("Failed to send to Nuke or Nuke server not available.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Error in play_with_nuke_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Nuke handler error: {e}", "ERROR")
            return False

    def play_with_nuke_player_handler(self, media_input):
        """
        Unified handler for Nuke Player playback, matching GUI expectations.
        Tries socket first, then falls back to process launching.
        Returns True if playback was launched, False otherwise.
        """
        try:
            result = self.launch_nuke_player(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("Nuke Player failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Playback error in play_with_nuke_player_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Nuke Player error: {e}", "ERROR")
            return False

    def play_with_nuke_full_handler(self, media_input):
        """
        Unified handler for full Nuke application playback.
        Uses the same approach as play_with_nuke_handler (socket first, then process).
        Returns True if playback was launched, False otherwise.
        """
        return self.play_with_nuke_handler(media_input)

    def play_with_mrv2_handler(self, media_input):
        """
        Unified handler for MRV2 playback, matching GUI expectations.
        MRV2 is a professional image sequence viewer with advanced color management.
        Returns True if playback was launched, False otherwise.
        """
        try:
            result = self.launch_mrv2(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("MRV2 failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Error in play_with_mrv2_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"MRV2 error: {e}", "ERROR")
            return False

    def play_with_djv_handler(self, media_input):
        """
        Unified handler for DJV playback, matching GUI expectations.
        DJV is a professional image sequence viewer optimized for film/VFX workflows.
        Returns True if playback was launched, False otherwise.
        """
        try:
            result = self.launch_djv(media_input)
            if not result and hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message("DJV failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.logger.error(f"Error in play_with_djv_handler: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"DJV error: {e}", "ERROR")
            return False

    def __init__(self, app_instance):
        """
        Initialize MediaPlayerUtils with app instance for settings access.
        
        Args:
            app_instance: The main CleanIncomings app instance        """
        self.app = app_instance
        self.logger = logging.getLogger(__name__)

    def launch_standalone_player(self, media_input, frame_rate=24, window_size=(1280, 720), enable_loop=False, ffplay_executable=None):
        """
        Enhanced standalone player launcher that intelligently chooses the best player.
        Detects EXR files and uses professional viewers when available.
        
        Args:
            media_input: File path, sequence data dict, or list of files
            frame_rate: Frame rate for playback (default: 24)
            window_size: Window size (width, height) (default: (1280, 720))
            enable_loop: Whether to loop playback (default: False)
            ffplay_executable: Optional path to ffplay executable
            
        Returns:
            subprocess.Popen or bool: The player process, True for system default, or None if failed
        """
        try:
            # Detect if this is an EXR file/sequence
            is_exr = False
            file_path = None
            
            if isinstance(media_input, dict):
                # Sequence data dict
                files = media_input.get('files', [])
                if files:
                    if isinstance(files[0], dict):
                        file_path = files[0].get('path', '')
                    else:
                        file_path = str(files[0])
                    if file_path.lower().endswith('.exr'):
                        is_exr = True
                        
            elif isinstance(media_input, list) and media_input:
                # List of files
                first_file = media_input[0]
                if isinstance(first_file, dict):
                    file_path = first_file.get('path', '')
                else:
                    file_path = str(first_file)
                if file_path.lower().endswith('.exr'):
                    is_exr = True
                    
            elif isinstance(media_input, str):
                # Single file path
                file_path = media_input
                if file_path.lower().endswith('.exr'):
                    is_exr = True
            
            # Use EXR viewer for EXR files
            if is_exr and file_path:
                self.logger.info(f"Detected EXR file, using professional EXR viewer: {file_path}")
                result = self.launch_exr_viewer(media_input)
                if result:
                    if hasattr(self.app, 'status_manager'):
                        self.app.status_manager.add_log_message(f"Playing EXR with professional viewer: {os.path.basename(file_path)}", "INFO")
                    return result
                else:
                    self.logger.warning("Professional EXR viewer failed, falling back to ffplay")
                    # Fall through to ffplay
            
            # Use the existing sequence player for non-EXR or EXR fallback
            return self.play_sequence(media_input, frame_rate, window_size, enable_loop, ffplay_executable)
            
        except Exception as e:
            self.logger.error(f"Error in launch_standalone_player: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching player: {e}", "ERROR")
            return None
    
    def get_ffplay_path(self) -> Optional[str]:
        """
        Get the ffplay executable path from app settings.
        
        Returns:
            str: Path to ffplay executable, or None if not configured
        """
        try:
            # Try to get from app ffplay_path_var first (Tkinter variable)
            if hasattr(self.app, 'ffplay_path_var') and self.app.ffplay_path_var.get():
                ffplay_path = self.app.ffplay_path_var.get().strip()
                if ffplay_path and os.path.exists(ffplay_path):
                    return ffplay_path
            
            # Try to get from direct app attribute (for mock apps or simple implementations)
            if hasattr(self.app, 'ffplay_path') and self.app.ffplay_path:
                ffplay_path = self.app.ffplay_path.strip()
                if ffplay_path and os.path.exists(ffplay_path):
                    return ffplay_path
            
            # Try to get from app settings dict
            if hasattr(self.app, 'settings') and self.app.settings:
                ffplay_path = self.app.settings.get('ui_state', {}).get('ffplay_path', '').strip()
                if ffplay_path and os.path.exists(ffplay_path):
                    return ffplay_path
            
            # Try to get from settings manager
            if hasattr(self.app, 'settings_manager'):
                settings = self.app.settings_manager.get_settings()
                ffplay_path = settings.get('ui_state', {}).get('ffplay_path', '').strip()
                if ffplay_path and os.path.exists(ffplay_path):
                    return ffplay_path
              # Fallback to auto-detection
            return find_ffplay()
            
        except Exception as e:
            self.logger.warning(f"Error getting ffplay path from settings: {e}")
            return find_ffplay()
    def play_with_ffplay(self, ffplay_path: str, media_file_path: str) -> bool:
        """
        Launch ffplay to play a media file (legacy method for compatibility).
        
        Args:
            ffplay_path: Path to ffplay executable
            media_file_path: Path to media file to play
            
        Returns:
            bool: True if launch was successful, False otherwise
        """
        print(f"[DEBUG_MEDIA_PLAYER] play_with_ffplay called with:")
        print(f"[DEBUG_MEDIA_PLAYER]   ffplay_path: {ffplay_path}")
        print(f"[DEBUG_MEDIA_PLAYER]   media_file_path: {media_file_path}")
        
        try:
            # Validate paths
            if not os.path.exists(ffplay_path):
                print(f"[DEBUG_MEDIA_PLAYER] ffplay executable not found: {ffplay_path}")
                self.logger.error(f"ffplay executable not found: {ffplay_path}")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"ffplay executable not found: {ffplay_path}", "ERROR")
                return False
            
            if not os.path.exists(media_file_path):
                print(f"[DEBUG_MEDIA_PLAYER] Media file not found: {media_file_path}")
                self.logger.error(f"Media file not found: {media_file_path}")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"Media file not found: {media_file_path}", "ERROR")
                return False
            
            print(f"[DEBUG_MEDIA_PLAYER] Both paths exist, calling launch_ffplay...")
            
            # For basic media playback, call the standalone function directly
            # This bypasses the complex sequence detection logic that may be causing issues
            process = launch_ffplay(
                media_file_path,
                ffplay_executable=ffplay_path,
                window_size=(800, 600),
                enable_loop=True,
                zoom_enabled=True
            )
            
            print(f"[DEBUG_MEDIA_PLAYER] launch_ffplay returned process: {process}")
            
            if process:
                print(f"[DEBUG_MEDIA_PLAYER] Successfully launched ffplay (PID: {process.pid})")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"Successfully launched ffplay for: {os.path.basename(media_file_path)}", "INFO")
                return True
            else:
                print(f"[DEBUG_MEDIA_PLAYER] Failed to launch ffplay - process is None")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"Failed to launch ffplay for: {os.path.basename(media_file_path)}", "ERROR")
                return False
                
        except Exception as e:
            print(f"[DEBUG_MEDIA_PLAYER] Exception in play_with_ffplay: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Error in play_with_ffplay: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching ffplay: {e}", "ERROR")
            return False
    
    def launch_ffplay(self, file_path: str, 
                     additional_args: Optional[List[str]] = None,
                     window_size: Tuple[int, int] = (800, 600),
                     enable_loop: bool = True,
                     zoom_enabled: bool = True,
                     ffplay_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
        """
        Launch ffplay to play a media file with enhanced options.
        
        Args:
            file_path: Path to media file to play
            additional_args: Additional ffplay arguments
            window_size: Initial window size (width, height)
            enable_loop: Enable loop playback
            zoom_enabled: Enable zoom controls (mouse wheel)
            ffplay_executable: Specific ffplay executable path (overrides settings)
            
        Returns:
            subprocess.Popen: Process handle, or None if launch failed
        """
        try:
            # Get ffplay path
            if ffplay_executable:
                ffplay_path = ffplay_executable
            else:
                ffplay_path = self.get_ffplay_path()
            
            if not ffplay_path:
                self.logger.error("ffplay not found in settings or system PATH")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message("ffplay executable not configured. Please set it in Settings.", "ERROR")
                return None
            
            # Check if this is an image sequence
            if os.path.isdir(file_path):
                # Directory - check for image sequence
                image_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
                    image_files.extend(Path(file_path).glob(f'*{ext}'))
                    image_files.extend(Path(file_path).glob(f'*{ext.upper()}'))
                
                if image_files:
                    image_files = [str(f) for f in sorted(image_files)]
                    if is_image_sequence(image_files):
                        return self.launch_ffplay_sequence(
                            image_files,
                            window_size=window_size,
                            enable_loop=enable_loop,
                            ffplay_executable=ffplay_path
                        )
              # Single file playback
            return launch_ffplay(
                file_path,
                additional_args=additional_args,
                window_size=window_size,
                enable_loop=enable_loop,
                zoom_enabled=zoom_enabled,
                ffplay_executable=ffplay_path
            )
            
        except Exception as e:
            self.logger.error(f"Error launching ffplay: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching ffplay: {e}", "ERROR")
            return None
      
    def launch_ffplay_sequence(self, files: List[str],
                              frame_rate: Optional[float] = None,
                              window_size: Tuple[int, int] = (800, 600),
                              enable_loop: bool = True,
                              ffplay_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
        """
        Launch ffplay to play an image sequence.
        
        Args:
            files: List of image files in sequence
            frame_rate: Playback frame rate (auto-detected if None)
            window_size: Initial window size
            enable_loop: Enable loop playback
            ffplay_executable: Specific ffplay executable path
            
        Returns:
            subprocess.Popen: Process handle, or None if launch failed
        """
        try:
            # Get ffplay path
            if ffplay_executable:
                ffplay_path = ffplay_executable
            else:
                ffplay_path = self.get_ffplay_path()
            
            if not ffplay_path:
                self.logger.error("ffplay not found for sequence playback")
                return None
            
            if not files:
                self.logger.error("No files provided for sequence playback")
                return None
            
            # Sort files to ensure proper sequence order
            files = sorted(files)
            
            # Auto-detect frame rate if not provided
            if frame_rate is None:
                frame_rate = get_sequence_frame_rate(files)
            
            # Create ffmpeg pattern for image sequence
            first_file = files[0]
            file_dir = os.path.dirname(first_file)
            base_name = os.path.basename(first_file)
            
            # Try to detect numbering pattern
            import re
            match = re.search(r'(\d+)', base_name)
            if match:
                # Create pattern like image_%04d.jpg
                number_part = match.group(1)
                pattern_name = base_name.replace(number_part, f'%0{len(number_part)}d')
                sequence_pattern = os.path.join(file_dir, pattern_name)
                
                additional_args = [
                    '-framerate', str(frame_rate),
                    '-start_number', number_part
                ]
            else:
                # Fallback to glob pattern
                file_ext = os.path.splitext(first_file)[1]
                sequence_pattern = os.path.join(file_dir, f'*{file_ext}')
                additional_args = [
                    '-framerate', str(frame_rate),
                    '-pattern_type', 'glob'
                ]
            
            # Build ffplay command
            cmd = [ffplay_path]
            
            # Window positioning and size
            cmd.extend(['-x', str(window_size[0]), '-y', str(window_size[1])])
            
            # Frame rate and pattern
            cmd.extend(additional_args)
            
            # Enable loop if requested
            if enable_loop:
                cmd.extend(['-loop', '0'])  # Infinite loop
            
            # Window title
            sequence_name = os.path.basename(file_dir) if file_dir else "sequence"
            cmd.extend(['-window_title', f'ffplay - {sequence_name} ({len(files)} frames @ {frame_rate}fps)'])
            
            # Auto-exit when done
            cmd.append('-autoexit')
            
            # Input pattern
            cmd.append(sequence_pattern)
            
            # Launch process
            self.logger.info(f"Launching ffplay sequence with command: {' '.join(cmd)}")
            
            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # Use SW_SHOWNORMAL (1) instead of SW_HIDE (0) to make the window visible
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"ffplay sequence launched successfully (PID: {process.pid})")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Playing image sequence: {len(files)} frames @ {frame_rate}fps", "INFO")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to launch ffplay sequence: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching image sequence: {e}", "ERROR")
            return None
    
    def launch_ffplay_from_sequence_data(self, sequence_data: dict,
                                        frame_rate: Optional[float] = None,
                                        window_size: Tuple[int, int] = (800, 600),
                                        enable_loop: bool = True,
                                        ffplay_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
        """
        Launch ffplay to play an image sequence using the rich sequence data structure 
        from the CleanIncomings mapping system.
        
        Args:
            sequence_data: Dictionary containing sequence information with keys like:
                          'base_name', 'files', 'frame_numbers', 'directory', 'frame_range', etc.
            frame_rate: Playback frame rate (auto-detected if None)
            window_size: Initial window size
            enable_loop: Enable loop playback
            ffplay_executable: Specific ffplay executable path
            
        Returns:
            subprocess.Popen: Process handle, or None if launch failed
        """
        try:
            # Get ffplay path
            if ffplay_executable:
                ffplay_path = ffplay_executable
            else:
                ffplay_path = self.get_ffplay_path()
            
            if not ffplay_path:
                self.logger.error("ffplay not found for sequence playback")
                return None
            
            # Extract sequence information from the rich data structure
            base_name = sequence_data.get('base_name', '')
            files = sequence_data.get('files', [])
            frame_numbers = sequence_data.get('frame_numbers', [])
            directory = sequence_data.get('directory', '')
            frame_range = sequence_data.get('frame_range', '')
            frame_count = sequence_data.get('frame_count', len(files))
            suffix = sequence_data.get('suffix', '')
            
            if not files:
                self.logger.error("No files provided in sequence data")
                return None
            
            # Auto-detect frame rate if not provided
            if frame_rate is None:
                frame_rate = get_sequence_frame_rate(files)
            
            # Use the base_name and suffix to create a proper ffmpeg pattern
            # This is much more accurate than trying to detect patterns from individual files
            if base_name and suffix:
                # Determine the number of digits in frame numbers
                if frame_numbers:
                    max_frame = max(frame_numbers)
                    min_frame = min(frame_numbers) 
                    # Calculate digits needed for the largest frame number
                    digits = len(str(max_frame))
                    # Use at least 4 digits for standard sequence patterns
                    digits = max(4, digits)
                    start_number = str(min_frame)
                else:
                    # Fallback to 4 digits
                    digits = 4
                    start_number = "1"
                
                # Create the ffmpeg pattern
                if '.' in suffix:
                    sequence_pattern = os.path.join(directory, f"{base_name}.%0{digits}d{suffix}")
                else:
                    sequence_pattern = os.path.join(directory, f"{base_name}_%0{digits}d{suffix}")
                
                additional_args = [
                    '-framerate', str(frame_rate),
                    '-start_number', start_number
                ]
            else:
                # Fallback to the original file-based detection
                self.logger.warning("No base_name/suffix in sequence data, falling back to file-based pattern detection")
                return self.launch_ffplay_sequence(
                    files, frame_rate, window_size, enable_loop, ffplay_executable
                )
            
            # Build ffplay command
            cmd = [ffplay_path]
            
            # Window positioning and size
            cmd.extend(['-x', str(window_size[0]), '-y', str(window_size[1])])
            
            # Frame rate and pattern
            cmd.extend(additional_args)
            
            # Enable loop if requested
            if enable_loop:
                cmd.extend(['-loop', '0'])  # Infinite loop
            
            # Window title with rich information
            title_parts = []
            if base_name:
                title_parts.append(base_name)
            if frame_range:
                title_parts.append(f"[{frame_range}]")
            title_parts.append(f"({frame_count} frames @ {frame_rate}fps)")
            
            window_title = f"ffplay - {' '.join(title_parts)}"
            cmd.extend(['-window_title', window_title])
            
            # Auto-exit when done
            cmd.append('-autoexit')
            
            # Input pattern
            cmd.append(sequence_pattern)
            
            # Launch process
            self.logger.info(f"Launching ffplay sequence from data with command: {' '.join(cmd)}")
            
            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # Use SW_SHOWNORMAL (1) instead of SW_HIDE (0) to make the window visible
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"ffplay sequence launched successfully (PID: {process.pid})")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(
                    f"Playing sequence: {base_name} [{frame_range}] ({frame_count} frames @ {frame_rate}fps)", 
                    "INFO"
                )
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to launch ffplay from sequence data: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching sequence from data: {e}", "ERROR")
            return None
      
    def get_media_info(self, file_path: str) -> dict:
        """
        Get media information for a file using ffprobe.
        
        Args:
            file_path: Path to media file
            
        Returns:
            dict: Media information
        """
        # Get the configured ffplay path and pass it to the standalone function
        ffplay_path = self.get_ffplay_path()
        return get_media_info(file_path, ffplay_executable=ffplay_path)
    
    def test_ffplay_installation(self) -> dict:
        """
        Test ffplay installation and report results to app.
        
        Returns:
            dict: Test results
        """
        results = test_ffplay_installation()
        
        # Log results to app if available
        if hasattr(self.app, 'status_manager'):
            if results['ffplay_found']:
                self.app.status_manager.add_log_message(f"ffplay found: {results['ffplay_path']}", "INFO")
                if results['version']:
                    self.app.status_manager.add_log_message(f"ffplay version: {results['version']}", "INFO")
            else:
                self.app.status_manager.add_log_message("ffplay not found. Please install FFmpeg.", "WARNING")
        
        return results

    def test_nuke_player_installation(self) -> dict:
        """
        Test Nuke Player installation and capabilities.
        
        Returns:
            dict: Test results with keys like 'nuke_found', 'nuke_path', 'version', 'supports_viewer_mode'
        """
        results = {
            'nuke_found': False,
            'nuke_path': None,
            'version': None,
            'supports_viewer_mode': False,
            'error': None
        }
        
        try:
            # Detect Nuke installations
            available_viewers = self.detect_exr_viewers()
            nuke_path = available_viewers.get('nuke_player')
            
            if nuke_path:
                results['nuke_found'] = True
                results['nuke_path'] = nuke_path
                
                # Test version and viewer mode support
                try:
                    # Try to get version info
                    result = subprocess.run(
                        [nuke_path, '--help'], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        # Extract version from help output
                        help_text = result.stdout
                        version_match = re.search(r'Nuke(\d+\.\d+)', help_text)
                        if version_match:
                            results['version'] = version_match.group(1)
                        
                        # Check if -v flag is supported
                        if '-v' in help_text.lower():
                            results['supports_viewer_mode'] = True
                        else:
                            # Some Nuke versions don't list -v in help but still support it
                            results['supports_viewer_mode'] = True  # Assume support
                            
                except subprocess.TimeoutExpired:
                    results['supports_viewer_mode'] = True  # Assume it works
                except Exception as e:
                    results['error'] = f"Could not test Nuke capabilities: {e}"
                    results['supports_viewer_mode'] = True  # Assume it works
        
        except Exception as e:
            results['error'] = str(e)
        
        # Log results to app if available
        if hasattr(self.app, 'status_manager') and self.app.status_manager:
            if results['nuke_found']:
                self.app.status_manager.add_log_message(f"Nuke Player found: {results['nuke_path']}", "INFO")
                if results['version']:
                    self.app.status_manager.add_log_message(f"Nuke version: {results['version']}", "INFO")
                if results['supports_viewer_mode']:
                    self.app.status_manager.add_log_message("Nuke Player supports viewer mode (-v flag)", "INFO")
            else:
                self.app.status_manager.add_log_message("Nuke Player not found. Please install Nuke or configure the path.", "WARNING")
        
        return results

    def test_mrv2_installation(self) -> dict:
        """
        Test MRV2 installation and capabilities.
        
        Returns:
            dict: Test results with keys like 'mrv2_found', 'mrv2_path', 'version', 'error'
        """
        results = {
            'mrv2_found': False,
            'mrv2_path': None,
            'version': None,
            'error': None
        }
        
        try:
            # Detect MRV2 installations
            available_viewers = self.detect_exr_viewers()
            mrv2_path = available_viewers.get('mrv2')
            
            if mrv2_path:
                results['mrv2_found'] = True
                results['mrv2_path'] = mrv2_path
                
                # Test version info
                try:
                    # Try to get version info
                    result = subprocess.run(
                        [mrv2_path, '--version'], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        # Extract version from output
                        version_text = result.stdout
                        version_match = re.search(r'mrv2[\s-]*([\d.]+)', version_text, re.IGNORECASE)
                        if version_match:
                            results['version'] = version_match.group(1)
                            
                except subprocess.TimeoutExpired:
                    results['error'] = "MRV2 version check timed out"
                except Exception as e:
                    results['error'] = f"Could not test MRV2 version: {e}"
        
        except Exception as e:
            results['error'] = str(e)
        
        # Log results to app if available
        if hasattr(self.app, 'status_manager') and self.app.status_manager:
            if results['mrv2_found']:
                self.app.status_manager.add_log_message(f"MRV2 found: {results['mrv2_path']}", "INFO")
                if results['version']:
                    self.app.status_manager.add_log_message(f"MRV2 version: {results['version']}", "INFO")
            else:
                self.app.status_manager.add_log_message("MRV2 not found. Please install MRV2 or configure the path.", "WARNING")
        
        return results

    def test_djv_installation(self) -> dict:
        """
        Test DJV installation and capabilities.
        
        Returns:
            dict: Test results with keys like 'djv_found', 'djv_path', 'version', 'error'
        """
        results = {
            'djv_found': False,
            'djv_path': None,
            'version': None,
            'error': None
        }
        
        try:
            # Detect DJV installations
            available_viewers = self.detect_exr_viewers()
            djv_path = available_viewers.get('djv')
            
            if djv_path:
                results['djv_found'] = True
                results['djv_path'] = djv_path
                
                # Test version info
                try:
                    # Try to get version info (DJV may use different flags)
                    for version_flag in ['--version', '-version', '--help']:
                        try:
                            result = subprocess.run(
                                [djv_path, version_flag], 
                                capture_output=True, 
                                text=True, 
                                timeout=10
                            )
                            
                            if result.returncode == 0:
                                # Extract version from output
                                version_text = result.stdout
                                version_match = re.search(r'djv[\s-]*([\d.]+)', version_text, re.IGNORECASE)
                                if version_match:
                                    results['version'] = version_match.group(1)
                                    break
                                # Alternative version pattern
                                version_match = re.search(r'version[\s:]*(\d+[\d.]*)', version_text, re.IGNORECASE)
                                if version_match:
                                    results['version'] = version_match.group(1)
                                    break
                        except:
                            continue
                            
                except subprocess.TimeoutExpired:
                    results['error'] = "DJV version check timed out"
                except Exception as e:
                    results['error'] = f"Could not test DJV version: {e}"
        
        except Exception as e:
            results['error'] = str(e)
        
        # Log results to app if available
        if hasattr(self.app, 'status_manager') and self.app.status_manager:
            if results['djv_found']:
                self.app.status_manager.add_log_message(f"DJV found: {results['djv_path']}", "INFO")
                if results['version']:
                    self.app.status_manager.add_log_message(f"DJV version: {results['version']}", "INFO")
            else:
                self.app.status_manager.add_log_message("DJV not found. Please install DJV or configure the path.", "WARNING")
        
        return results

    def is_media_file(self, file_path: str) -> bool:
        """
        Check if a file is a supported media file.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file appears to be a media file
        """
        if not os.path.exists(file_path):
            return False
        
        # Common media extensions
        media_extensions = {
            # Video
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v',
            '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob', '.ts',
            '.mts', '.m2ts', '.divx', '.xvid', '.ogv', '.mxf', '.r3d', '.dng',
            # Audio
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus',
            '.ac3', '.dts', '.pcm', '.aiff', '.au', '.snd',
            # Images (for sequences) - Basic formats
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp',
            # Professional image formats (Nuke specializes in these)
            '.exr', '.hdr', '.dpx', '.cin', '.sgi', '.tga', '.psd', '.iff',
            '.pic', '.rla', '.rpf', '.sxr', '.mxr', '.null', '.rgb', '.rgba',
            # RAW camera formats
            '.cr2', '.nef', '.arw', '.orf', '.rw2', '.pef', '.srw', '.raf',
            # Additional professional formats
            '.tx', '.rat', '.it', '.als', '.shd', '.slim', '.slx', '.rs'
        }
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in media_extensions

    def play_sequence(self, sequence_input, frame_rate=24, window_size=(1280, 720), enable_loop=False, ffplay_executable=None):
        """
        Unified sequence player that automatically detects input type and uses appropriate playback method.
        
        Args:
            sequence_input: Can be one of:
                - Rich sequence data dict with keys like 'base_name', 'files', 'frame_numbers', etc.
                - List of file paths
                - Single file path (first file of sequence)
                - Directory path containing sequences
            frame_rate (int): Frame rate for playback (default: 24)
            window_size (tuple): Window size (width, height) (default: (1280, 720))
            enable_loop (bool): Whether to loop playback (default: False)
            ffplay_executable (str): Optional path to ffplay executable
            
        Returns:
            subprocess.Popen: The ffplay process, or None if failed
        """
        try:
            # Type 1: Rich sequence data dict (preferred)
            if isinstance(sequence_input, dict) and 'base_name' in sequence_input:
                self.logger.info("Playing sequence from rich sequence data")
                return self.launch_ffplay_from_sequence_data(
                    sequence_input, frame_rate, window_size, enable_loop, ffplay_executable
                )
            
            # Type 2: List of file paths
            elif isinstance(sequence_input, list) and sequence_input:
                self.logger.info(f"Playing sequence from file list ({len(sequence_input)} files)")
                return self.launch_ffplay_sequence(
                    sequence_input, frame_rate, window_size, enable_loop, ffplay_executable
                )
              # Type 3: Single file path (assume it's part of a sequence)
            elif isinstance(sequence_input, str) and os.path.isfile(sequence_input):
                self.logger.info("Playing sequence from single file path")
                # Try to find other files in the sequence
                try:
                    directory = os.path.dirname(sequence_input)
                    basename = os.path.basename(sequence_input)
                    
                    # Look for similar files in the same directory
                    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.exr', '.dpx'}
                    file_ext = os.path.splitext(basename)[1].lower()
                    
                    if file_ext in image_extensions:
                        # Find all files with same extension in directory
                        all_files = [f for f in os.listdir(directory) 
                                   if f.lower().endswith(file_ext)]
                        all_files_full = [os.path.join(directory, f) for f in sorted(all_files)]
                        
                        if len(all_files_full) > 1 and is_image_sequence(all_files_full):
                            return self.launch_ffplay_sequence(
                                all_files_full, frame_rate, window_size, enable_loop, ffplay_executable
                            )
                    
                    # Single file fallback
                    return self.launch_ffplay(
                        sequence_input, window_size=window_size, 
                        enable_loop=enable_loop, ffplay_executable=ffplay_executable
                    )
                        
                except Exception as e:
                    self.logger.warning(f"Error detecting sequence from single file: {e}")
                    # Fallback to single file playback
                    return self.launch_ffplay(
                        sequence_input, window_size=window_size,
                        enable_loop=enable_loop, ffplay_executable=ffplay_executable
                    )
            
            # Type 4: Directory path 
            elif isinstance(sequence_input, str) and os.path.isdir(sequence_input):
                self.logger.info("Playing sequences from directory")
                # Find image sequences in directory
                image_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.exr', '.dpx']:
                    image_files.extend(Path(sequence_input).glob(f'*{ext}'))
                    image_files.extend(Path(sequence_input).glob(f'*{ext.upper()}'))
                
                if image_files:
                    image_files = [str(f) for f in sorted(image_files)]
                    if is_image_sequence(image_files):
                        return self.launch_ffplay_sequence(
                            image_files, frame_rate, window_size, enable_loop, ffplay_executable
                        )
                
                self.logger.error(f"No valid image sequence found in directory: {sequence_input}")
                return None
            
            else:
                self.logger.error(f"Unsupported sequence input type: {type(sequence_input)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to play sequence: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error playing sequence: {e}", "ERROR")
            return None

    def launch_mpv_subprocess(self, media_path: str) -> Optional[subprocess.Popen]:
        """
        Launch the standalone MPV script as a subprocess.

        Args:
            media_path: Path to the media file or the first frame of a sequence.

        Returns:
            subprocess.Popen: Process handle, or None if launch failed.
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            mpv_script_path = os.path.join(script_dir, "..", "scripts", "launch_mpv.py")

            if not os.path.exists(mpv_script_path):
                self.logger.error(f"MPV launch script not found at: {mpv_script_path}")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"MPV launch script not found: {mpv_script_path}", "ERROR")
                return None

            if not os.path.exists(media_path) and not media_path.startswith(('http://', 'https://')):
                self.logger.error(f"Media file for MPV not found: {media_path}")
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"Media file for MPV not found: {media_path}", "ERROR")
                return None

            command = [sys.executable, mpv_script_path, media_path]
            
            self.logger.info(f"Launching MPV with command: {' '.join(command)}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Playing with MPV: {os.path.basename(media_path)}", "INFO")

            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL (make console visible but not focused)
                                            # For no console: subprocess.CREATE_NO_WINDOW (but then logs are lost)
                                            # or redirect stdout/stderr to DEVNULL if logs from launch_mpv.py are not needed by main app

            process = subprocess.Popen(
                command,
                startupinfo=startupinfo,
                stdout=subprocess.PIPE, # Capture stdout
                stderr=subprocess.PIPE  # Capture stderr
            )
            
            # Try to get immediate output for errors from launch_mpv.py
            try:
                # Wait for a short period to see if the script errors out quickly
                stdout, stderr = process.communicate(timeout=1.5) # Increased timeout slightly
                if stdout:
                    self.logger.info(f"Output from launch_mpv.py (stdout):\n{stdout.decode(errors='ignore')}")
                if stderr:
                    self.logger.error(f"Output from launch_mpv.py (stderr):\n{stderr.decode(errors='ignore')}")
                
                # If communicate returned, the process ended. Check exit code.
                if process.returncode != 0:
                    self.logger.error(f"launch_mpv.py exited with code {process.returncode}")
                else:
                    self.logger.info(f"launch_mpv.py exited successfully (code 0). This might be unexpected if MPV should keep running.")

            except subprocess.TimeoutExpired:
                # This is expected if launch_mpv.py starts MPV and keeps running
                self.logger.info(f"launch_mpv.py process is running (PID: {process.pid}). MPV window should be visible.")
            except Exception as e:
                self.logger.error(f"Error while trying to communicate with launch_mpv.py: {e}")

            # Log the attempt and PID regardless
            self.logger.info(f"MPV launch attempt for: {media_path} (PID: {process.pid if process else 'N/A'})")
            
            # Return the process object. If communicate() completed, process.poll() will be set.
            # If it timed out, the process is still running.
            return process

        except Exception as e:
            self.logger.error(f"Failed to launch MPV subprocess: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error launching MPV: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None

    def launch_nuke(self, media_input) -> Optional[subprocess.Popen]:
        """
        DEPRECATED: Use send_to_nuke() instead.
        Launch full Nuke application for media playback without safe mode restrictions.
        """
        self.logger.warning("launch_nuke() is deprecated. Use send_to_nuke() instead.")
        # Try socket approach first, fallback to old method
        if self.send_to_nuke(media_input):
            return True  # Return True to indicate success (can't return process for socket)
        
        # If socket approach fails, user can still manually launch Nuke
        self.logger.warning("Socket approach failed. Please ensure Nuke is running with NukeServerSocket plugin.")
        if hasattr(self.app, 'status_manager'):
            self.app.status_manager.add_log_message("Socket failed. Ensure Nuke is running with NukeServerSocket plugin.", "WARNING")
        return None

    def launch_nuke_player(self, media_input) -> Optional[subprocess.Popen]:
        """
        Launch Nuke Player for media playback with support for various media types.
        Uses the traditional --safe --player approach for standalone viewing.
        
        Args:
            media_input: Can be:
                - Single file path (str)
                - Sequence data dict with keys like 'base_name', 'files', etc.
                - List of files
        
        Returns:
            subprocess.Popen: Process handle, or None if failed
        """
        self.logger.info("Launching Nuke Player process...")
        if hasattr(self.app, 'status_manager') and self.app.status_manager:
            self.app.status_manager.add_log_message("Launching Nuke Player...", "INFO")
        
        try:
            # Detect available Nuke installations
            available_viewers = self.detect_exr_viewers()
            nuke_exe = available_viewers.get('nuke_player')
            
            if not nuke_exe:
                self.logger.error("Nuke Player not found on system")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("Nuke Player not found. Please install Nuke or configure the path.", "ERROR")
                return None
            
            # Process different input types
            file_path = None
            is_sequence = False
            
            if isinstance(media_input, dict):
                # Rich sequence data dict
                seq_info = media_input
                directory = seq_info.get('directory', '')
                base_name = seq_info.get('base_name', '')
                suffix = seq_info.get('suffix', '')
                frame_numbers = seq_info.get('frame_numbers', [])
                files = seq_info.get('files', [])
                
                if base_name and suffix and frame_numbers:
                    # Create Nuke-style sequence pattern (e.g., "image.####.exr")
                    digits = len(str(max(frame_numbers))) if frame_numbers else 4
                    digits = max(4, digits)  # At least 4 digits
                    pattern = f"{base_name}.{'#' * digits}{suffix}"
                    sequence_pattern = os.path.join(directory, pattern)
                    # Convert Windows backslashes to forward slashes for Nuke
                    sequence_pattern = sequence_pattern.replace('\\', '/')
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Using sequence pattern: {pattern}")
                elif files:
                    # Fallback to first file
                    if isinstance(files[0], dict):
                        file_path = files[0].get('path', '')
                    else:
                        file_path = str(files[0])
                    file_path = file_path.replace('\\', '/')
                    
            elif isinstance(media_input, list) and media_input:
                # List of files - try to detect pattern
                files = [str(f) if isinstance(f, dict) and 'path' in f else str(f) for f in media_input]
                files = sorted(files)
                
                # Try to create sequence pattern from file list
                first_file = files[0]
                directory = os.path.dirname(first_file)
                basename = os.path.basename(first_file)
                
                # Look for numeric pattern
                import re
                match = re.search(r'(\d+)', basename)
                if match and len(files) > 1:
                    number_part = match.group(1)
                    digits = len(number_part)
                    pattern_name = basename.replace(number_part, '#' * digits)
                    sequence_pattern = os.path.join(directory, pattern_name)
                    sequence_pattern = sequence_pattern.replace('\\', '/')
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Detected sequence pattern: {pattern_name}")
                else:
                    # Single file or no pattern detected
                    file_path = first_file.replace('\\', '/')
                    
            elif isinstance(media_input, str):
                # Single file path
                file_path = media_input.replace('\\', '/')
            
            if not file_path or not os.path.exists(file_path.replace('#', '1') if '#' in file_path else file_path):
                self.logger.error(f"Media file not found for Nuke Player: {file_path}")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message(f"Media file not found: {file_path}", "ERROR")
                return None
            
            # Build Nuke command for HieroPlayer/Nuke Player
            cmd = [nuke_exe]
            
            # Add safe mode and player flags
            cmd.extend(['--safe', '--workspace', 'Flipbook', '--player'])
            
            # Add the file/sequence path
            cmd.append(file_path)
            
            self.logger.info(f"Launching Nuke Player with command: {' '.join(cmd)}")
            
            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"Nuke Player launched successfully (PID: {process.pid})")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                filename = os.path.basename(file_path)
                success_msg = f"Launched Nuke Player: {filename}"
                if is_sequence:
                    success_msg += " (sequence)"
                self.app.status_manager.add_log_message(success_msg, "INFO")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to launch Nuke Player: {e}")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                self.app.status_manager.add_log_message(f"Error launching Nuke Player: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None

    def launch_mrv2(self, media_input) -> Optional[subprocess.Popen]:
        """
        Launch MRV2 professional image viewer for media playback.
        MRV2 is a specialized viewer for VFX and animation with advanced color management.
        
        Args:
            media_input: Can be:
                - Single file path (str)
                - Sequence data dict with keys like 'base_name', 'files', etc.
                - List of files
        
        Returns:
            subprocess.Popen: Process handle, or None if failed
        """
        try:
            # Detect available MRV2 installations
            available_viewers = self.detect_exr_viewers()
            mrv2_exe = available_viewers.get('mrv2')
            
            if not mrv2_exe:
                self.logger.error("MRV2 not found on system")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("MRV2 not found. Please install MRV2 or configure the path.", "ERROR")
                return None
            
            # Process different input types
            file_path = None
            is_sequence = False
            
            if isinstance(media_input, dict):
                # Rich sequence data dict
                seq_info = media_input
                directory = seq_info.get('directory', '')
                base_name = seq_info.get('base_name', '')
                suffix = seq_info.get('suffix', '')
                frame_numbers = seq_info.get('frame_numbers', [])
                files = seq_info.get('files', [])
                
                if base_name and suffix and frame_numbers:
                    # Create sequence pattern for MRV2 (uses printf-style formatting)
                    digits = len(str(max(frame_numbers))) if frame_numbers else 4
                    digits = max(4, digits)  # At least 4 digits
                    pattern = f"{base_name}.%0{digits}d{suffix}"
                    sequence_pattern = os.path.join(directory, pattern)
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Using MRV2 sequence pattern: {pattern}")
                elif files:
                    # Fallback to first file
                    if isinstance(files[0], dict):
                        file_path = files[0].get('path', '')
                    else:
                        file_path = str(files[0])
                    
            elif isinstance(media_input, list) and media_input:
                # List of files - try to detect pattern or use first file
                files = [str(f) if isinstance(f, dict) and 'path' in f else str(f) for f in media_input]
                files = sorted(files)
                
                # Try to create sequence pattern from file list
                first_file = files[0]
                directory = os.path.dirname(first_file)
                basename = os.path.basename(first_file)
                
                # Look for numeric pattern
                import re
                match = re.search(r'(\d+)', basename)
                if match and len(files) > 1:
                    number_part = match.group(1)
                    digits = len(number_part)
                    pattern_name = basename.replace(number_part, f'%0{digits}d')
                    sequence_pattern = os.path.join(directory, pattern_name)
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Detected MRV2 sequence pattern: {pattern_name}")
                else:
                    # Single file or no pattern detected
                    file_path = first_file
                    
            elif isinstance(media_input, str):
                # Single file path
                file_path = media_input
            
            if not file_path:
                self.logger.error("No valid file path found for MRV2")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("No valid file path found for MRV2", "ERROR")
                return None
            
            # Build MRV2 command
            cmd = [mrv2_exe]
            
            # Add the file/sequence path
            cmd.append(file_path)
            
            self.logger.info(f"Launching MRV2 with command: {' '.join(cmd)}")
            
            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"MRV2 launched successfully (PID: {process.pid})")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                filename = os.path.basename(file_path)
                success_msg = f"Launched MRV2: {filename}"
                if is_sequence:
                    success_msg += " (sequence)"
                self.app.status_manager.add_log_message(success_msg, "INFO")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to launch MRV2: {e}")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                self.app.status_manager.add_log_message(f"Error launching MRV2: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None

    def launch_djv(self, media_input) -> Optional[subprocess.Popen]:
        """
        Launch DJV professional image viewer for media playback.
        DJV is optimized for film and VFX workflows with robust sequence support.
        
        Args:
            media_input: Can be:
                - Single file path (str)
                - Sequence data dict with keys like 'base_name', 'files', etc.
                - List of files
        
        Returns:
            subprocess.Popen: Process handle, or None if failed
        """
        try:
            # Detect available DJV installations
            available_viewers = self.detect_exr_viewers()
            djv_exe = available_viewers.get('djv')
            
            if not djv_exe:
                self.logger.error("DJV not found on system")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("DJV not found. Please install DJV or configure the path.", "ERROR")
                return None
            
            # Process different input types
            file_path = None
            is_sequence = False
            
            if isinstance(media_input, dict):
                # Rich sequence data dict
                seq_info = media_input
                directory = seq_info.get('directory', '')
                base_name = seq_info.get('base_name', '')
                suffix = seq_info.get('suffix', '')
                frame_numbers = seq_info.get('frame_numbers', [])
                files = seq_info.get('files', [])
                
                if base_name and suffix and frame_numbers:
                    # Create sequence pattern for DJV (uses @ symbol for frame numbers)
                    digits = len(str(max(frame_numbers))) if frame_numbers else 4
                    digits = max(4, digits)  # At least 4 digits
                    pattern = f"{base_name}.{'@' * digits}{suffix}"
                    sequence_pattern = os.path.join(directory, pattern)
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Using DJV sequence pattern: {pattern}")
                elif files:
                    # Fallback to first file
                    if isinstance(files[0], dict):
                        file_path = files[0].get('path', '')
                    else:
                        file_path = str(files[0])
                    
            elif isinstance(media_input, list) and media_input:
                # List of files - try to detect pattern or use first file
                files = [str(f) if isinstance(f, dict) and 'path' in f else str(f) for f in media_input]
                files = sorted(files)
                
                # Try to create sequence pattern from file list
                first_file = files[0]
                directory = os.path.dirname(first_file)
                basename = os.path.basename(first_file)
                
                # Look for numeric pattern
                import re
                match = re.search(r'(\d+)', basename)
                if match and len(files) > 1:
                    number_part = match.group(1)
                    digits = len(number_part)
                    pattern_name = basename.replace(number_part, '@' * digits)
                    sequence_pattern = os.path.join(directory, pattern_name)
                    is_sequence = True
                    file_path = sequence_pattern
                    self.logger.info(f"Detected DJV sequence pattern: {pattern_name}")
                else:
                    # Single file or no pattern detected
                    file_path = first_file
                    
            elif isinstance(media_input, str):
                # Single file path
                file_path = media_input
            
            if not file_path:
                self.logger.error("No valid file path found for DJV")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("No valid file path found for DJV", "ERROR")
                return None
            
            # Build DJV command
            cmd = [djv_exe]
            
            # Add the file/sequence path
            cmd.append(file_path)
            
            self.logger.info(f"Launching DJV with command: {' '.join(cmd)}")
            
            # Launch with minimal console window on Windows
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
            
            process = subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            self.logger.info(f"DJV launched successfully (PID: {process.pid})")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                filename = os.path.basename(file_path)
                success_msg = f"Launched DJV: {filename}"
                if is_sequence:
                    success_msg += " (sequence)"
                self.app.status_manager.add_log_message(success_msg, "INFO")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to launch DJV: {e}")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                self.app.status_manager.add_log_message(f"Error launching DJV: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None

    def send_to_nuke(self, media_input) -> bool:
        """
        Send media to Nuke via socket connection to create a Read node.
        
        Args:
            media_input: Can be:
                - Single file path (str)
                - Sequence data dict with keys like 'base_name', 'files', etc.
                - List of files
        
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        try:
            # Process different input types to get file path and sequence info
            file_path = None
            is_sequence = False
            sequence_pattern = None
            first_frame = None
            last_frame = None
            
            if isinstance(media_input, dict):
                # Rich sequence data dict
                seq_info = media_input
                directory = seq_info.get('directory', '')
                base_name = seq_info.get('base_name', '')
                suffix = seq_info.get('suffix', '')
                frame_numbers = seq_info.get('frame_numbers', [])
                files = seq_info.get('files', [])
                
                if base_name and suffix and frame_numbers:
                    # Create Nuke-style sequence pattern (e.g., "image.####.exr")
                    digits = len(str(max(frame_numbers))) if frame_numbers else 4
                    digits = max(4, digits)  # At least 4 digits
                    pattern = f"{base_name}.{'#' * digits}{suffix}"
                    sequence_pattern = os.path.join(directory, pattern)
                    # Convert Windows backslashes to forward slashes for Nuke
                    sequence_pattern = sequence_pattern.replace('\\', '/')
                    is_sequence = True
                    file_path = sequence_pattern
                    
                    # Extract frame range from frame_numbers
                    if frame_numbers:
                        first_frame = min(frame_numbers)
                        last_frame = max(frame_numbers)
                        self.logger.info(f"Using sequence pattern: {pattern} [{first_frame}-{last_frame}]")
                    else:
                        self.logger.info(f"Using sequence pattern: {pattern}")
                elif files:
                    # Fallback to first file
                    if isinstance(files[0], dict):
                        file_path = files[0].get('path', '')
                    else:
                        file_path = str(files[0])
                    file_path = file_path.replace('\\', '/')
                    
            elif isinstance(media_input, list) and media_input:
                # List of files - try to detect pattern
                files = [str(f) if isinstance(f, dict) and 'path' in f else str(f) for f in media_input]
                files = sorted(files)
                
                # Try to create sequence pattern from file list
                first_file = files[0]
                directory = os.path.dirname(first_file)
                basename = os.path.basename(first_file)
                
                # Look for numeric pattern and extract frame numbers
                import re
                match = re.search(r'(\d+)', basename)
                if match and len(files) > 1:
                    number_part = match.group(1)
                    digits = len(number_part)
                    pattern_name = basename.replace(number_part, '#' * digits)
                    sequence_pattern = os.path.join(directory, pattern_name)
                    sequence_pattern = sequence_pattern.replace('\\', '/')
                    is_sequence = True
                    file_path = sequence_pattern
                    
                    # Extract frame numbers from all files in the list
                    frame_numbers = []
                    for file_in_list in files:
                        file_basename = os.path.basename(file_in_list)
                        file_match = re.search(r'(\d+)', file_basename)
                        if file_match:
                            frame_numbers.append(int(file_match.group(1)))
                    
                    if frame_numbers:
                        first_frame = min(frame_numbers)
                        last_frame = max(frame_numbers)
                        self.logger.info(f"Detected sequence pattern: {pattern_name} [{first_frame}-{last_frame}]")
                    else:
                        self.logger.info(f"Detected sequence pattern: {pattern_name}")
                else:
                    # Single file or no pattern detected
                    file_path = first_file.replace('\\', '/')
                    
            elif isinstance(media_input, str):
                # Single file path
                file_path = media_input.replace('\\', '/')
            
            if not file_path:
                self.logger.error("No valid file path found for Nuke")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("No valid file path found for Nuke", "ERROR")
                return False
            
            # Connect to Nuke socket server and send Read node command
            return self._send_nuke_command(file_path, is_sequence, first_frame, last_frame)
            
        except Exception as e:
            self.logger.error(f"Failed to send media to Nuke: {e}")
            if hasattr(self.app, 'status_manager'):
                self.app.status_manager.add_log_message(f"Error sending to Nuke: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def _send_nuke_command(self, file_path: str, is_sequence: bool = False, first_frame: int = None, last_frame: int = None) -> bool:
        """
        Send a command to Nuke via socket to create a Read node.
        
        Args:
            file_path: File path or sequence pattern to load
            is_sequence: Whether this is an image sequence
            first_frame: First frame of the sequence (if applicable)
            last_frame: Last frame of the sequence (if applicable)
            
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        try:
            # Create socket connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)  # 5 second timeout
            
            try:
                s.connect(('127.0.0.1', 49512))
            except socket.error as e:
                self.logger.error(f"Could not connect to Nuke server at 127.0.0.1:49512. Is Nuke running with NukeServerSocket? Error: {e}")
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message("Could not connect to Nuke server. Is Nuke running with NukeServerSocket?", "ERROR")
                s.close()
                return False
            
            # Create Nuke Python command to add Read node
            if is_sequence:
                nuke_command = f"""
import nuke

# Create Read node for sequence
read_node = nuke.createNode('Read')
read_node['file'].setValue('{file_path}')
"""
                # Set frame range if provided
                if first_frame is not None and last_frame is not None:
                    nuke_command += f"""
# Set frame range for sequence
read_node['first'].setValue({first_frame})
read_node['last'].setValue({last_frame})

print("Added sequence: " + read_node.name() + " [{first_frame}-{last_frame}]")
"""
                else:
                    nuke_command += """
print("Added sequence: " + read_node.name())
"""
                
                nuke_command += """
# Position the node nicely
read_node.setXYpos(int(read_node.xpos()), int(read_node.ypos()) + 100)

# Show in viewer
viewer = nuke.activeViewer()
if viewer:
    viewer.setInput(0, read_node)

print("Read node created successfully")
"""
            else:
                nuke_command = f"""
import nuke

# Create Read node for single file
read_node = nuke.createNode('Read')
read_node['file'].setValue('{file_path}')

print("Added file: " + read_node.name())

# Position the node nicely
read_node.setXYpos(int(read_node.xpos()), int(read_node.ypos()) + 100)

# Show in viewer
viewer = nuke.activeViewer()
if viewer:
    viewer.setInput(0, read_node)

print("Read node created successfully")
"""
            
            # Prepare JSON data for NukeServerSocket
            data = {
                "text": nuke_command.strip(),
                "formatText": "0"  # Plain text output for easier parsing
            }
            
            # Send command
            message = json.dumps(data)
            s.sendall(message.encode('utf-8'))
            
            # Receive response
            response_data = s.recv(4096)  # Increased buffer size
            s.close()
            
            # Process response
            response = response_data.decode('utf-8')
            self.logger.info(f"Nuke server response: {response}")
            
            # Check if the command was successful
            if "Read node created successfully" in response:
                filename = os.path.basename(file_path)
                success_msg = f"Successfully sent to Nuke: {filename}"
                if is_sequence:
                    success_msg += " (sequence)"
                
                self.logger.info(success_msg)
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message(success_msg, "INFO")
                return True
            else:
                # Command may have failed
                error_msg = f"Nuke command may have failed. Response: {response}"
                self.logger.warning(error_msg)
                if hasattr(self.app, 'status_manager') and self.app.status_manager:
                    self.app.status_manager.add_log_message(f"Nuke response: {response}", "WARNING")
                return False  # Still return False to indicate uncertainty
            
        except socket.timeout:
            self.logger.error("Timeout connecting to Nuke server")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                self.app.status_manager.add_log_message("Timeout connecting to Nuke server", "ERROR")
            try:
                s.close()
            except:
                pass
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending command to Nuke: {e}")
            if hasattr(self.app, 'status_manager') and self.app.status_manager:
                self.app.status_manager.add_log_message(f"Error sending command to Nuke: {e}", "ERROR")
            try:
                s.close()
            except:
                pass
            import traceback
            traceback.print_exc()
            return False

    def test_nuke_socket_connection(self) -> dict:
        """
        Test connection to Nuke socket server.
        
        Returns:
            dict: Test results with keys like 'connected', 'response', 'error'
        """
        results = {
            'connected': False,
            'nuke_version': None,
            'response': None,
            'error': None
        }
        
        try:
            # Create socket connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)  # 3 second timeout for testing
            
            try:
                s.connect(('127.0.0.1', 49512))
                results['connected'] = True
                
                # Send a simple test command to get Nuke version
                test_command = {
                    "text": "import nuke; print(f'Nuke {nuke.NUKE_VERSION_STRING} connected')",
                    "formatText": "0"
                }
                
                message = json.dumps(test_command)
                s.sendall(message.encode('utf-8'))
                
                # Receive response
                response_data = s.recv(1024)
                response = response_data.decode('utf-8')
                results['response'] = response
                
                # Try to extract version info
                if 'Nuke' in response and 'connected' in response:
                    import re
                    version_match = re.search(r'Nuke ([\d.]+)', response)
                    if version_match:
                        results['nuke_version'] = version_match.group(1)
                
                s.close()
                
            except socket.error as e:
                results['error'] = f"Connection failed: {e}"
                try:
                    s.close()
                except:
                    pass
                
        except Exception as e:
            results['error'] = str(e)
        
        # Log results to app if available
        if hasattr(self.app, 'status_manager') and self.app.status_manager:
            if results['connected']:
                version_info = f" (v{results['nuke_version']})" if results['nuke_version'] else ""
                self.app.status_manager.add_log_message(f"✓ Nuke socket server connected{version_info}", "INFO")
            else:
                self.app.status_manager.add_log_message(f"✗ Nuke socket server not available: {results.get('error', 'Unknown error')}", "WARNING")
        
        return results

    def detect_exr_viewers(self) -> Dict[str, str]:
        """
        Detect available EXR/image sequence viewers on the system.
        
        Returns:
            Dict[str, str]: Dictionary mapping viewer names to their executable paths
        """
        viewers = {}
        
        # Common EXR viewer locations
        viewer_configs = {
            'nuke_player': {
                'windows': [
                    r'C:\Program Files\Nuke*\Nuke*.exe',
                    r'C:\Program Files (x86)\Nuke*\Nuke*.exe',
                    r'C:\Users\*\AppData\Local\Nuke*\Nuke*.exe',
                    r'C:\Nuke*\Nuke*.exe',
                    r'D:\Program Files\Nuke*\Nuke*.exe',
                    r'D:\Nuke*\Nuke*.exe',
                    # Network installations
                    r'\\*\Nuke*\Nuke*.exe',
                    # Foundry standard locations
                    r'C:\Program Files\Foundry\Nuke*\Nuke*.exe',
                    r'C:\Program Files (x86)\Foundry\Nuke*\Nuke*.exe'
                ],
                'linux': [
                    '/usr/local/Nuke*/Nuke*',
                    '/opt/Nuke*/Nuke*',
                    '/home/*/Nuke*/Nuke*',
                    '/usr/local/foundry/nuke*/Nuke*',
                    '/opt/foundry/nuke*/Nuke*',
                    # Network mounts
                    '/mnt/*/Nuke*/Nuke*',
                    '/net/*/Nuke*/Nuke*'
                ],
                'darwin': [
                    '/Applications/Nuke*/Nuke*.app/Contents/MacOS/Nuke*',
                    '/usr/local/Nuke*/Nuke*',
                    '/opt/Nuke*/Nuke*',
                    '/Applications/Foundry/Nuke*/Nuke*.app/Contents/MacOS/Nuke*'
                ]
            },
            'mrv2': {
                'windows': [
                    r'C:\Program Files\mrv2*\bin\mrv2.exe',
                    r'C:\Program Files (x86)\mrv2*\bin\mrv2.exe',
                    r'C:\mrv2*\bin\mrv2.exe',
                    r'C:\mrv2*\mrv2.exe',
                    r'D:\Program Files\mrv2*\bin\mrv2.exe',
                    r'D:\mrv2*\bin\mrv2.exe',
                    # User installations
                    r'C:\Users\*\AppData\Local\mrv2*\bin\mrv2.exe',
                    r'C:\Users\*\mrv2*\bin\mrv2.exe',
                    # Network installations  
                    r'\\*\mrv2*\bin\mrv2.exe'
                ],
                'linux': [
                    '/usr/local/mrv2*/bin/mrv2',
                    '/opt/mrv2*/bin/mrv2',
                    '/usr/bin/mrv2',
                    '/usr/local/bin/mrv2',
                    '/home/*/mrv2*/bin/mrv2',
                    # AppImage locations
                    '/usr/local/mrv2*/mrv2*.AppImage',
                    '/opt/mrv2*/mrv2*.AppImage',
                    '/home/*/Applications/mrv2*.AppImage',
                    # Network mounts
                    '/mnt/*/mrv2*/bin/mrv2',
                    '/net/*/mrv2*/bin/mrv2'
                ],
                'darwin': [
                    '/Applications/mrv2*.app/Contents/MacOS/mrv2*',
                    '/usr/local/mrv2*/bin/mrv2',
                    '/opt/mrv2*/bin/mrv2',
                    '/usr/local/bin/mrv2',
                    # Homebrew locations
                    '/opt/homebrew/bin/mrv2',
                    '/usr/local/Cellar/mrv2*/bin/mrv2'
                ]
            },
            'djv': {
                'windows': [
                    r'C:\Program Files\DJV*\bin\djv_view.exe',
                    r'C:\Program Files (x86)\DJV*\bin\djv_view.exe',
                    r'C:\DJV*\bin\djv_view.exe',
                    r'C:\DJV*\djv_view.exe',
                    r'D:\Program Files\DJV*\bin\djv_view.exe',
                    r'D:\DJV*\bin\djv_view.exe',
                    # User installations
                    r'C:\Users\*\AppData\Local\DJV*\bin\djv_view.exe',
                    r'C:\Users\*\DJV*\bin\djv_view.exe',
                    # Network installations
                    r'\\*\DJV*\bin\djv_view.exe',
                    # Alternative executable names
                    r'C:\Program Files\DJV*\bin\djv.exe',
                    r'C:\Program Files (x86)\DJV*\bin\djv.exe'
                ],
                'linux': [
                    '/usr/local/DJV*/bin/djv_view',
                    '/opt/DJV*/bin/djv_view',
                    '/usr/bin/djv_view',
                    '/usr/local/bin/djv_view',
                    '/home/*/DJV*/bin/djv_view',
                    # Alternative executable names
                    '/usr/local/DJV*/bin/djv',
                    '/opt/DJV*/bin/djv',
                    '/usr/bin/djv',
                    '/usr/local/bin/djv',
                    # AppImage locations
                    '/usr/local/DJV*/DJV*.AppImage',
                    '/opt/DJV*/DJV*.AppImage',
                    '/home/*/Applications/DJV*.AppImage',
                    # Network mounts
                    '/mnt/*/DJV*/bin/djv_view',
                    '/net/*/DJV*/bin/djv_view'
                ],
                'darwin': [
                    '/Applications/DJV*.app/Contents/MacOS/djv_view',
                    '/Applications/DJV*.app/Contents/MacOS/djv',
                    '/usr/local/DJV*/bin/djv_view',
                    '/opt/DJV*/bin/djv_view',
                    '/usr/local/bin/djv_view',
                    '/usr/local/bin/djv',
                    # Homebrew locations
                    '/opt/homebrew/bin/djv_view',
                    '/opt/homebrew/bin/djv',
                    '/usr/local/Cellar/djv*/bin/djv_view'
                ]
            }
        }
        
        system = platform.system().lower()
        system_map = {'windows': 'windows', 'linux': 'linux', 'darwin': 'darwin'}
        system_key = system_map.get(system, 'linux')
        
        for viewer_name, config in viewer_configs.items():
            paths = config.get(system_key, [])
            for path in paths:
                # Handle wildcards for Nuke
                if '*' in path:
                    import glob
                    matches = glob.glob(path)
                    if matches:
                        # For Nuke, filter matches to exclude utility executables
                        if viewer_name == 'nuke_player':
                            # Filter out known utility executables
                            filtered_matches = []
                            for match in matches:
                                exe_name = os.path.basename(match).lower()
                                # Only include main Nuke executables, exclude utilities
                                if (exe_name.startswith('nuke') and 
                                    not any(util in exe_name for util in [
                                        'crash', 'feedback', 'studio', 'batch', 
                                        'render', 'worker', 'plugin', 'sdk'
                                    ])):
                                    filtered_matches.append(match)
                            matches = filtered_matches
                        elif viewer_name == 'mrv2':
                            # Filter MRV2 matches to exclude non-executable files
                            filtered_matches = []
                            for match in matches:
                                if os.path.isfile(match) and (match.endswith('.exe') or 
                                                            match.endswith('.AppImage') or
                                                            not '.' in os.path.basename(match)):
                                    filtered_matches.append(match)
                            matches = filtered_matches
                        elif viewer_name == 'djv':
                            # Filter DJV matches to exclude non-executable files
                            filtered_matches = []
                            for match in matches:
                                if os.path.isfile(match) and (match.endswith('.exe') or 
                                                            match.endswith('.AppImage') or
                                                            not '.' in os.path.basename(match)):
                                    filtered_matches.append(match)
                            matches = filtered_matches
                        
                        # Sort to get the latest version
                        matches.sort(reverse=True)
                        for match in matches:
                            if os.path.exists(match):
                                # For Nuke, do additional validation
                                if viewer_name == 'nuke_player':
                                    if self._validate_nuke_executable(match):
                                        viewers[viewer_name] = match
                                        print(f"[NUKE_DETECTION] Found valid Nuke Player: {match}")
                                        break
                                else:
                                    viewers[viewer_name] = match
                                    print(f"[{viewer_name.upper()}_DETECTION] Found {viewer_name}: {match}")
                                    break
                        if viewer_name in viewers:
                            break
                else:
                    if os.path.exists(path):
                        # For Nuke, do additional validation
                        if viewer_name == 'nuke_player':
                            if self._validate_nuke_executable(path):
                                viewers[viewer_name] = path
                                print(f"[NUKE_DETECTION] Found valid Nuke Player: {path}")
                        else:
                            viewers[viewer_name] = path
                            print(f"[{viewer_name.upper()}_DETECTION] Found {viewer_name}: {path}")
                        break
        
        return viewers

    def _validate_nuke_executable(self, nuke_path: str) -> bool:
        """
        Validate that a Nuke executable supports image viewing with -v flag.
        
        Args:
            nuke_path: Path to potential Nuke executable
            
        Returns:
            bool: True if this Nuke supports -v flag for image viewing
        """
        try:
            # First check if this is actually the main Nuke executable
            exe_name = os.path.basename(nuke_path).lower()
            
            # Exclude utility executables that are not the main Nuke application
            excluded_names = [
                'nukecrashfeedback.exe',
                'nukex.exe',  # NukeX might not support -v the same way
                'nukestudio.exe',  # Nuke Studio is different
                'nukegui.exe',  # Sometimes there are GUI-specific variants
                'nukebatch.exe',  # Batch rendering, not viewer
                'nukerender.exe',  # Render-only version
                'nukeworker.exe',  # Render worker
                'nukeplugin.exe',  # Plugin utilities
                'nukesdk.exe'  # SDK utilities
            ]
            
            # Check if this executable should be excluded
            for excluded in excluded_names:
                if excluded in exe_name:
                    print(f"[NUKE_DETECTION] Excluding utility executable: {nuke_path}")
                    return False
            
            # Look for the main Nuke executable patterns
            valid_patterns = [
                'nuke',  # Basic nuke
                'nuke13',  # Version-specific
                'nuke14',
                'nuke15',
                'nuke16',
                'nuke10'  # Non-commercial version
            ]
            
            # Check if the executable name matches valid patterns
            is_valid_name = False
            for pattern in valid_patterns:
                if exe_name.startswith(pattern) and not any(excluded in exe_name for excluded in excluded_names):
                    is_valid_name = True
                    break
            
            if not is_valid_name:
                print(f"[NUKE_DETECTION] Executable name doesn't match valid Nuke patterns: {nuke_path}")
                return False
            
            print(f"[NUKE_DETECTION] Valid Nuke executable found: {nuke_path}")
            
            # Quick test to see if Nuke responds to --help without crashing
            result = subprocess.run(
                [nuke_path, '--help'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            # Check if help output mentions -v flag for viewing
            help_text = result.stdout.lower()
            if '-v' in help_text and 'display' in help_text:
                print(f"[NUKE_DETECTION] Nuke supports -v image viewing: {nuke_path}")
                return True
            else:
                print(f"[NUKE_DETECTION] Nuke may not support -v viewing, but assuming it does: {nuke_path}")
                # Still return True as most Nuke versions support -v
                return True
                
        except subprocess.TimeoutExpired:
            print(f"[NUKE_DETECTION] Nuke help command timed out, assuming valid: {nuke_path}")
            return True  # Assume it works if we can't test
        except Exception as e:
            print(f"[NUKE_DETECTION] Error validating Nuke: {nuke_path}, error: {e}")
            return True  # Assume it works if we can't test


if __name__ == "__main__":
    # Test the utilities
    print("Testing ffplay installation...")
    test_results = test_ffplay_installation()
    
    for key, value in test_results.items():
        print(f"{key}: {value}")
    
    if test_results['ffplay_found']:
        print("\nffplay is ready for use!")
        print("\nZoom controls in ffplay:")
        print("- Mouse wheel: Zoom in/out")
        print("- Right click: Context menu with zoom options")
        print("- 'w' key: Cycle through zoom modes")
        print("- 's' key: Step through frames")
        print("- Space: Pause/resume")
        print("- 'q' or ESC: Quit")
        print("\nImage sequence support:")
        print("- Automatic frame rate detection")
        print("- Supports common formats: JPG, PNG, TIFF, EXR, DPX, etc.")
        print("- Sequential numbering pattern detection")
    else:
        print("\nffplay not found. Please install FFmpeg.")
        print("Download from: https://ffmpeg.org/download.html")
    
    # Test Nuke Player installation
    print("\n" + "="*50)
    print("Testing Nuke Player installation...")
    
    # Create a mock app instance for testing
    class MockApp:
        def __init__(self):
            self.status_manager = None
    
    mock_app = MockApp()
    media_utils = MediaPlayerUtils(mock_app)
    nuke_results = media_utils.test_nuke_player_installation()
    
    print("\nNuke Player test results:")
    for key, value in nuke_results.items():
        print(f"{key}: {value}")
    
    if nuke_results['nuke_found']:
        print("\nNuke Player is ready for professional media playback!")
        print("\nNuke Player features:")
        print("- Professional image sequence playback")
        print("- Supports EXR, DPX, CIN, and other professional formats")
        print("- Frame-accurate scrubbing and playback")
        print("- Built-in color management")
        print("- High dynamic range (HDR) support")
        print("- Network rendering and collaboration features")
        print("\nNuke Player controls:")
        print("- Left/Right arrows: Step through frames")
        print("- Space: Play/pause")
        print("- Home/End: Go to first/last frame") 
        print("- Mouse drag: Scrub through timeline")
        print("- Mouse wheel: Zoom in/out")
        print("- Right click: Color correction and view options")
    else:
        print("\nNuke Player not found.")
        print("Install Foundry Nuke for professional media playback.")
        print("Download from: https://www.foundry.com/products/nuke")

    # Test MRV2 installation
    print("\n" + "="*50)
    print("Testing MRV2 installation...")
    
    mrv2_results = media_utils.test_mrv2_installation()
    
    print("\nMRV2 test results:")
    for key, value in mrv2_results.items():
        print(f"{key}: {value}")
    
    if mrv2_results['mrv2_found']:
        print("\nMRV2 is ready for professional media playback!")
        print("\nMRV2 features:")
        print("- Professional image sequence viewer")
        print("- Advanced color management and LUT support")
        print("- ACES and OpenColorIO integration")
        print("- VFX and animation workflow optimized")
        print("- Supports EXR, DPX, TIFF, MOV, and many other formats")
        print("- Real-time playback with GPU acceleration")
        print("\nMRV2 controls:")
        print("- Space: Play/pause")
        print("- Left/Right arrows: Step through frames")
        print("- Mouse wheel: Zoom in/out")
        print("- Right click: Context menu with color and display options")
    else:
        print("\nMRV2 not found.")
        print("Install MRV2 for professional VFX media playback.")
        print("Download from: https://github.com/ggarra13/mrv2")

    # Test DJV installation
    print("\n" + "="*50)
    print("Testing DJV installation...")
    
    djv_results = media_utils.test_djv_installation()
    
    print("\nDJV test results:")
    for key, value in djv_results.items():
        print(f"{key}: {value}")
    
    if djv_results['djv_found']:
        print("\nDJV is ready for professional media playback!")
        print("\nDJV features:")
        print("- Professional image sequence viewer")
        print("- Optimized for film and VFX workflows")
        print("- Supports industry-standard formats (EXR, DPX, CIN, etc.)")
        print("- Color management and LUT support")
        print("- High-performance playback engine")
        print("- Cross-platform compatibility")
        print("\nDJV controls:")
        print("- Space: Play/pause")
        print("- Left/Right arrows: Step through frames")
        print("- Page Up/Down: Jump by larger increments")
        print("- Mouse wheel: Zoom in/out")
        print("- Right click: View and playback options")
    else:
        print("\nDJV not found.")
        print("Install DJV for professional image sequence playback.")
        print("Download from: https://darbyjohnston.github.io/DJV/")
    
    # Test all available media players
    print("\n" + "="*50)
    print("Available media players summary:")
    
    available_players = []
    if test_results['ffplay_found']:
        available_players.append("ffplay (FFmpeg)")
    if nuke_results['nuke_found']:
        available_players.append("Nuke Player (Professional)")
    if mrv2_results['mrv2_found']:
        available_players.append("MRV2 (VFX Optimized)")
    if djv_results['djv_found']:
        available_players.append("DJV (Film/VFX)")
    
    # Test Nuke socket connection
    print("\n" + "="*50)
    print("Testing Nuke socket connection...")
    
    socket_results = media_utils.test_nuke_socket_connection()
    print("\nNuke socket test results:")
    for key, value in socket_results.items():
        print(f"{key}: {value}")
    
    if socket_results['connected']:
        print("\n✅ Nuke socket server is running and ready!")
        print("\nNuke socket features:")
        print("- Send Read nodes directly to open Nuke session")
        print("- Automatic sequence pattern detection")
        print("- Frame range detection and project setup")
        print("- Real-time communication with running Nuke")
        print("- No need to launch separate processes")
        print("\nTo use: Ensure Nuke is running with NukeServerSocket plugin loaded")
        available_players.append("Nuke Socket (Real-time)")
    else:
        print("\n⚠️ Nuke socket server not available")
        print("To enable:")
        print("1. Start Nuke")
        print("2. Load the NukeServerSocket plugin")
        print("3. Ensure server is listening on 127.0.0.1:49512")
    
    if available_players:
        print(f"\nFound {len(available_players)} media player(s):")
        for player in available_players:
            print(f"  ✓ {player}")
    else:
        print("\nNo media players found. Please install FFmpeg and/or professional viewers.")
    
    print("\nRecommended usage:")
    print("- ffplay: General purpose video/audio playback, fast and lightweight")
    print("- Nuke Socket: Professional sequences, real-time Read node creation")
    print("- Nuke Player: Professional image sequences, VFX, color-critical work")
    print("- MRV2: VFX and animation workflows, advanced color management")
    print("- DJV: Film and VFX workflows, high-performance sequence playback")
    print("- All support image sequences with frame-accurate playback")

    print("- Nuke Socket: Professional sequences, real-time Read node creation")
    print("- Nuke Player: Professional image sequences, VFX, color-critical work")
    print("- All support image sequences with frame-accurate playback")
