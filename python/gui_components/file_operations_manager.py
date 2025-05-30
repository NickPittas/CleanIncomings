"""
File Operations Manager Module

Handles file copy/move operations and related functionality
for the Clean Incomings GUI application.
"""

import os
import threading
import uuid
import concurrent.futures
from typing import Callable, Dict, Any, List
from python.file_operations_utils.file_management import copy_item, move_item, copy_sequence_batch, move_sequence_batch


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
        
        # Threading configuration for parallel file operations
        self.max_concurrent_transfers = 4  # Maximum concurrent file transfers
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_transfers)
        self.shutdown_requested = False

    def copy_files(self, items_to_copy: List[Dict[str, Any]]):
        """Copy selected files/sequences using batch operations for maximum efficiency."""
        self._start_optimized_batch_operation("Copy", items_to_copy)

    def move_files(self, items_to_move: List[Dict[str, Any]]):
        """Move selected files/sequences using batch operations for maximum efficiency."""
        self._start_optimized_batch_operation("Move", items_to_move)

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
        
        # Show progress window
        if hasattr(self.app, 'file_operations_progress'):
            self.app.file_operations_progress.start_operation_batch(operation_type, total_files)
        
        # Start optimized multithreaded operations
        def start_optimized_operations():
            try:
                # Process sequence batches first (much faster)
                for batch_data in sequence_batches:
                    if self.shutdown_requested:
                        break
                    
                    transfer_id = str(uuid.uuid4())
                    
                    # Add batch to progress tracking
                    if hasattr(self.app, 'file_operations_progress'):
                        self.app.file_operations_progress.add_transfer(
                            transfer_id, 
                            f"{batch_data['sequence_name']} ({batch_data['file_count']} files)", 
                            batch_data.get('operation', operation_type.lower()), 
                            batch_data['total_size']
                        )
                    
                    print(f"[BATCH_DEBUG] Processing sequence batch with {batch_data['file_count']} files...")
                    
                    # Custom progress callback for sequence batches
                    def create_batch_progress_callback(captured_batch_data, captured_transfer_id):
                        def batch_progress_callback(status_data):
                            print(f"[BATCH_CALLBACK_DEBUG] Received status update: {status_data}")
                            
                            def update_batch_ui():
                                try:
                                    print(f"[BATCH_UI_DEBUG] Processing status update in UI thread")
                                    
                                    if hasattr(self.app, 'file_operations_progress'):
                                        data = status_data.get('data', {})
                                        status = data.get('status', '')
                                        
                                        print(f"[BATCH_UI_DEBUG] Status: {status}, Data keys: {list(data.keys())}")
                                        print(f"[BATCH_UI_DEBUG] Captured batch total_size: {captured_batch_data.get('total_size', 'NOT_FOUND')}")
                                        
                                        if status == 'success':
                                            # Batch completed successfully
                                            speed_mbps = data.get('speed_mbps', 0)
                                            speed_gbps = data.get('speed_gbps', 0)
                                            file_count = data.get('total_files', data.get('file_count', 0))
                                            
                                            print(f"[BATCH_UI_DEBUG] Success - completing transfer {captured_transfer_id}")
                                            
                                            # Mark as completed with speed info
                                            self.app.file_operations_progress.complete_transfer(
                                                captured_transfer_id, True, 
                                                f"✅ {file_count} files at {speed_mbps:.1f} MB/s ({speed_gbps:.1f} Gbps)"
                                            )
                                            
                                            self.app.status_manager.add_log_message(
                                                f"✅ BATCH SUCCESS: {file_count} files at {speed_mbps:.1f} MB/s ({speed_gbps:.1f} Gbps)", 
                                                "INFO"
                                            )
                                        elif status == 'progress':
                                            # Extract progress values
                                            files_copied = data.get('files_copied', 0)
                                            file_count = data.get('total_files', 1)
                                            percent = data.get('percent', 0)
                                            speed_mbps = data.get('speed_mbps', 0.0)
                                            eta_str = data.get('eta_str', 'Calculating...')
                                            
                                            print(f"[BATCH_UI_DEBUG] Progress update: {files_copied}/{file_count} ({percent:.1f}%) at {speed_mbps} MB/s")
                                            
                                            # Use total_size from the original batch data if available
                                            if captured_batch_data['total_size'] > 0:
                                                estimated_transferred = min(files_copied * (captured_batch_data['total_size'] // file_count), captured_batch_data['total_size']) if file_count > 0 else 0
                                                print(f"[BATCH_UI_DEBUG] Using total_size: {captured_batch_data['total_size']} for progress calculation")
                                            else:
                                                # Fallback: estimate based on files copied
                                                estimated_transferred = files_copied * 2000000  # Assume 2MB per file
                                                print(f"[BATCH_UI_DEBUG] Using total_size: 0 for progress calculation")
                                            
                                            print(f"[BATCH_UI_DEBUG] Updating progress bar - transferred: {estimated_transferred}, speed: {speed_mbps}, eta: {eta_str}")
                                            
                                            # CRITICAL FIX: Update progress with real-time info and actual percentage
                                            self.app.file_operations_progress.update_transfer_progress(
                                                captured_transfer_id, 
                                                estimated_transferred,
                                                speed_mbps,
                                                eta_str,
                                                'active',
                                                percent  # Pass the actual percentage from callback
                                            )
                                            
                                            # Log periodic progress (less frequent to avoid spam)
                                            if files_copied > 0 and files_copied % 50 == 0:  # Every 50 files
                                                self.app.status_manager.add_log_message(
                                                    f"📊 Batch progress: {files_copied}/{file_count} files ({percent:.1f}%) at {speed_mbps:.1f} MB/s", 
                                                    "DEBUG"
                                                )
                                        elif status == 'warning':
                                            # Handle warnings (like existing files or no files found)
                                            message = data.get('message', 'Warning')
                                            files_skipped = data.get('files_skipped', 0)
                                            
                                            print(f"[BATCH_UI_DEBUG] Warning: {message}")
                                            
                                            # For existing files, show as completed but with warning icon
                                            if files_skipped > 0:
                                                self.app.file_operations_progress.complete_transfer(
                                                    captured_transfer_id, True, f"⚠️ {files_skipped} files already exist"
                                                )
                                                self.app.status_manager.add_log_message(f"⚠️ EXISTING FILES: {message}", "WARNING")
                                            else:
                                                self.app.file_operations_progress.complete_transfer(
                                                    captured_transfer_id, True, f"⚠️ {message}"
                                                )
                                                self.app.status_manager.add_log_message(f"⚠️ BATCH WARNING: {message}", "WARNING")
                                        elif status == 'error':
                                            # Handle errors
                                            message = data.get('message', 'Error')
                                            print(f"[BATCH_UI_DEBUG] Error: {message}")
                                            self.app.file_operations_progress.complete_transfer(
                                                captured_transfer_id, False, f"❌ {message}"
                                            )
                                            self.app.status_manager.add_log_message(f"❌ BATCH ERROR: {message}", "ERROR")
                                    else:
                                        print(f"[BATCH_UI_DEBUG] No file_operations_progress found on app!")
                                except Exception as ui_error:
                                    print(f"[BATCH_UI_ERROR] Error updating batch progress UI: {ui_error}")
                                    import traceback
                                    traceback.print_exc()
                            
                            if hasattr(self.app, 'after'):
                                self.app.after(0, update_batch_ui)
                            else:
                                print(f"[BATCH_CALLBACK_DEBUG] App has no 'after' method!")
                        return batch_progress_callback
                    
                    # Execute sequence batch operation - use correct function based on operation type
                    if operation_type == "Copy":
                        success, message = copy_sequence_batch(
                            source_dir=batch_data['source_dir'],
                            destination_dir=batch_data['dest_dir'],
                            file_pattern=batch_data['pattern'],
                            status_callback=create_batch_progress_callback(batch_data, transfer_id),
                            transfer_id=transfer_id,
                            file_count=batch_data['file_count'],
                            total_size=batch_data['total_size']
                        )
                    else:  # Move operation
                        success, message = move_sequence_batch(
                            source_dir=batch_data['source_dir'],
                            destination_dir=batch_data['dest_dir'],
                            file_pattern=batch_data['pattern'],
                            status_callback=create_batch_progress_callback(batch_data, transfer_id),
                            transfer_id=transfer_id,
                            file_count=batch_data['file_count'],
                            total_size=batch_data['total_size']
                        )
                    
                    if not success:
                        def mark_batch_error():
                            if hasattr(self.app, 'file_operations_progress'):
                                self.app.file_operations_progress.complete_transfer(
                                    transfer_id, False, f"Batch failed: {message}"
                                )
                        self.app.after(0, mark_batch_error)
                
                # Process individual files with traditional threading
                if individual_files:
                    operation_func = copy_item if operation_type == "Copy" else move_item
                    
                    # Submit individual files for processing
                    future_to_file = {}
                    for file_data in individual_files:
                        if self.shutdown_requested:
                            break
                        
                        transfer_id = str(uuid.uuid4())
                        
                        # Add to progress tracking
                        if hasattr(self.app, 'file_operations_progress'):
                            self.app.file_operations_progress.add_transfer(
                                transfer_id, file_data['file_name'], file_data['operation'], file_data['total_size']
                            )
                        
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
            
            print(f"DEBUG: File {file_number}/{total_files}: {file_name}")
            print(f"DEBUG: Source path: {source_path}")
            print(f"DEBUG: Target file path: {destination_path}")
            
            # Custom status callback for progress panel integration
            def progress_callback(status_data):
                # Schedule UI updates on main thread to prevent freezing
                def update_ui():
                    try:
                        if hasattr(self.app, 'file_operations_progress'):
                            # Extract progress data from the status_data structure
                            data = status_data.get('data', {})
                            
                            # Check if this is a progress update with meaningful speed data
                            if 'speed_mbps' in data and 'transferred_bytes' in data:
                                transferred = data.get('transferred_bytes', 0)
                                total_size = data.get('total_bytes', 0)
                                speed_mbps = data.get('speed_mbps', 0.0)
                                eta_str = data.get('eta_str', 'Calculating...')
                                
                                # Only update if speed_mbps is present and meaningful
                                self.app.file_operations_progress.update_transfer_progress(
                                    transfer_id, transferred, speed_mbps, eta_str, 'active'
                                )
                            elif data.get('status') == 'success' and 'destination' in data:
                                # This is a completion callback - mark as completed without changing speed
                                # The complete_transfer method will be called separately
                                pass
                    except Exception as ui_error:
                        print(f"Error updating progress UI: {ui_error}")
                
                # Schedule on main thread
                if hasattr(self.app, 'after'):
                    self.app.after(0, update_ui)
                
                # Also send to status manager for logging (on background thread is OK)
                if hasattr(self.app, 'status_manager'):
                    self.app.status_manager.add_log_message(f"File operation progress: {status_data.get('data', {}).get('message', 'Progress update')}", "DEBUG")
            
            # Execute the file operation with progress callback
            success, message = operation_func(
                source_path=source_path,
                destination_path=destination_path,
                status_callback=progress_callback,
                transfer_id=transfer_id
            )
            
            if success:
                # Mark as completed successfully
                def mark_success():
                    try:
                        if hasattr(self.app, 'file_operations_progress'):
                            self.app.file_operations_progress.complete_transfer(
                                transfer_id, True, "Completed successfully"
                            )
                        
                        self.app.status_manager.add_log_message(
                            f"file_operation_success: Successfully {operation_name.lower()}ed {file_name} to {destination_path}",
                            "DEBUG"
                        )
                    except Exception as success_error:
                        print(f"Error marking success: {success_error}")
                
                self.app.after(0, mark_success)
                return (success, message)
            else:
                # Mark as failed
                def mark_failed():
                    try:
                        if hasattr(self.app, 'file_operations_progress'):
                            self.app.file_operations_progress.complete_transfer(
                                transfer_id, False, message
                            )
                        
                        self.app.status_manager.add_log_message(
                            f"file_operation_error: Failed to {operation_name.lower()} {file_name}: {message}",
                            "ERROR"
                        )
                    except Exception as failed_error:
                        print(f"Error marking failure: {failed_error}")
                
                self.app.after(0, mark_failed)
                raise Exception(message)
                
        except Exception as worker_exception:
            # Handle any exceptions - capture the exception in the outer scope
            error_message = str(worker_exception)
            
            def handle_error():
                try:
                    if hasattr(self.app, 'file_operations_progress'):
                        self.app.file_operations_progress.complete_transfer(
                            transfer_id, False, error_message
                        )
                    
                    self.app.status_manager.add_log_message(
                        f"file_operation_exception: Error in {operation_name.lower()} operation for {file_name}: {error_message}",
                        "ERROR"
                    )
                except Exception as handler_error:
                    print(f"Error in error handler: {handler_error}")
            
            self.app.after(0, handle_error)
            raise

    def shutdown(self):
        """Shutdown the file operations manager and clean up resources."""
        self.shutdown_requested = True
        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)

    def handle_transfer_state_change(self, transfer_id: str, new_status: str):
        """Handle state changes from the progress panel (pause/resume)."""
        try:
            # Store the state change in active transfers
            if transfer_id in self.active_transfers:
                self.active_transfers[transfer_id]['status'] = new_status
                self.app.status_manager.add_log_message(
                    f"Transfer {transfer_id} state changed to: {new_status}", "DEBUG"
                )
                
                # Note: Actual pause/resume implementation would need to be added
                # to the underlying file operation functions (copy_item, move_item)
                # For now, this just tracks the state
                
        except Exception as e:
            self.app.status_manager.add_log_message(
                f"Error handling transfer state change: {str(e)}", "ERROR"
            )

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