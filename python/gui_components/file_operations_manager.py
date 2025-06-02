"""
File Operations Manager Module

Handles file copy/move operations and related functionality
for the Clean Incomings GUI application.
"""

import os
import threading
import uuid
import time
import concurrent.futures
from typing import Callable, Dict, Any, List
from python.file_operations_utils.file_management import copy_item, move_item, copy_sequence_batch, move_sequence_batch
from PyQt5.QtCore import QMetaObject, Qt, QTimer, pyqtSignal, QObject
from python.gui_components.copy_move_progress_window_pyqt5 import CopyMoveProgressWindow

class BatchProgressSignalHelper(QObject):
    batch_progress_update = pyqtSignal(dict)

class FileOperationsManager:
    """Manages file operations like copy and move for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the FileOperationsManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.active_transfers = {}  # Dictionary to store FileTransfer instances by transfer_id
        self.current_batch_id = None
        self.current_operation_type = None
        self._copy_move_progress_window = None
        self._pause_requested = False
        # Threading configuration for parallel file operations
        self.max_concurrent_transfers = 4  # Maximum concurrent file transfers
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_transfers)
        self.shutdown_requested = False
        # --- Batch progress signal helper for thread-safe UI updates ---
        self._batch_signal_helper = BatchProgressSignalHelper()
        self._batch_signal_helper.batch_progress_update.connect(self._on_batch_progress_update)

    def copy_files(self, items_to_copy: List[Dict[str, Any]]):
        """Copy selected files/sequences using batch operations for maximum efficiency."""
        self._start_optimized_batch_operation("Copy", items_to_copy)

    def move_files(self, items_to_move: List[Dict[str, Any]]):
        """Move selected files/sequences using batch operations for maximum efficiency."""
        self._start_optimized_batch_operation("Move", items_to_move)

    def _on_batch_progress_update(self, update_data):
        """
        Slot to update batch progress UI on the main thread via signal.
        """
        try:
            progress_window = self._copy_move_progress_window
            if not progress_window:
                print("[BATCH_SIGNAL] No progress window to update.")
                return
            data = update_data.get('data', {})
            status = data.get('status', '')
            files_copied = data.get('files_copied', 0)
            file_count = data.get('total_files', 1)
            percent = data.get('percent', 0)
            speed_mbps = data.get('speed_mbps', 0.0)
            eta_str = data.get('eta_str', 'Calculating...')
            current_file = data.get('current_file', '')
            estimated_transferred = data.get('transferred_bytes')
            if estimated_transferred is None:
                # fallback to estimate if needed
                estimated_transferred = files_copied * 2000000  # Assume 2MB per file
            total_size = data.get('total_size', 0)
            file_size = data.get('file_size', None)
            print(f"[BATCH_SIGNAL] Updating progress: files_done={files_copied}, bytes_done={estimated_transferred}, current_file={current_file}, speed={speed_mbps}, eta={eta_str}")
            # Aggregate progress: update only the file count, not per-batch details
            # Use the grand total for correct aggregate progress
            total_files = self.aggregate_total_files if hasattr(self, 'aggregate_total_files') else file_count
            percent = int(100 * files_copied / total_files) if total_files else 0
            # ETA calculation: estimate based on elapsed time and rate
            elapsed = getattr(self, '_aggregate_start_time', None)
            if elapsed is None:
                self._aggregate_start_time = time.time()
                elapsed = 0
            else:
                elapsed = time.time() - self._aggregate_start_time
            eta_str = ''
            if files_copied > 0 and elapsed > 2:
                est_total = elapsed * total_files / files_copied
                eta_sec = int(est_total - elapsed)
                if eta_sec > 0:
                    m, s = divmod(eta_sec, 60)
                    h, m = divmod(m, 60)
                    if h:
                        eta_str = f"ETA: {h}h {m}m {s}s"
                    elif m:
                        eta_str = f"ETA: {m}m {s}s"
                    else:
                        eta_str = f"ETA: {s}s"
            progress_window.update_aggregate_progress(files_copied, total_files)
            progress_window.label_eta.setText(eta_str)
            # (Optionally, speed can be set here if desired)
            # Do NOT close the window automatically; user must close via the Close button
        except Exception as err:
            import traceback
            print(f"[BATCH_SIGNAL_ERROR] Exception in _on_batch_progress_update: {err}")
            traceback.print_exc()

    def _start_optimized_batch_operation(self, operation_type: str, items_to_process: List[Dict[str, Any]]):
        """Start an optimized batch operation that groups sequences for maximum 10GbE performance."""
        self.current_batch_id = str(uuid.uuid4())
        self.current_operation_type = operation_type
        self.shutdown_requested = False
        
        # Separate sequences from individual files for optimized processing
        sequence_batches = []
        individual_files = []
        
        for item_data in items_to_process:
            item_type = item_data.get('type', 'file')
            
            if item_type == 'Sequence':
                # Handle sequences as batch operations
                sequence_info = item_data.get('sequence_info', {})
                files_list = sequence_info.get('files', [])
                sequence_dest_path = item_data.get('new_destination_path', '')
                
                if files_list and sequence_dest_path:
                    # Get source directory from first file
                    first_file_path = files_list[0].get('path', '')
                    if first_file_path:
                        source_dir = os.path.dirname(first_file_path)
                        dest_dir = os.path.dirname(sequence_dest_path)
                        
                        # Create a pattern for the sequence files
                        # Extract the common pattern from the filename
                        base_names = [os.path.basename(f.get('path', '')) for f in files_list if f.get('path')]
                        if base_names:
                            # Find common prefix and create pattern
                            # For OLNT0010_main_arch_rgb_LL1804k_sRGBg24_PREVIZ_v022.1001.png
                            # Create pattern like OLNT0010_main_arch_rgb_*.png
                            common_prefix = self._find_common_prefix(base_names)
                            file_extension = os.path.splitext(base_names[0])[1]
                            pattern = f"{common_prefix}*{file_extension}"
                            
                            # Skip redundant size calculation - not needed for copy/move operations
                            # Progress will be tracked by file count instead of bytes
                            total_size_bytes = 0  # Will be calculated during transfer if needed
                            
                            print(f"[BATCH_DEBUG] Skipping size calculation - will track progress by file count")
                            
                            sequence_batch = {
                                'type': 'sequence_batch',
                                'source_dir': source_dir,
                                'dest_dir': dest_dir, 
                                'pattern': pattern,
                                'file_count': len(files_list),
                                'total_size': total_size_bytes,
                                'sequence_name': item_data.get('filename', 'Unknown Sequence')
                            }
                            sequence_batches.append(sequence_batch)
                            
                            print(f"[BATCH_DEBUG] Created sequence batch:")
                            print(f"  Source: {source_dir}")
                            print(f"  Dest: {dest_dir}")
                            print(f"  Pattern: {pattern}")
                            print(f"  Files: {len(files_list)}")
                            print(f"  Total Size: {sequence_batch['total_size']} bytes")
            else:
                # Handle individual files
                source_path = item_data.get('source_path', '')
                if source_path and os.path.exists(source_path):
                    file_size = os.path.getsize(source_path) if os.path.isfile(source_path) else 0
                    file_data = {
                        'source_path': source_path,
                        'destination_path': item_data.get('new_destination_path', ''),
                        'file_name': os.path.basename(source_path),
                        'operation': operation_type.lower(),
                        'total_size': file_size
                    }
                    individual_files.append(file_data)
        
        total_operations = len(sequence_batches) + len(individual_files)
        total_files = sum(b['file_count'] for b in sequence_batches) + len(individual_files)
        
        if total_operations == 0:
            self.app.status_manager.add_log_message("No valid files found to process", "WARNING")
            return
        
        self.app.status_manager.add_log_message(
            f"🚀 Starting OPTIMIZED {operation_type.lower()} operation:", "INFO"
        )
        self.app.status_manager.add_log_message(
            f"  • {len(sequence_batches)} sequence batches ({sum(b['file_count'] for b in sequence_batches)} files)", "INFO"
        )
        self.app.status_manager.add_log_message(
            f"  • {len(individual_files)} individual files", "INFO"
        )
        self.app.status_manager.add_log_message(
            f"  • Total: {total_files} files in {total_operations} operations", "INFO"
        )
        
        # --- AGGREGATE PROGRESS STATE ---
        self.aggregate_total_files = total_files
        self.aggregate_files_copied = 0
        self.aggregate_batches_completed = 0
        self.aggregate_batches_total = len(sequence_batches) + (1 if individual_files else 0)
        self._aggregate_lock = threading.Lock()

        # Show PyQt5 floating progress window (never closes automatically)
        if self._copy_move_progress_window:
            QMetaObject.invokeMethod(self._copy_move_progress_window, "close", Qt.QueuedConnection)
        self._copy_move_progress_window = CopyMoveProgressWindow(operation_type=operation_type.title(), parent=self.app)
        progress_window = self._copy_move_progress_window
        print(f"[DEBUG] Progress window CREATED: {progress_window} (id(self)={id(self)})", flush=True)
        progress_window.set_total(total_files, 0)
        progress_window.pause_resume_requested.connect(self._on_pause_resume)
        progress_window.cancel_requested.connect(self._on_cancel)
        progress_window.show()
        print(f"[DEBUG] Progress window SHOWN: {progress_window.isVisible()} (id(self)={id(self)})", flush=True)

        def aggregate_progress_callback(batch_files_copied):
            with self._aggregate_lock:
                self.aggregate_files_copied += batch_files_copied
                percent = int(100 * self.aggregate_files_copied / self.aggregate_total_files) if self.aggregate_total_files else 0
                # Only emit signal for overall progress
                self._batch_signal_helper.batch_progress_update.emit({
                    'data': {
                        'status': 'progress',
                        'files_copied': self.aggregate_files_copied,
                        'total_files': self.aggregate_total_files,
                        'percent': percent,
                        'current_file': '',
                        'speed_mbps': 0.0,
                        'eta_str': '',
                    }
                })

        # Start optimized multithreaded operations
        def start_optimized_operations():
            try:
                # Process sequence batches first (much faster)
                for batch_data in sequence_batches:
                    if self.shutdown_requested:
                        break
                    transfer_id = str(uuid.uuid4())
                    print(f"[BATCH_DEBUG] Processing sequence batch with {batch_data['file_count']} files...")
                    
                    # Custom progress callback for sequence batches
                    def create_batch_progress_callback():
                        last_files_copied = {'val': 0}
                        def batch_progress_callback(status_data):
                            data = status_data.get('data', {})
                            files_copied = data.get('files_copied', 0)
                            # Only aggregate the delta since the last update
                            delta = files_copied - last_files_copied['val']
                            if delta > 0:
                                aggregate_progress_callback(delta)
                                last_files_copied['val'] = files_copied
                        return batch_progress_callback
                    
                    # Execute sequence batch operation - use correct function based on operation type
                    if operation_type == "Copy":
                        success, message = copy_sequence_batch(
                            source_dir=batch_data['source_dir'],
                            destination_dir=batch_data['dest_dir'],
                            file_pattern=batch_data['pattern'],
                            status_callback=create_batch_progress_callback(),
                            transfer_id=transfer_id,
                            file_count=batch_data['file_count'],
                            total_size=batch_data['total_size']
                        )
                    else:
                        success, message = move_sequence_batch(
                            source_dir=batch_data['source_dir'],
                            destination_dir=batch_data['dest_dir'],
                            file_pattern=batch_data['pattern'],
                            status_callback=create_batch_progress_callback(),
                            transfer_id=transfer_id,
                            file_count=batch_data['file_count'],
                            total_size=batch_data['total_size']
                        )
                    if not success:
                        def mark_batch_error():
                            self.app.status_manager.add_log_message(
                                f"Batch failed: {message}", "ERROR"
                            )
                        QTimer.singleShot(0, mark_batch_error)
                
                # Process individual files with traditional threading
                if individual_files:
                    operation_func = copy_item if operation_type == "Copy" else move_item
                    
                    # Submit individual files for processing
                    future_to_file = {}
                    for file_data in individual_files:
                        if self.shutdown_requested:
                            break
                        
                        transfer_id = str(uuid.uuid4())
                        
                        future = self.thread_pool.submit(
                            self._execute_file_operation_worker,
                            operation_func,
                            file_data['source_path'],
                            file_data['destination_path'],
                            transfer_id,
                            file_data['file_name'],
                            0,  # file_number (not used for individual files)
                            1   # total_files (not used for individual files)
                        )
                        future_to_file[future] = file_data
                    
                    # Wait for individual files to complete
                    for future in concurrent.futures.as_completed(future_to_file):
                        if self.shutdown_requested:
                            break
                        
                        file_data = future_to_file[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            self.app.status_manager.add_log_message(
                                f"Error processing {file_data['file_name']}: {str(e)}", "ERROR"
                            )
                
                # Final completion message
                if not self.shutdown_requested:
                    self.app.status_manager.add_log_message(
                        f"🎯 OPTIMIZED {operation_type.lower()} operation completed! Sequences processed as batches for maximum speed.", "INFO"
                    )
                
            except Exception as e:
                self.app.status_manager.add_log_message(
                    f"Error in optimized {operation_type.lower()} operation: {str(e)}", "ERROR"
                )
        
        # Start in background thread
        batch_thread = threading.Thread(target=start_optimized_operations, daemon=True)
        batch_thread.start()

    def _find_common_prefix(self, filenames: List[str]) -> str:
        """Find the common prefix of a list of filenames for pattern creation."""
        if not filenames:
            return ""
        
        # For sequences like: OLNT0010_main_arch_rgb_LL1804k_sRGBg24_PREVIZ_v022.1001.png
        # Find the part before the frame number
        
        # Remove extensions first
        names_without_ext = [os.path.splitext(name)[0] for name in filenames]
        
        if len(names_without_ext) < 2:
            # Single file, find where numbers start from the end
            name = names_without_ext[0]
            # Find the last non-digit part
            for i in range(len(name) - 1, -1, -1):
                if not name[i].isdigit() and name[i] != '.':
                    return name[:i+1]
            return name
        
        # Find common prefix among all names
        prefix = names_without_ext[0]
        for name in names_without_ext[1:]:
            # Find common prefix
            common_len = 0
            for i in range(min(len(prefix), len(name))):
                if prefix[i] == name[i]:
                    common_len += 1
                else:
                    break
            prefix = prefix[:common_len]
        
        # Remove trailing frame numbers and dots
        while prefix and (prefix[-1].isdigit() or prefix[-1] == '.'):
            prefix = prefix[:-1]
        
        return prefix

    def _execute_file_operation_worker(self, operation_func: Callable, source_path: str, destination_path: str, transfer_id: str, file_name: str, file_number: int, total_files: int):
        """Worker function to execute a file operation with detailed progress tracking."""
        operation_name = "Copy" if operation_func == copy_item else "Move"
        try:
            self.app.status_manager.add_log_message(
                f"{operation_name} worker (ID: {transfer_id}) started for: {file_name} -> {destination_path}",
                "DEBUG"
            )
            def progress_callback(status_data):
                def update_ui():
                    try:
                        data = status_data.get('data', {})
                        transferred = data.get('transferred_bytes', 0)
                        files_done = 1  # Only one file in this worker
                        current_file = file_name
                        speed_mbps = data.get('speed_mbps', 0.0)
                        eta_str = data.get('eta_str', 'Calculating...')
                        if self._copy_move_progress_window:
                            def safe_update():
                                print(f"[QT_DEBUG] File progress: files_done={files_done}, bytes_done={transferred}, current_file={current_file}, speed={speed_mbps}, eta={eta_str}")
                                self._copy_move_progress_window.update_progress(files_done, transferred, current_file)
                                self._copy_move_progress_window.label_speed.setText(f"Speed: {speed_mbps:.2f} MB/s" if speed_mbps > 0 else "Speed: Calculating...")
                                self._copy_move_progress_window.label_eta.setText(f"ETA: {eta_str}")
                            QTimer.singleShot(0, safe_update)
                        # On completion, close the window
                        if data.get('status') == 'success' or data.get('status') == 'error':
                            if self._copy_move_progress_window:
                                QMetaObject.invokeMethod(self._copy_move_progress_window, "close", Qt.QueuedConnection)
                    except Exception as ui_error:
                        print(f"Error updating progress UI: {ui_error}")
                QTimer.singleShot(0, update_ui)
            success, message = operation_func(
                source_path=source_path,
                destination_path=destination_path,
                status_callback=progress_callback,
                transfer_id=transfer_id
            )
            if success:
                def mark_success():
                    try:
                        self.app.status_manager.add_log_message(
                            f"file_operation_success: Successfully {operation_name.lower()}ed {file_name} to {destination_path}",
                            "DEBUG"
                        )
                    except Exception as success_error:
                        print(f"Error marking success: {success_error}")
                QTimer.singleShot(0, mark_success)
                return (success, message)
            else:
                def mark_failed():
                    try:
                        self.app.status_manager.add_log_message(
                            f"file_operation_error: Failed to {operation_name.lower()} {file_name}: {message}",
                            "ERROR"
                        )
                    except Exception as failed_error:
                        print(f"Error marking failure: {failed_error}")
                QTimer.singleShot(0, mark_failed)
                raise Exception(message)
        except Exception as worker_exception:
            error_message = str(worker_exception)
            def handle_error():
                try:
                    self.app.status_manager.add_log_message(
                        f"file_operation_exception: Error in {operation_name.lower()} operation for {file_name}: {error_message}",
                        "ERROR"
                    )
                except Exception as handler_error:
                    print(f"Error in error handler: {handler_error}")
            QTimer.singleShot(0, handle_error)
            raise

    def shutdown(self):
        """Shutdown the file operations manager and clean up resources."""
        self.shutdown_requested = True
        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)

    def _on_pause_resume(self):
        """Handle pause/resume requested from the PyQt5 progress window."""
        self._pause_requested = not self._pause_requested
        self.app.status_manager.add_log_message(
            f"Pause/Resume requested. Now paused: {self._pause_requested}", "INFO"
        )
        # Implement soft pause logic between files if possible

    def _on_cancel(self):
        """Handle cancel requested from the PyQt5 progress window."""
        self.shutdown_requested = True
        self.app.status_manager.add_log_message(
            f"Cancel requested by user. Shutting down batch operation.", "WARNING"
        )
        if self._copy_move_progress_window:
            QMetaObject.invokeMethod(self._copy_move_progress_window, "close", Qt.QueuedConnection)

    def handle_transfer_cancellation(self, transfer_id: str):
        """Handle transfer cancellation requests."""
        try:
            if transfer_id in self.active_transfers:
                self.active_transfers[transfer_id]['status'] = 'cancelled'
                self.app.status_manager.add_log_message(
                    f"Transfer {transfer_id} cancelled by user", "INFO"
                )
                
                # Note: Actual cancellation would need to interrupt the file operation
                # This would require more sophisticated threading controls
                
        except Exception as e:
            self.app.status_manager.add_log_message(
                f"Error handling transfer cancellation: {str(e)}", "ERROR"
            )

    def on_copy_selected_click(self):
        """Handle copy button click - wrapper for backward compatibility."""
        print("Copy button clicked")
        
        # Get selected items from the preview tree
        try:
            selected_items = self.app.tree_manager.get_selected_items()
            
            if not selected_items:
                self.app.status_manager.add_log_message("No items selected for copying", "WARNING")
                return
            
            destination_folder = self.app.selected_destination_folder.get().strip()
            if not destination_folder or not os.path.isdir(destination_folder):
                self.app.status_manager.add_log_message("Invalid destination folder selected", "ERROR")
                return
            
            # Use optimized batch operation
            self.copy_files(selected_items)
            
        except Exception as e:
            self.app.status_manager.add_log_message(f"Error starting copy operation: {str(e)}", "ERROR")
            print(f"Error in copy operation: {e}")

    def on_move_selected_click(self):
        """Handle move button click - wrapper for backward compatibility."""
        print("Move button clicked")
        
        # Get selected items from the preview tree
        try:
            selected_items = self.app.tree_manager.get_selected_items()
            
            if not selected_items:
                self.app.status_manager.add_log_message("No items selected for moving", "WARNING")
                return
            
            destination_folder = self.app.selected_destination_folder.get().strip()
            if not destination_folder or not os.path.isdir(destination_folder):
                self.app.status_manager.add_log_message("Invalid destination folder selected", "ERROR")
                return
            
            # Use optimized batch operation
            self.move_files(selected_items)
            
        except Exception as e:
            self.app.status_manager.add_log_message(f"Error starting move operation: {str(e)}", "ERROR")
            print(f"Error in move operation: {e}") 