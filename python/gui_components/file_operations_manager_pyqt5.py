"""
File Operations Manager Module - PyQt5 Compatible

Handles file operations (copy/move) functionality
for the Clean Incomings GUI application.
"""

import os
import threading
from typing import List, Dict, Any
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QMetaObject, Qt
from python.gui_components.copy_move_progress_window_pyqt5 import CopyMoveProgressWindow


class FileOperationsManager:
    """Manages file operations for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the FileOperationsManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.active_operations = {}
        self._copy_move_progress_window = None
        self._pause_requested = False
        self._cancel_requested = False

    def on_copy_selected_click(self):
        """Handle copy selected button click."""
        selected_items = self.app.tree_manager.get_selected_items()
        
        if not selected_items:
            QMessageBox.warning(self.app, "No Selection", "Please select items to copy.")
            return
            
        self.start_file_operation(selected_items, operation_type="copy")

    def on_move_selected_click(self):
        """Handle move selected button click."""
        selected_items = self.app.tree_manager.get_selected_items()
        
        if not selected_items:
            QMessageBox.warning(self.app, "No Selection", "Please select items to move.")
            return
            
        # Confirm move operation
        reply = QMessageBox.question(
            self.app, 
            "Confirm Move", 
            f"Are you sure you want to move {len(selected_items)} items?\n\nThis will remove them from the source location.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_file_operation(selected_items, operation_type="move")

    def start_file_operation(self, items: List[Dict[str, Any]], operation_type: str):
        """
        Start file operation in background thread and show progress window.
        """
        if not items:
            return
        # Disable action buttons during operation
        if hasattr(self.app, 'copy_selected_btn'):
            self.app.copy_selected_btn.setEnabled(False)
        if hasattr(self.app, 'move_selected_btn'):
            self.app.move_selected_btn.setEnabled(False)
        # Update status
        self.app.status_manager.set_status(f"Starting {operation_type} operation for {len(items)} items...")
        # Calculate total bytes
        total_bytes = 0
        for item in items:
            if item.get('type') == 'Sequence':
                seq_info = item.get('sequence_info', {})
                files = seq_info.get('files', [])
                sizes = seq_info.get('sizes', [])
                if sizes and len(sizes) == len(files):
                    total_bytes += sum(sizes)
                else:
                    # Fallback: try os.path.getsize
                    for filename in files:
                        src_file = item.get('source_path', '')
                        src_dir = os.path.dirname(src_file)
                        fp = os.path.join(src_dir, filename)
                        try:
                            total_bytes += os.path.getsize(fp)
                        except Exception:
                            pass
            else:
                src_file = item.get('source_path', '')
                try:
                    total_bytes += os.path.getsize(src_file)
                except Exception:
                    pass
        # Show progress window
        self._copy_move_progress_window = CopyMoveProgressWindow(operation_type=operation_type.title(), parent=self.app)
        self._copy_move_progress_window.set_total(len(items), total_bytes)
        self._copy_move_progress_window.pause_resume_requested.connect(self._on_pause_resume)
        self._copy_move_progress_window.cancel_requested.connect(self._on_cancel)
        self._copy_move_progress_window.show()
        self._pause_requested = False
        self._cancel_requested = False
        # Start operation in background thread
        operation_thread = threading.Thread(
            target=self._file_operation_worker,
            args=(items, operation_type),
            daemon=True
        )
        operation_thread.start()

    def _file_operation_worker(self, items: List[Dict[str, Any]], operation_type: str):
        """
        Worker thread for file operations. Updates progress window and supports pause/cancel.
        """
        try:
            success_count = 0
            error_count = 0
            files_done = 0
            bytes_done = 0
            total_files = len(items)
            # Calculate total bytes (again for safety)
            total_bytes = 0
            for item in items:
                if item.get('type') == 'Sequence':
                    seq_info = item.get('sequence_info', {})
                    files = seq_info.get('files', [])
                    sizes = seq_info.get('sizes', [])
                    if sizes and len(sizes) == len(files):
                        total_bytes += sum(sizes)
                    else:
                        for filename in files:
                            src_file = item.get('source_path', '')
                            src_dir = os.path.dirname(src_file)
                            fp = os.path.join(src_dir, filename)
                            try:
                                total_bytes += os.path.getsize(fp)
                            except Exception:
                                pass
                else:
                    src_file = item.get('source_path', '')
                    try:
                        total_bytes += os.path.getsize(src_file)
                    except Exception:
                        pass
            # Progress tracking
            for i, item in enumerate(items):
                if self._cancel_requested:
                    self._update_progress_window(files_done, bytes_done, "Operation cancelled by user.")
                    break
                # Soft pause: pause between files
                while self._pause_requested and not self._cancel_requested:
                    QMetaObject.invokeMethod(self._copy_move_progress_window, "setWindowTitle", Qt.QueuedConnection, 
                        None, f"{operation_type.title()} Progress (Paused)")
                    QTimer.singleShot(200, lambda: None)
                    time.sleep(0.2)
                QMetaObject.invokeMethod(self._copy_move_progress_window, "setWindowTitle", Qt.QueuedConnection, 
                    None, f"{operation_type.title()} Progress")
                try:
                    source_path = item.get('source_path', '')
                    dest_path = item.get('destination_path', '')
                    if not source_path or not dest_path:
                        error_count += 1
                        continue
                    # Perform the operation
                    before_bytes = bytes_done
                    if operation_type == "copy":
                        success, file_bytes, filename = self._copy_item_with_progress(source_path, dest_path, item)
                    else:
                        success, file_bytes, filename = self._move_item_with_progress(source_path, dest_path, item)
                    if success:
                        files_done += 1
                        bytes_done += file_bytes
                        success_count += 1
                    else:
                        error_count += 1
                    # Update progress window
                    self._update_progress_window(files_done, bytes_done, filename)
                except Exception as e:
                    error_count += 1
            # Final status update
            total_items = len(items)
            if error_count == 0 and not self._cancel_requested:
                status_msg = f"{operation_type.title()} completed successfully: {success_count}/{total_items} items"
            elif self._cancel_requested:
                status_msg = f"{operation_type.title()} cancelled: {success_count} succeeded, {error_count} failed"
            else:
                status_msg = f"{operation_type.title()} completed with errors: {success_count} succeeded, {error_count} failed"
            self._update_progress_window(files_done, bytes_done, status_msg, done=True)
            self.app.status_manager.set_status(status_msg)
        except Exception as e:
            self.app.status_manager.set_status(f"{operation_type.title()} operation failed: {str(e)}")
        finally:
            # Re-enable action buttons
            if hasattr(self.app, 'copy_selected_btn'):
                self.app.copy_selected_btn.setEnabled(True)
            if hasattr(self.app, 'move_selected_btn'):
                self.app.move_selected_btn.setEnabled(True)
            if self._copy_move_progress_window:
                QMetaObject.invokeMethod(self._copy_move_progress_window, "close", Qt.QueuedConnection)

    def _copy_item_with_progress(self, source_path, dest_path, item_data):
        """Copy item and return (success, bytes_copied, filename) for progress."""
        try:
            if item_data.get('type') == 'Sequence':
                seq_info = item_data.get('sequence_info', {})
                files = seq_info.get('files', [])
                sizes = seq_info.get('sizes', [])
                src_dir = os.path.dirname(source_path)
                dest_dir = os.path.dirname(dest_path)
                total_bytes = 0
                for idx, filename in enumerate(files):
                    src_file = os.path.join(src_dir, filename)
                    dst_file = os.path.join(dest_dir, filename)
                    try:
                        import shutil
                        shutil.copy2(src_file, dst_file)
                        sz = sizes[idx] if sizes and idx < len(sizes) else os.path.getsize(src_file)
                        total_bytes += sz
                    except Exception:
                        pass
                return True, total_bytes, files[-1] if files else ""
            else:
                import shutil
                shutil.copy2(source_path, dest_path)
                sz = os.path.getsize(source_path)
                return True, sz, os.path.basename(source_path)
        except Exception as e:
            return False, 0, os.path.basename(source_path)

    def _move_item_with_progress(self, source_path, dest_path, item_data):
        """Move item and return (success, bytes_moved, filename) for progress."""
        success, file_bytes, filename = self._copy_item_with_progress(source_path, dest_path, item_data)
        if success:
            try:
                if item_data.get('type') == 'Sequence':
                    seq_info = item_data.get('sequence_info', {})
                    files = seq_info.get('files', [])
                    src_dir = os.path.dirname(source_path)
                    for filename in files:
                        src_file = os.path.join(src_dir, filename)
                        if os.path.exists(src_file):
                            os.remove(src_file)
                else:
                    if os.path.exists(source_path):
                        os.remove(source_path)
            except Exception:
                pass
        return success, file_bytes, filename

    def _update_progress_window(self, files_done, bytes_done, current_file, done=False):
        if not self._copy_move_progress_window:
            return
        def update():
            if done:
                self._copy_move_progress_window.update_progress(files_done, bytes_done, current_file)
                self._copy_move_progress_window.close()
            else:
                self._copy_move_progress_window.update_progress(files_done, bytes_done, current_file)
        QMetaObject.invokeMethod(self._copy_move_progress_window, update, Qt.QueuedConnection)

    def _on_pause_resume(self):
        self._pause_requested = not self._pause_requested

    def _on_cancel(self):
        self._cancel_requested = True
        if self._copy_move_progress_window:
            QMetaObject.invokeMethod(self._copy_move_progress_window, "close", Qt.QueuedConnection)

    def _copy_item(self, source_path: str, dest_path: str, item_data: Dict[str, Any]) -> bool:
        """
        Copy a single item.
        
        Args:
            source_path: Source file/directory path
            dest_path: Destination path
            item_data: Item metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Check if it's a sequence or single file
            if item_data.get('type') == 'Sequence':
                return self._copy_sequence(source_path, dest_path, item_data)
            else:
                return self._copy_single_file(source_path, dest_path)
                
        except Exception as e:
            print(f"Error copying {source_path}: {e}")
            return False

    def _move_item(self, source_path: str, dest_path: str, item_data: Dict[str, Any]) -> bool:
        """
        Move a single item.
        
        Args:
            source_path: Source file/directory path
            dest_path: Destination path
            item_data: Item metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # For move operations, we first copy then delete source
            if self._copy_item(source_path, dest_path, item_data):
                # Remove source after successful copy
                if item_data.get('type') == 'Sequence':
                    return self._remove_sequence_files(source_path, item_data)
                else:
                    if os.path.exists(source_path):
                        os.remove(source_path)
                        return True
            return False
                
        except Exception as e:
            print(f"Error moving {source_path}: {e}")
            return False

    def _copy_single_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a single file."""
        try:
            import shutil
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                return True
            else:
                print(f"Source file not found: {source_path}")
                return False
        except Exception as e:
            print(f"Error copying file {source_path}: {e}")
            return False

    def _copy_sequence(self, source_path: str, dest_path: str, item_data: Dict[str, Any]) -> bool:
        """Copy a sequence of files."""
        try:
            import shutil
            
            # Get sequence info if available
            sequence_info = item_data.get('sequence_info', {})
            files = sequence_info.get('files', [])
            
            if not files:
                # Fall back to single file copy if no sequence info
                return self._copy_single_file(source_path, dest_path)
            
            # Copy all files in the sequence
            source_dir = os.path.dirname(source_path)
            dest_dir = os.path.dirname(dest_path)
            
            success_count = 0
            for filename in files:
                try:
                    src_file = os.path.join(source_dir, filename)
                    dst_file = os.path.join(dest_dir, filename)
                    
                    if os.path.exists(src_file):
                        shutil.copy2(src_file, dst_file)
                        success_count += 1
                    else:
                        print(f"Sequence file not found: {src_file}")
                        
                except Exception as e:
                    print(f"Error copying sequence file {filename}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error copying sequence {source_path}: {e}")
            return False

    def _remove_sequence_files(self, source_path: str, item_data: Dict[str, Any]) -> bool:
        """Remove sequence files after successful move."""
        try:
            sequence_info = item_data.get('sequence_info', {})
            files = sequence_info.get('files', [])
            
            if not files:
                # Fall back to single file removal
                if os.path.exists(source_path):
                    os.remove(source_path)
                    return True
                return False
            
            # Remove all files in the sequence
            source_dir = os.path.dirname(source_path)
            success_count = 0
            
            for filename in files:
                try:
                    src_file = os.path.join(source_dir, filename)
                    if os.path.exists(src_file):
                        os.remove(src_file)
                        success_count += 1
                except Exception as e:
                    print(f"Error removing sequence file {filename}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error removing sequence files: {e}")
            return False
