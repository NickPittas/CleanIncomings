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
from typing import Optional, List, Tuple

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
    
    def __init__(self, app_instance):
        """
        Initialize MediaPlayerUtils with app instance for settings access.
        
        Args:
            app_instance: The main CleanIncomings app instance        """
        self.app = app_instance
        self.logger = logging.getLogger(__name__)
    
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
                self.app.status_manager.add_log_message("ffplay not found. Please install FFmpeg and configure the path in Settings.", "WARNING")
        
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
            # Images (for sequences)
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp',
            '.exr', '.hdr', '.dpx', '.cin', '.sgi', '.tga', '.psd'
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
