import os
import shutil
import logging
import threading
import time
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class FileTransfer:
    def __init__(self, src: str, dst: str, status_callback_adapter: Optional[Callable] = None, transfer_id: Optional[str] = None):
        print(f"[FILETRANSFER_DEBUG] Initializing FileTransfer: '{src}' -> '{dst}'")
        self.src = src
        self.dst = dst
        self.status_callback_adapter = status_callback_adapter
        self.transfer_id = transfer_id # For GUI to track specific transfers

        if not os.path.exists(src):
            error_msg = f"Source file not found: {src}"
            print(f"[FILETRANSFER_ERROR] {error_msg}")
            raise FileNotFoundError(error_msg)
        if not os.path.isfile(src):
            # This class is designed for file-to-file copy.
            # If directory copy is needed, it would require a different approach (e.g., recursive instantiation).
            error_msg = f"Source is not a file: {src}"
            print(f"[FILETRANSFER_ERROR] {error_msg}")
            raise ValueError(error_msg)

        self.total_size = os.path.getsize(src)
        print(f"[FILETRANSFER_DEBUG] File size: {self.total_size} bytes")
        self.transferred_bytes = 0
        
        # For native Windows commands, we use simpler callback timing
        self.last_callback_time = 0
        self.callback_interval = 0.5  # Less frequent callbacks since we can't track byte progress
        self.last_callback_bytes = 0
        
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event() # True if paused, False if running
        
        self.start_time = None
        self.error_message = None
        self.completed_successfully = False
        print(f"[FILETRANSFER_DEBUG] FileTransfer initialized successfully")

    def cancel(self):
        """Signals the copy operation to cancel."""
        self._cancel_event.set()

    def pause(self):
        """Signals the copy operation to pause."""
        self._pause_event.set()

    def resume(self):
        """Signals the copy operation to resume if paused."""
        self._pause_event.clear()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def copy(self):
        """Executes the file copy operation using native Windows commands for maximum speed."""
        print(f"[FILETRANSFER_DEBUG] Starting native Windows copy operation...")
        self.start_time = time.time()
        self.completed_successfully = False
        self.error_message = None
        
        # Use native Windows commands for maximum 10GbE performance
        return self._native_windows_copy()
    
    def _native_windows_copy(self):
        """Ultra-fast copy using native Windows commands (robocopy/xcopy) for maximum 10GbE performance."""
        try:
            # Send initial status
            if self.status_callback_adapter:
                self.status_callback_adapter(0, self.total_size, 0, 0, "copying", self.transfer_id)
            
            src_dir = os.path.dirname(self.src)
            src_filename = os.path.basename(self.src)
            dst_dir = os.path.dirname(self.dst)
            
            print(f"[FILETRANSFER_DEBUG] Using native Windows robocopy for maximum speed")
            print(f"[FILETRANSFER_DEBUG] Source dir: {src_dir}")
            print(f"[FILETRANSFER_DEBUG] Source file: {src_filename}")
            print(f"[FILETRANSFER_DEBUG] Dest dir: {dst_dir}")
            
            # Use robocopy with aggressive settings for 10GbE
            # /J = Unbuffered I/O (faster for large files)
            # /MT:32 = Multi-threaded with 32 threads for maximum 10GbE utilization
            # /NFL /NDL = No file/directory listing (faster)
            # /NP = No progress (we handle our own)
            # /R:0 = No retries (fail fast)
            # /W:1 = Wait 1 second between retries
            cmd = [
                'robocopy',
                src_dir,
                dst_dir,
                src_filename,
                '/J',           # Unbuffered I/O for maximum speed
                '/MT:32',       # 32 threads for 10GbE
                '/NFL',         # No file listing
                '/NDL',         # No directory listing  
                '/NP',          # No progress meter
                '/R:0',         # No retries
                '/W:1',         # 1 second wait
                '/BYTES',       # Show file sizes in bytes (for consistent output parsing)
                '/IS'           # Include Same files (OVERWRITE existing files)
            ]
            
            print(f"[FILETRANSFER_DEBUG] Executing: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            speed_bps = self.total_size / elapsed_time if elapsed_time > 0.001 else 0
            speed_mbps = speed_bps / (1024 * 1024)
            
            print(f"[FILETRANSFER_DEBUG] Robocopy completed in {elapsed_time:.2f}s")
            print(f"[FILETRANSFER_DEBUG] Speed: {speed_mbps:.2f} MB/s ({speed_bps * 8 / 1_000_000_000:.2f} Gbps)")
            print(f"[FILETRANSFER_DEBUG] Return code: {result.returncode}")
            print(f"[FILETRANSFER_DEBUG] Stdout: {result.stdout}")
            print(f"[FILETRANSFER_DEBUG] Stderr: {result.stderr}")
            
            # Robocopy return codes: 0=no files copied, 1=files copied successfully, >7=error
            if result.returncode <= 1:
                # Verify the file was actually copied
                if os.path.exists(self.dst) and os.path.getsize(self.dst) == self.total_size:
                    self.transferred_bytes = self.total_size
                    self.completed_successfully = True
                    
                    print(f"[FILETRANSFER_DEBUG] ✅ NATIVE COPY SUCCESS! Speed: {speed_mbps:.2f} MB/s ({speed_bps * 8 / 1_000_000_000:.2f} Gbps)")
                    
                    # Send completion status
                    if self.status_callback_adapter:
                        self.status_callback_adapter(
                            self.total_size, self.total_size, speed_bps, 0, "completed", self.transfer_id
                        )
                    
                    return True
                else:
                    self.error_message = f"Robocopy reported success but destination file validation failed"
                    print(f"[FILETRANSFER_ERROR] {self.error_message}")
                    return False
            else:
                # Try fallback to xcopy for compatibility
                print(f"[FILETRANSFER_DEBUG] Robocopy failed (code {result.returncode}), trying xcopy fallback...")
                return self._xcopy_fallback()
                
        except Exception as e:
            print(f"[FILETRANSFER_ERROR] Native copy failed: {e}, trying xcopy fallback...")
            return self._xcopy_fallback()
    
    def _xcopy_fallback(self):
        """Fallback to xcopy if robocopy fails."""
        try:
            print(f"[FILETRANSFER_DEBUG] Using xcopy fallback for compatibility")
            
            # Use xcopy with aggressive settings
            # /Y = Overwrite without prompting
            # /J = Unbuffered I/O
            # /H = Copy hidden and system files
            cmd = ['xcopy', f'"{self.src}"', f'"{self.dst}"', '/Y', '/H']
            
            print(f"[FILETRANSFER_DEBUG] Executing xcopy: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, shell=True)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            speed_bps = self.total_size / elapsed_time if elapsed_time > 0.001 else 0
            speed_mbps = speed_bps / (1024 * 1024)
            
            print(f"[FILETRANSFER_DEBUG] Xcopy completed in {elapsed_time:.2f}s")
            print(f"[FILETRANSFER_DEBUG] Speed: {speed_mbps:.2f} MB/s ({speed_bps * 8 / 1_000_000_000:.2f} Gbps)")
            print(f"[FILETRANSFER_DEBUG] Return code: {result.returncode}")
            
            if result.returncode == 0:
                # Verify the file was actually copied
                if os.path.exists(self.dst) and os.path.getsize(self.dst) == self.total_size:
                    self.transferred_bytes = self.total_size
                    self.completed_successfully = True
                    
                    print(f"[FILETRANSFER_DEBUG] ✅ XCOPY SUCCESS! Speed: {speed_mbps:.2f} MB/s ({speed_bps * 8 / 1_000_000_000:.2f} Gbps)")
                    
                    # Send completion status
                    if self.status_callback_adapter:
                        self.status_callback_adapter(
                            self.total_size, self.total_size, speed_bps, 0, "completed", self.transfer_id
                        )
                    
                    return True
                else:
                    self.error_message = f"Xcopy reported success but destination file validation failed"
                    print(f"[FILETRANSFER_ERROR] {self.error_message}")
                    return False
            else:
                # Final fallback to Python shutil for maximum compatibility
                print(f"[FILETRANSFER_DEBUG] Xcopy failed (code {result.returncode}), using Python shutil as final fallback...")
                return self._python_fallback()
                
        except Exception as e:
            print(f"[FILETRANSFER_ERROR] Xcopy fallback failed: {e}, using Python shutil as final fallback...")
            return self._python_fallback()
    
    def _python_fallback(self):
        """Final fallback to Python shutil for maximum compatibility."""
        try:
            print(f"[FILETRANSFER_DEBUG] Using Python shutil.copy2() as final fallback")
            
            start_time = time.time()
            shutil.copy2(self.src, self.dst)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            speed_bps = self.total_size / elapsed_time if elapsed_time > 0.001 else 0
            speed_mbps = speed_bps / (1024 * 1024)
            
            print(f"[FILETRANSFER_DEBUG] Python fallback completed in {elapsed_time:.2f}s")
            print(f"[FILETRANSFER_DEBUG] Speed: {speed_mbps:.2f} MB/s ({speed_bps * 8 / 1_000_000_000:.2f} Gbps)")
            
            self.transferred_bytes = self.total_size
            self.completed_successfully = True
            
            # Send completion status
            if self.status_callback_adapter:
                self.status_callback_adapter(
                    self.total_size, self.total_size, speed_bps, 0, "completed", self.transfer_id
                )
            
            print(f"[FILETRANSFER_DEBUG] ⚠️ Python fallback completed (slower than native commands)")
            return True
            
        except Exception as e:
            self.error_message = f"All copy methods failed. Final error: {e}"
            print(f"[FILETRANSFER_ERROR] {self.error_message}")
            return False

def create_destination_directory_if_not_exists(destination_path: str, is_file_path: bool = True) -> Tuple[bool, Optional[str]]:
    """Ensures the destination directory for a file or a directory path exists."""
    if is_file_path:
        dest_dir = os.path.dirname(destination_path)
    else:
        dest_dir = destination_path
    
    if not dest_dir: # Handle cases where dirname might be empty (e.g. for files in current dir)
        return True, None

    print(f"[CREATE_DIR_DEBUG] Attempting to create directory: '{dest_dir}'")
    print(f"[CREATE_DIR_DEBUG] Directory exists check: {os.path.exists(dest_dir)}")
    
    if not os.path.exists(dest_dir):
        try:
            # Handle Windows long path names by using the UNC prefix if needed
            if os.name == 'nt' and len(dest_dir) > 250 and not dest_dir.startswith('\\\\?\\'):
                if dest_dir.startswith('\\\\'):
                    # UNC path: \\server\share -> \\?\UNC\server\share
                    dest_dir = '\\\\?\\UNC\\' + dest_dir[2:]
                else:
                    # Regular path: C:\... -> \\?\C:\...
                    dest_dir = '\\\\?\\' + dest_dir
                print(f"[CREATE_DIR_DEBUG] Using Windows long path format: '{dest_dir}'")
            
            os.makedirs(dest_dir, exist_ok=True) # exist_ok=True is good practice
            print(f"[CREATE_DIR_DEBUG] Successfully created directory: '{dest_dir}'")
            logger.info(f"Created destination directory: {dest_dir}")
            return True, None
        except PermissionError as e:
            err_msg = f"Permission denied creating directory {dest_dir}: {e}"
            print(f"[CREATE_DIR_ERROR] {err_msg}")
            logger.error(err_msg)
            return False, err_msg
        except FileNotFoundError as e:
            err_msg = f"Path not found error creating directory {dest_dir}: {e}"
            print(f"[CREATE_DIR_ERROR] {err_msg}")
            logger.error(err_msg)
            return False, err_msg
        except OSError as e:
            err_msg = f"OS error creating directory {dest_dir}: {e}"
            print(f"[CREATE_DIR_ERROR] {err_msg}")
            logger.error(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"Unexpected error creating directory {dest_dir}: {e}"
            print(f"[CREATE_DIR_ERROR] {err_msg}")
            logger.error(err_msg)
            return False, err_msg
    else:
        print(f"[CREATE_DIR_DEBUG] Directory already exists: '{dest_dir}'")
    
    return True, None

def copy_item(source_path: str, destination_path: str, 
              status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
              transfer_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Copies a single file from source_path to destination_path using the FileTransfer class.
    This function is intended to be run in a worker thread.
    It provides progress, speed, ETA, and supports cancellation.
    Returns a tuple (success: bool, message: str).
    """
    
    base_name = os.path.basename(source_path)

    def _send_status(type_suffix: str, status_str: str, message: str, **kwargs):
        if status_callback:
            data = {
                'status': status_str,
                'message': message,
                'file_path': source_path,
                'transfer_id': transfer_id,
                **kwargs
            }
            status_callback({'type': f'file_operation_{type_suffix}', 'data': data})

    print(f"[COPY_ITEM_DEBUG] Starting copy: '{source_path}' -> '{destination_path}'")
    _send_status('progress', 'progress', f'Preparing to copy {base_name}...', percent=0, speed_mbps=0, eta_str="Calculating...")

    # Check source file
    if not os.path.exists(source_path):
        msg = f"Source file not found: {source_path}"
        print(f"[COPY_ITEM_ERROR] {msg}")
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg

    if not os.path.isfile(source_path):
        msg = f"Source is not a file: {source_path}"
        print(f"[COPY_ITEM_ERROR] {msg}")
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg

    print(f"[COPY_ITEM_DEBUG] Source file validated: {source_path}")
    
    # Create destination directory
    print(f"[COPY_ITEM_DEBUG] Creating destination directory for: {destination_path}")
    dir_created, error_msg_dir = create_destination_directory_if_not_exists(destination_path)
    if not dir_created:
        final_error_msg = error_msg_dir if error_msg_dir else f"Failed to create destination directory for {destination_path}"
        print(f"[COPY_ITEM_ERROR] Directory creation failed: {final_error_msg}")
        logger.error(final_error_msg)
        _send_status('error', 'error', final_error_msg)
        return False, final_error_msg

    print(f"[COPY_ITEM_DEBUG] Destination directory ready")

    file_transfer_instance = None

    def _ft_progress_adapter(transferred_b, total_b, speed_val_bps, eta_val_sec, copy_status_str, ft_id):
        # This adapter is called by FileTransfer during the copy loop.
        if status_callback:
            percent = (transferred_b / total_b) * 100 if total_b > 0 else 0
            speed_mbps = speed_val_bps / (1024 * 1024) if speed_val_bps is not None else 0
            
            if eta_val_sec == float('inf') or eta_val_sec is None:
                eta_str = "Estimating..."
            elif eta_val_sec < 0: 
                eta_str = "Finalizing..." # Or "Done" if percent is 100
            else:
                eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_val_sec)) if eta_val_sec < 86400 else f"{eta_val_sec/3600:.1f} hrs"

            _send_status(
                'progress', 
                'progress' if copy_status_str == "copying" else copy_status_str, # e.g. "paused"
                f'{copy_status_str.capitalize()} {base_name}: {percent:.2f}%',
                percent=round(percent, 2),
                transferred_bytes=transferred_b,
                total_bytes=total_b,
                speed_mbps=round(speed_mbps, 2),
                eta_str=eta_str
            )
    
    try:
        print(f"[COPY_ITEM_DEBUG] Initializing FileTransfer...")
        # Note: The FileTransfer instance itself should be managed by the GUI thread
        # if cancel/pause/resume controls are to be exposed directly.
        # For now, this function runs it to completion or error/cancel.
        file_transfer_instance = FileTransfer(source_path, destination_path, 
                                              status_callback_adapter=_ft_progress_adapter,
                                              transfer_id=transfer_id)
        
        print(f"[COPY_ITEM_DEBUG] FileTransfer initialized, starting copy operation...")
        # This call is blocking for the current thread (the worker thread).
        file_transfer_instance.copy() 
        print(f"[COPY_ITEM_DEBUG] Copy operation completed, checking results...")

        # After copy() returns, check its state:
        if file_transfer_instance.is_cancelled():
            msg = f"Copy of {base_name} cancelled."
            print(f"[COPY_ITEM_INFO] {msg}")
            logger.info(msg)
            _send_status('cancelled', 'cancelled', msg)
            if os.path.exists(destination_path): # Remove partial file on cancel
                 try:
                     os.remove(destination_path)
                     logger.info(f"Removed partial file on cancel: {destination_path}")
                 except Exception as e_rem:
                     logger.warning(f"Could not remove partial file {destination_path} on cancel: {e_rem}")
            return False, msg 

        if file_transfer_instance.error_message:
            msg = f"Error copying {base_name}: {file_transfer_instance.error_message}"
            print(f"[COPY_ITEM_ERROR] {msg}")
            logger.error(msg)
            _send_status('error', 'error', msg)
            return False, msg

        if file_transfer_instance.completed_successfully:
            msg = f"Successfully copied {base_name} to {destination_path}"
            print(f"[COPY_ITEM_SUCCESS] {msg}")
            logger.info(msg)
            _send_status('success', 'success', msg, destination=destination_path, operation='copy')
            return True, msg
        else:
            # Fallback for unexpected non-completion without specific error or cancellation
            msg = f"Copy of {base_name} did not complete as expected (transferred: {file_transfer_instance.transferred_bytes}/{file_transfer_instance.total_size})."
            print(f"[COPY_ITEM_WARNING] {msg}")
            logger.warning(msg)
            _send_status('error', 'error', msg)
            return False, msg

    except (FileNotFoundError, ValueError) as e_init: # Errors from FileTransfer.__init__
        msg = f"Error initializing copy for {base_name}: {e_init}"
        print(f"[COPY_ITEM_ERROR] {msg}")
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg
    except Exception as e_unexpected:
        msg = f"Unexpected error during copy of {base_name}: {e_unexpected}"
        print(f"[COPY_ITEM_ERROR] {msg}")
        logger.error(msg, exc_info=True) 
        _send_status('error', 'error', msg)
        return False, msg

def move_item(source_path: str, destination_path: str, 
              status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
              transfer_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Moves a single file from source_path to destination_path by copying and then deleting the source.
    Uses FileTransfer for the copy phase to provide progress, speed, ETA, and support cancellation.
    Returns a tuple (success: bool, message: str).
    """
    base_name = os.path.basename(source_path)

    def _send_status(type_suffix: str, status_str: str, message: str, **kwargs):
        if status_callback:
            data = {
                'status': status_str,
                'message': message,
                'file_path': source_path,
                'transfer_id': transfer_id,
                **kwargs
            }
            status_callback({'type': f'file_operation_{type_suffix}', 'data': data})

    _send_status('progress', 'progress', f'Preparing to move {base_name}...', percent=0, speed_mbps=0, eta_str="Calculating...")

    if not os.path.exists(source_path):
        msg = f"Source file not found: {source_path}"
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg

    if not os.path.isfile(source_path):
        msg = f"Source is not a file: {source_path} (move_item currently only supports files)"
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg

    dir_created, error_msg_dir = create_destination_directory_if_not_exists(destination_path)
    if not dir_created:
        final_error_msg = error_msg_dir if error_msg_dir else f"Failed to create destination directory for {destination_path}"
        logger.error(final_error_msg)
        _send_status('error', 'error', final_error_msg)
        return False, final_error_msg

    file_transfer_instance = None

    def _ft_progress_adapter_for_move(transferred_b, total_b, speed_val_bps, eta_val_sec, copy_status_str, ft_id):
        if status_callback:
            percent = (transferred_b / total_b) * 100 if total_b > 0 else 0
            speed_mbps = speed_val_bps / (1024 * 1024) if speed_val_bps is not None else 0
            
            if eta_val_sec == float('inf') or eta_val_sec is None:
                eta_str = "Estimating..."
            elif eta_val_sec < 0: 
                eta_str = "Finalizing..."
            else:
                eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_val_sec)) if eta_val_sec < 86400 else f"{eta_val_sec/3600:.1f} hrs"

            _send_status(
                'progress',
                'progress' if copy_status_str == "copying" else copy_status_str,
                f'Copying (for move) {base_name}: {percent:.2f}%',
                percent=round(percent, 2),
                transferred_bytes=transferred_b,
                total_bytes=total_b,
                speed_mbps=round(speed_mbps, 2),
                eta_str=eta_str
            )

    try:
        # --- COPY PHASE ---
        _send_status('progress', 'progress', f'Starting copy phase for move of {base_name}...', percent=0)
        file_transfer_instance = FileTransfer(source_path, destination_path, 
                                              status_callback_adapter=_ft_progress_adapter_for_move,
                                              transfer_id=transfer_id)
        file_transfer_instance.copy() # This call is blocking for the current worker thread.

        if file_transfer_instance.is_cancelled():
            msg = f"Move (copy phase) of {base_name} cancelled."
            logger.info(msg)
            _send_status('cancelled', 'cancelled', msg, operation='move')
            if os.path.exists(destination_path): # Remove partial file on cancel
                 try:
                     os.remove(destination_path)
                     logger.info(f"Removed partial file on cancel: {destination_path}")
                 except Exception as e_rem:
                     logger.warning(f"Could not remove partial file {destination_path} on cancel: {e_rem}")
            return False, msg 

        if file_transfer_instance.error_message:
            msg = f"Error during move (copy phase) of {base_name}: {file_transfer_instance.error_message}"
            logger.error(msg)
            _send_status('error', 'error', msg, operation='move')
            return False, msg

        if not file_transfer_instance.completed_successfully:
            msg = f"Move (copy phase) of {base_name} did not complete as expected (transferred: {file_transfer_instance.transferred_bytes}/{file_transfer_instance.total_size})."
            logger.warning(msg)
            _send_status('error', 'error', msg, operation='move')
            return False, msg

        # --- DELETE PHASE ---
        _send_status('progress', 'progress', f'Copy phase successful. Deleting original {base_name}...', percent=100) # Indicate copy part is done
        try:
            os.remove(source_path)
            msg = f"Successfully moved {base_name} to {destination_path}"
            logger.info(msg)
            _send_status('success', 'success', msg, destination=destination_path, operation='move')
            return True, msg
        except Exception as e_del:
            msg = f"Successfully copied {base_name} to {destination_path}, but failed to delete original: {e_del}"
            logger.error(msg)
            # Send as an error, but with a specific operation detail for GUI to potentially handle differently
            _send_status('error', 'error', msg, destination=destination_path, operation='move_delete_failed')
            return False, msg # Or True, if a successful copy is considered a partially successful move

    except (FileNotFoundError, ValueError) as e_init: # Errors from FileTransfer.__init__
        msg = f"Error initializing move (copy phase) for {base_name}: {e_init}"
        logger.error(msg)
        _send_status('error', 'error', msg, operation='move')
        return False, msg
    except Exception as e_unexpected:
        msg = f"Unexpected error during move of {base_name}: {e_unexpected}"
        logger.error(msg, exc_info=True) 
        _send_status('error', 'error', msg, operation='move')
        return False, msg

def copy_sequence_batch(source_dir: str, destination_dir: str, file_pattern: str,
                       status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                       transfer_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Copies an entire sequence/batch of files using native Windows commands for maximum speed.
    Much more efficient than copying files one by one.
    
    Args:
        source_dir: Source directory containing the files
        destination_dir: Destination directory 
        file_pattern: Pattern like "OLNT0010_main_arch_rgb_*.png" or "*" for all files
        status_callback: Optional callback for progress updates
        transfer_id: Optional transfer ID for tracking
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    
    def _send_status(type_suffix: str, status_str: str, message: str, **kwargs):
        if status_callback:
            data = {
                'status': status_str,
                'message': message,
                'source_dir': source_dir,
                'transfer_id': transfer_id,
                **kwargs
            }
            status_callback({'type': f'sequence_operation_{type_suffix}', 'data': data})

    print(f"[SEQUENCE_COPY_DEBUG] Starting batch copy...")
    print(f"[SEQUENCE_COPY_DEBUG] Source dir: {source_dir}")
    print(f"[SEQUENCE_COPY_DEBUG] Dest dir: {destination_dir}")
    print(f"[SEQUENCE_COPY_DEBUG] Pattern: {file_pattern}")
    
    _send_status('progress', 'progress', f'Preparing to copy sequence batch: {file_pattern}', percent=0)

    # Validate source directory
    if not os.path.exists(source_dir):
        msg = f"Source directory not found: {source_dir}"
        print(f"[SEQUENCE_COPY_ERROR] {msg}")
        logger.error(msg)
        _send_status('error', 'error', msg)
        return False, msg

    # Create destination directory
    dir_created, error_msg_dir = create_destination_directory_if_not_exists(destination_dir, is_file_path=False)
    if not dir_created:
        final_error_msg = error_msg_dir if error_msg_dir else f"Failed to create destination directory: {destination_dir}"
        print(f"[SEQUENCE_COPY_ERROR] {final_error_msg}")
        logger.error(final_error_msg)
        _send_status('error', 'error', final_error_msg)
        return False, final_error_msg

    try:
        # Count files to estimate progress
        import glob
        source_files = glob.glob(os.path.join(source_dir, file_pattern))
        total_files = len(source_files)
        total_size_bytes = sum(os.path.getsize(f) for f in source_files if os.path.isfile(f))
        
        print(f"[SEQUENCE_COPY_DEBUG] Found {total_files} files matching pattern")
        print(f"[SEQUENCE_COPY_DEBUG] Total size: {total_size_bytes} bytes ({total_size_bytes / (1024*1024):.2f} MB)")
        
        if total_files == 0:
            msg = f"No files found matching pattern: {file_pattern}"
            print(f"[SEQUENCE_COPY_WARNING] {msg}")
            _send_status('warning', 'warning', msg)
            return True, msg  # Not an error, just nothing to copy

        _send_status('progress', 'progress', f'Starting batch copy of {total_files} files...', 
                    total_files=total_files, total_size=total_size_bytes, percent=5)

        # Use robocopy with ultra-fast settings and background progress monitoring
        print(f"[SEQUENCE_COPY_DEBUG] Using robocopy with MAXIMUM 10GbE speed + background progress monitoring")
        
        # Robocopy command for MAXIMUM speed (restored critical performance flags)
        cmd = [
            'robocopy',
            source_dir,
            destination_dir,
            file_pattern,
            '/J',           # Unbuffered I/O for maximum speed
            '/MT:32',       # 32 threads for 10GbE
            '/NFL',         # No file listing (CRITICAL for speed)
            '/NDL',         # No directory listing  
            '/NP',          # No progress meter (CRITICAL for speed)
            '/R:0',         # No retries on failed copies
            '/W:1',         # Wait 1 second between retries
            '/BYTES',       # Show file sizes in bytes (for consistent output parsing)
            '/IS'           # Include Same files (OVERWRITE existing files)
        ]
        
        print(f"[SEQUENCE_COPY_DEBUG] Executing: {' '.join(cmd)}")
        
        start_time = time.time()
        
        # Start robocopy process at MAXIMUM speed (no output parsing overhead)
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Background progress monitoring by checking destination directory
        import threading
        import glob
        
        def monitor_progress():
            """Monitor progress by checking destination directory file count"""
            print(f"[PROGRESS_MONITOR_DEBUG] Starting background progress monitoring thread")
            last_update_time = 0
            last_file_count = 0
            
            while process.poll() is None:  # While robocopy is still running
                try:
                    current_time = time.time()
                    
                    # Check progress every 1 second (don't spam)
                    if current_time - last_update_time >= 1.0:
                        # Count files in destination directory
                        dest_pattern = os.path.join(destination_dir, file_pattern)
                        print(f"[PROGRESS_MONITOR_DEBUG] Checking pattern: {dest_pattern}")
                        
                        dest_files = glob.glob(dest_pattern)
                        files_copied = len(dest_files)
                        
                        print(f"[PROGRESS_MONITOR_DEBUG] Found {files_copied} files in destination (was {last_file_count})")
                        
                        if files_copied > last_file_count:  # Progress detected
                            # Calculate progress
                            progress_percent = min(95, (files_copied / total_files) * 100)
                            elapsed = current_time - start_time
                            
                            if elapsed > 0.1:
                                # Estimate speed based on files copied so far
                                estimated_bytes_copied = (files_copied / total_files) * total_size_bytes
                                estimated_speed = estimated_bytes_copied / elapsed
                                speed_mbps = estimated_speed / (1024 * 1024)
                                speed_gbps = estimated_speed * 8 / 1_000_000_000
                                
                                # Calculate ETA
                                remaining_files = total_files - files_copied
                                if files_copied > 0:
                                    files_per_second = files_copied / elapsed
                                    eta_seconds = remaining_files / files_per_second if files_per_second > 0 else 0
                                    eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds)) if eta_seconds < 86400 else f"{eta_seconds/3600:.1f} hrs"
                                else:
                                    eta_str = "Calculating..."
                                
                                print(f"[PROGRESS_MONITOR_DEBUG] Sending progress update: {files_copied}/{total_files} ({progress_percent:.1f}%) at {speed_mbps:.1f} MB/s")
                                
                                # Send progress update
                                _send_status('progress', 'progress', 
                                           f'Ultra-fast copy: {files_copied}/{total_files} ({progress_percent:.1f}%)', 
                                           percent=progress_percent,
                                           files_copied=files_copied,
                                           total_files=total_files,
                                           speed_mbps=round(speed_mbps, 2),
                                           speed_gbps=round(speed_gbps, 3),
                                           eta_str=eta_str)
                                
                                last_file_count = files_copied
                        elif files_copied == 0 and current_time - start_time > 2.0:
                            # No files found yet after 2 seconds, send a "starting" update
                            print(f"[PROGRESS_MONITOR_DEBUG] No files detected yet after {current_time - start_time:.1f}s")
                            _send_status('progress', 'progress', 
                                       f'Robocopy starting... {total_files} files queued', 
                                       percent=1,
                                       files_copied=0,
                                       total_files=total_files,
                                       speed_mbps=0,
                                       speed_gbps=0,
                                       eta_str="Starting...")
                        
                        last_update_time = current_time
                    
                    time.sleep(0.5)  # Check every 0.5 seconds
                    
                except Exception as monitor_error:
                    print(f"[PROGRESS_MONITOR_ERROR] {monitor_error}")
                    import traceback
                    traceback.print_exc()
                    break
            
            print(f"[PROGRESS_MONITOR_DEBUG] Background monitoring thread finished")
        
        # Start background progress monitoring thread
        print(f"[SEQUENCE_COPY_DEBUG] Starting background progress monitoring thread...")
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # Send initial status to confirm monitoring is active
        _send_status('progress', 'progress', f'Robocopy started with {total_files} files...', 
                    percent=2, files_copied=0, total_files=total_files, 
                    speed_mbps=0, speed_gbps=0, eta_str="Preparing...")
        
        # Wait for robocopy to complete and capture results
        stdout, stderr = process.communicate()
        
        # Stop background monitoring
        stop_monitoring = True
        monitor_thread.join(timeout=2.0)
        
        # Calculate performance metrics
        end_time = time.time()
        duration = end_time - start_time
        speed_mbps = (total_size_bytes / (1024 * 1024)) / duration if duration > 0 else 0
        speed_gbps = speed_mbps / 1000
        
        print(f"[SEQUENCE_COPY_DEBUG] Batch robocopy completed in {duration:.2f}s")
        print(f"[SEQUENCE_COPY_DEBUG] Speed: {speed_mbps:.2f} MB/s ({speed_gbps:.2f} Gbps)")
        print(f"[SEQUENCE_COPY_DEBUG] Files copied: {total_files}")
        print(f"[SEQUENCE_COPY_DEBUG] Return code: {process.returncode}")
        
        # Parse robocopy output to detect skipped vs copied files
        if isinstance(stdout, bytes):
            stdout_str = stdout.decode('utf-8', errors='ignore')
        else:
            stdout_str = stdout  # Already a string
        print(f"[SEQUENCE_COPY_DEBUG] Final stdout:\n{stdout_str}")
        
        # Parse robocopy statistics from output
        files_copied = 0
        files_skipped = 0
        files_failed = 0
        
        lines = stdout_str.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Files :'):
                # Parse: "Files :       1771         0       1771         0         0         0"
                # Format: Total Copied Skipped Mismatch FAILED Extras
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        total_robocopy = int(parts[2])
                        files_copied = int(parts[3])
                        files_skipped = int(parts[4])
                        files_failed = int(parts[6])
                        
                        print(f"[ROBOCOPY_STATS] Total: {total_robocopy}, Copied: {files_copied}, Skipped: {files_skipped}, Failed: {files_failed}")
                        break
                    except (ValueError, IndexError) as e:
                        print(f"[ROBOCOPY_STATS] Failed to parse robocopy stats line: {line}, error: {e}")
        
        # Determine result based on robocopy return code and statistics
        if process.returncode == 0:
            # Return code 0: No files copied (all files already existed)
            if files_skipped > 0:
                success_message = f"⚠️ All {files_skipped} files already exist at destination - no copying needed"
                print(f"[SEQUENCE_COPY_DEBUG] {success_message}")
                
                if status_callback:
                    status_callback({
                        'type': 'sequence_operation_warning',
                        'data': {
                            'status': 'warning',
                            'message': success_message,
                            'source_dir': source_dir,
                            'transfer_id': transfer_id,
                            'total_files': files_skipped,
                            'files_skipped': files_skipped,
                            'speed_mbps': 0,
                            'speed_gbps': 0,
                            'percent': 100,
                            'operation': 'batch_copy'
                        }
                    })
                
                return (True, success_message)
            else:
                success_message = f"✅ No files to copy (empty or no matching pattern)"
                print(f"[SEQUENCE_COPY_DEBUG] {success_message}")
                return (True, success_message)
                
        elif process.returncode == 1:
            # Return code 1: Files copied successfully
            success_message = f"✅ BATCH COPY SUCCESS! {files_copied} files at {speed_mbps:.2f} MB/s ({speed_gbps:.2f} Gbps)"
            
            if files_skipped > 0:
                success_message += f" ({files_skipped} files already existed)"
            
            print(f"[SEQUENCE_COPY_DEBUG] {success_message}")
            
            if status_callback:
                status_callback({
                    'type': 'sequence_operation_success',
                    'data': {
                        'status': 'success',
                        'message': success_message,
                        'source_dir': source_dir,
                        'transfer_id': transfer_id,
                        'total_files': files_copied + files_skipped,
                        'files_copied': files_copied,
                        'files_skipped': files_skipped,
                        'speed_mbps': speed_mbps,
                        'speed_gbps': speed_gbps,
                        'percent': 100,
                        'operation': 'batch_copy'
                    }
                })
            
            return (True, success_message)
        else:
            # Error cases (return codes 4, 8, 16, etc.)
            error_message = f"Robocopy failed with return code {process.returncode}"
            if files_failed > 0:
                error_message += f" - {files_failed} files failed to copy"
            
            print(f"[SEQUENCE_COPY_DEBUG] Error: {error_message}")
            
            if status_callback:
                status_callback({
                    'type': 'sequence_operation_error',
                    'data': {
                        'status': 'error',
                        'message': error_message,
                        'source_dir': source_dir,
                        'transfer_id': transfer_id,
                        'files_failed': files_failed,
                        'operation': 'batch_copy'
                    }
                })
            
            return (False, error_message)
            
    except Exception as e:
        print(f"[SEQUENCE_COPY_ERROR] Batch copy failed: {e}")
        return _xcopy_sequence_fallback(source_dir, destination_dir, file_pattern, status_callback, transfer_id, 0, 0)

def _xcopy_sequence_fallback(source_dir: str, destination_dir: str, file_pattern: str,
                            status_callback: Optional[Callable], transfer_id: Optional[str],
                            total_files: int, total_size_bytes: int) -> Tuple[bool, str]:
    """Fallback to xcopy for batch sequence copying."""
    try:
        print(f"[SEQUENCE_COPY_DEBUG] Using xcopy for batch sequence fallback")
        
        # For xcopy, we need to copy all files matching pattern
        # Use xcopy with recursive and overwrite flags
        source_pattern = os.path.join(source_dir, file_pattern)
        cmd = ['xcopy', f'"{source_pattern}"', f'"{destination_dir}\\"', '/Y', '/H']
        
        print(f"[SEQUENCE_COPY_DEBUG] Executing xcopy: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, shell=True)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        speed_bps = total_size_bytes / elapsed_time if elapsed_time > 0.001 and total_size_bytes > 0 else 0
        speed_mbps = speed_bps / (1024 * 1024)
        speed_gbps = speed_bps * 8 / 1_000_000_000
        
        print(f"[SEQUENCE_COPY_DEBUG] Batch xcopy completed in {elapsed_time:.2f}s")
        print(f"[SEQUENCE_COPY_DEBUG] Speed: {speed_mbps:.2f} MB/s ({speed_gbps:.2f} Gbps)")
        print(f"[SEQUENCE_COPY_DEBUG] Return code: {result.returncode}")
        
        if result.returncode == 0:
            msg = f"✅ XCOPY BATCH SUCCESS! {total_files} files at {speed_mbps:.2f} MB/s ({speed_gbps:.2f} Gbps)"
            print(f"[SEQUENCE_COPY_DEBUG] {msg}")
            
            def _send_status(type_suffix: str, status_str: str, message: str, **kwargs):
                if status_callback:
                    data = {
                        'status': status_str,
                        'message': message,
                        'source_dir': source_dir,
                        'transfer_id': transfer_id,
                        **kwargs
                    }
                    status_callback({'type': f'sequence_operation_{type_suffix}', 'data': data})
            
            _send_status('success', 'success', msg,
                        total_files=total_files,
                        speed_mbps=round(speed_mbps, 2),
                        speed_gbps=round(speed_gbps, 2),
                        operation='batch_copy_xcopy')
            return True, msg
        else:
            msg = f"Xcopy batch failed with return code {result.returncode}"
            print(f"[SEQUENCE_COPY_ERROR] {msg}")
            return False, msg
            
    except Exception as e:
        msg = f"Batch copy fallback failed: {e}"
        print(f"[SEQUENCE_COPY_ERROR] {msg}")
        return False, msg

# TODO:
# - For move_item with FileTransfer: implement as copy_item then delete source. Ensure atomicity or recovery.
# - Multi-file support: A manager class to handle a queue of FileTransfer instances.
# - Auto-resume: Persist transfer state (e.g., .part file and metadata) and check on startup.
#   FileTransfer would need to support starting from an offset.
# - GUI integration for cancel/pause/resume buttons for each active transfer.