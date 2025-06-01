"""
File Operations Manager Module - PyQt5 Compatible

Handles file operations (copy/move) functionality
for the Clean Incomings GUI application.
"""

import os
import threading
from typing import List, Dict, Any
from PyQt5.QtWidgets import QMessageBox


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
        Start file operation in background thread.
        
        Args:
            items: List of items to process
            operation_type: Either "copy" or "move"
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
        
        # Start operation in background thread
        operation_thread = threading.Thread(
            target=self._file_operation_worker,
            args=(items, operation_type),
            daemon=True
        )
        operation_thread.start()

    def _file_operation_worker(self, items: List[Dict[str, Any]], operation_type: str):
        """
        Worker thread for file operations.
        
        Args:
            items: List of items to process
            operation_type: Either "copy" or "move"
        """
        try:
            success_count = 0
            error_count = 0
            
            for i, item in enumerate(items):
                try:
                    source_path = item.get('source_path', '')
                    dest_path = item.get('destination_path', '')
                    
                    if not source_path or not dest_path:
                        print(f"Skipping item {i+1}: missing source or destination path")
                        error_count += 1
                        continue
                    
                    # Update progress
                    progress = (i / len(items)) * 100
                    filename = os.path.basename(source_path)
                    self.app.status_manager.update_progress(
                        progress, 
                        f"{operation_type.title()}ing: {filename}"
                    )
                    
                    # Perform the operation
                    if operation_type == "copy":
                        success = self._copy_item(source_path, dest_path, item)
                    else:  # move
                        success = self._move_item(source_path, dest_path, item)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"Error processing item {i+1}: {e}")
                    error_count += 1
            
            # Final status update
            total_items = len(items)
            if error_count == 0:
                status_msg = f"{operation_type.title()} completed successfully: {success_count}/{total_items} items"
            else:
                status_msg = f"{operation_type.title()} completed with errors: {success_count} succeeded, {error_count} failed"
            
            self.app.status_manager.set_status(status_msg)
            
        except Exception as e:
            print(f"Error in file operation worker: {e}")
            self.app.status_manager.set_status(f"{operation_type.title()} operation failed: {str(e)}")
        
        finally:
            # Re-enable action buttons
            if hasattr(self.app, 'copy_selected_btn'):
                self.app.copy_selected_btn.setEnabled(True)
            if hasattr(self.app, 'move_selected_btn'):
                self.app.move_selected_btn.setEnabled(True)

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
