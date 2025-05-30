"""
Status Manager Module

Handles status updates, progress reporting, and logging functionality
for the Clean Incomings GUI application.
"""

import datetime
import threading
import tkinter as tk
from typing import Dict, Any, Optional
import re
import time  # Add time for rate limiting


class StatusManager:
    """Manages status updates, progress reporting, and logging for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the StatusManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.current_transfer_info = {
            'file_name': '',
            'speed_mbps': 0.0,
            'eta_str': 'Calculating...',
            'percent': 0.0,
            'status': 'idle'
        }
        self.scan_in_progress = False
        
        # Rate limiting for UI updates
        self.last_ui_update = 0
        self.min_ui_update_interval = 0.1  # Minimum 100ms between UI updates
        self.pending_ui_update = False

    def _get_stage_status_enum(self):
        """Get the StageStatus enum - import it directly."""
        try:
            from .progress_panel import StageStatus
            return StageStatus
        except ImportError:
            # Create a basic enum-like class as fallback
            class StageStatus:
                PENDING = "pending"
                IN_PROGRESS = "in_progress"
                COMPLETED = "completed"
                ERROR = "error"
            return StageStatus

    def _can_update_ui(self) -> bool:
        """Check if we can update the UI based on rate limiting."""
        current_time = time.time()
        if current_time - self.last_ui_update < self.min_ui_update_interval:
            if not self.pending_ui_update:
                # Schedule a delayed update
                self.pending_ui_update = True
                self.app.after(int(self.min_ui_update_interval * 1000), self._delayed_ui_update)
            return False
        return True

    def _delayed_ui_update(self):
        """Handle delayed UI updates for rate limiting."""
        self.pending_ui_update = False
        # This will be called if we need to update the UI after rate limiting

    def set_status_message(self, message: str, progress: Optional[float] = None):
        """Set status message and optional progress."""
        if not self._can_update_ui():
            return
        
        try:
            self.last_ui_update = time.time()
            self.app.status_label.configure(text=message)
            if progress is not None and hasattr(self.app, 'progress_bar'):
                progress = max(0.0, min(1.0, progress))
                self.app.progress_bar.set(progress)
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error setting status: {e}")

    def add_log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log textbox."""
        if not hasattr(self.app, 'log_textbox'):
            return
            
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {level}: {message}\n"
            
            self.app.log_textbox.configure(state='normal')
            self.app.log_textbox.insert('end', formatted_message)
            self.app.log_textbox.see('end')  # Auto-scroll to bottom
            self.app.log_textbox.configure(state='disabled')
        except Exception as e:
            print(f"Error adding log message: {e}")

    def start_scan_progress(self):
        """Start scan progress mode with multi-stage popup panel."""
        try:
            self.scan_in_progress = True
            
            # Show and reset progress panel popup
            if hasattr(self.app, 'progress_panel'):
                self.app.progress_panel.reset()
                self.app.progress_panel.show()
            
            self.add_log_message("Scan progress tracking started", "INFO")
        except Exception as e:
            self.add_log_message(f"Error starting scan progress: {e}", "ERROR")
            print(f"Scan progress start error: {e}")

    def complete_validation_stage(self):
        """Complete the validation stage in the progress panel."""
        try:
            if hasattr(self.app, 'progress_panel'):
                # Complete initialization stage
                self.app.progress_panel.complete_stage('initialization', 'Validation completed')
                # Start collection stage
                self.app.progress_panel.start_stage('collection', 'Starting file collection...')
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error completing validation stage: {e}")

    def finish_scan_progress(self, success: bool, message: str = ""):
        """Finish scan progress with success or failure status."""
        try:
            self.scan_in_progress = False
            
            if hasattr(self.app, 'progress_panel'):
                current_stage = self.app.progress_panel.get_current_stage()
                StageStatus = self._get_stage_status_enum()
                
                if success:
                    # Complete any remaining stages
                    for stage_info in self.app.progress_panel.stages:
                        stage_id = stage_info['id']
                        if self.app.progress_panel.stage_status[stage_id] not in [
                            StageStatus.COMPLETED,
                            StageStatus.ERROR
                        ]:
                            self.app.progress_panel.complete_stage(stage_id, "Completed")
                else:
                    # Mark current stage as error
                    if current_stage:
                        self.app.progress_panel.error_stage(current_stage, message or "Operation failed")
                    
                # Hide progress panel after a delay
                self.app.after(3000, self._hide_progress_panel)
            
            log_message = f"Scan {'completed successfully' if success else 'failed'}"
            if message:
                log_message += f": {message}"
            self.add_log_message(log_message, "INFO" if success else "ERROR")
            
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error finishing scan progress: {e}")

    def complete_scan_progress(self):
        """Complete scan progress and clean up UI."""
        def update_completion():
            try:
                self.scan_in_progress = False
                
                # Complete any remaining stages
                if hasattr(self.app, 'progress_panel'):
                    if not self.app.progress_panel.is_complete():
                        # Complete the current stage if not already completed
                        current_stage = self.app.progress_panel.get_current_stage()
                        StageStatus = self._get_stage_status_enum()
                        if current_stage and self.app.progress_panel.stage_status.get(current_stage) != StageStatus.COMPLETED:
                            self.app.progress_panel.complete_stage(current_stage, "Completed")
                    
                    # Hide progress panel after a delay
                    self.app.after(3000, self._hide_progress_panel)
                
                self.add_log_message("Scan completed successfully", "INFO")
            except Exception as e:
                self.add_log_message(f"Error updating completion UI: {e}", "ERROR")
                print(f"Completion update error: {e}")
        
        self.app.after(0, update_completion)

    def _hide_progress_panel(self):
        """Hide the progress panel popup."""
        try:
            if hasattr(self.app, 'progress_panel'):
                self.app.progress_panel.hide()
        except Exception as e:
            print(f"Error hiding progress panel: {e}")

    def process_adapter_status(self, status_info: dict):
        """Processes status updates in the main GUI thread."""
        status_type = status_info.get("type")
        data = status_info.get("data", {})

        # Handle multi-stage progress if scan is in progress
        if self.scan_in_progress:
            self._process_multi_stage_progress(status_type, data)
        else:
            # Handle regular single progress bar for file operations
            self._process_legacy_progress(status_type, data)

    def _process_multi_stage_progress(self, status_type: str, data: dict):
        """Process status updates for the multi-stage progress panel."""
        if status_type == "scan":
            self._process_scan_stage_progress(data)
        elif status_type == "mapping_generation":
            self._process_mapping_stage_progress(data)
        elif status_type == "transformation":
            self._process_transformation_stage_progress(data)
        else:
            self.add_log_message(f"Unhandled multi-stage status type: {status_type}", "WARNING")

    def _process_scan_stage_progress(self, data: dict):
        """Process scan stage progress for the multi-stage panel."""
        if not self._can_update_ui():
            return
            
        try:
            self.last_ui_update = time.time()
            progress_percentage = data.get("progressPercentage", 0)
            status_message = data.get("status", "scanning")
            total_files_scanned = data.get("totalFilesScanned", 0)
            total_folders_scanned = data.get("totalFoldersScanned", 0)
            estimated_total = data.get("estimatedTotalFiles", 0)
            current_file_path = data.get("currentFile")
            current_folder_path = data.get("currentFolder")

            # Ensure we're in the scanning stage
            if self.app.progress_panel.get_current_stage() != 'collection':
                self.app.progress_panel.start_stage('collection', 'Scanning files and folders...')

            # Update scanning stage progress
            progress_value = progress_percentage / 100.0
            
            # Create detailed progress message
            count_info = f"{total_files_scanned} files"
            if total_folders_scanned > 0:
                count_info += f", {total_folders_scanned} folders"
            
            if estimated_total > 0:
                count_info += f" of ~{estimated_total}"

            # Include current item being processed
            detail_parts = [count_info]
            if current_folder_path:
                import os
                detail_parts.append(f"Folder: {os.path.basename(current_folder_path)}")
            elif current_file_path:
                import os
                detail_parts.append(f"File: {os.path.basename(current_file_path)}")

            details = " • ".join(detail_parts)

            if status_message == "completed":
                self.app.progress_panel.complete_stage('collection', f"Scan complete: {count_info}")
                self.app.progress_panel.start_stage('mapping', 'Starting mapping generation...')
            elif status_message == "failed":
                error_detail = data.get('result', {}).get('error', 'Unknown scan error')
                self.app.progress_panel.error_stage('collection', f"Scan failed: {error_detail}")
            else:
                self.app.progress_panel.update_stage_progress('collection', progress_value, details)
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error in scan stage progress: {e}")

    def _process_mapping_stage_progress(self, data: dict):
        """Process mapping generation stage progress with rate limiting."""
        mg_status = data.get("status", "processing")
        mg_message = data.get("message", "Generating mappings...")
        current_files = data.get("current_file_count", 0)
        total_files = data.get("total_files", 0)
        progress_percentage_val = data.get("progress_percentage", None)

        # Ensure we're in the mapping stage
        if self.app.progress_panel.get_current_stage() != 'mapping':
            self.app.progress_panel.start_stage('mapping', mg_message)

        # Only filter out initial setup messages without any meaningful content
        is_initial_setup_message = (
            current_files == 0 and 
            total_files == 0 and 
            progress_percentage_val is None and
            mg_status not in ["completed", "warning", "finished", "error"] and
            ("Collecting files" in mg_message or 
             "Starting collection" in mg_message or
             "Initiating mapping" in mg_message or
             "Starting mapping generation" in mg_message)
        )
        
        if is_initial_setup_message:
            # Just update the message without changing progress bar
            try:
                self.app.progress_panel.stage_details['mapping'] = mg_message
                # Update the details display without changing progress
                widgets = self.app.progress_panel.stage_widgets.get('mapping')
                if widgets and 'details' in widgets:
                    display_details = mg_message[:50] + "..." if len(mg_message) > 50 else mg_message
                    widgets['details'].configure(text=display_details)
            except Exception as e:
                print(f"[STATUS_MANAGER_ERROR] Error updating setup message: {e}")
            return

        # Rate limit progress updates for mapping stage
        if not self._can_update_ui():
            return
        
        try:
            self.last_ui_update = time.time()
            
            # Calculate progress using raw data
            progress_value = 0.0
            if progress_percentage_val is not None:
                progress_value = progress_percentage_val / 100.0
                progress_percentage = progress_value * 100
                details = f"{mg_message} ({progress_percentage:.1f}%)"
            elif total_files > 0 and current_files > 0:
                progress_value = min(0.95, current_files / total_files)  # Cap at 95% until complete
                progress_percentage = progress_value * 100
                details = f"{mg_message} ({progress_percentage:.1f}%)"
            elif current_files > 0:
                # Even without total, show some progress if files are being processed
                progress_value = min(0.5, current_files / 100.0)  # Assume 100 files as rough estimate
                details = f"{mg_message} ({current_files} files processed)"
            else:
                details = mg_message

            if mg_status in ["completed", "warning", "finished"]:
                self.app.progress_panel.complete_stage('mapping', 'Mapping generation complete')
                self.app.progress_panel.start_stage('processing', 'Processing results...')
            elif mg_status == "error":
                self.app.progress_panel.error_stage('mapping', f"Mapping error: {mg_message}")
            else:
                self.app.progress_panel.update_stage_progress('mapping', progress_value, details)
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error in mapping stage progress: {e}")

    def _process_transformation_stage_progress(self, data: dict):
        """Process transformation stage progress."""
        if not self._can_update_ui():
            return
            
        try:
            self.last_ui_update = time.time()
            status = data.get("status", "processing")
            message = data.get("message", "Processing...")

            # Ensure we're in the processing stage
            if self.app.progress_panel.get_current_stage() != 'processing':
                self.app.progress_panel.start_stage('processing', message)

            if status == "completed":
                self.app.progress_panel.complete_stage('processing', 'Results processed successfully')
            elif status == "error":
                self.app.progress_panel.error_stage('processing', f"Processing error: {message}")
            else:
                # For transformation, we don't have detailed progress, so just show as in progress
                self.app.progress_panel.update_stage_progress('processing', 0.5, message)
        except Exception as e:
            print(f"[STATUS_MANAGER_ERROR] Error in transformation stage progress: {e}")

    def _process_legacy_progress(self, status_type: str, data: dict):
        """Process status updates for the legacy single progress bar."""
        # Ensure progress bar is visible and reset color before processing
        try:
            if hasattr(self.app, 'progress_bar'):
                self.app.progress_bar.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
            
            import customtkinter as ctk
            default_text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            if isinstance(default_text_color, tuple): # (light_mode_color, dark_mode_color)
                 current_mode = ctk.get_appearance_mode()
                 default_text_color = default_text_color[0] if current_mode == "Light" else default_text_color[1]
            self.app.status_label.configure(text_color=default_text_color)
        except Exception:
             self.app.status_label.configure(text_color="black") # Fallback

        if status_type == "scan":
            self._process_scan_status(data)
        elif status_type == "mapping_generation":
            self._process_mapping_generation_status(data)
        else:
            self.add_log_message(f"Received unhandled status type: {status_type} with data: {data}", "WARNING")
            self.app.status_label.configure(text=f"Status: {status_type} - {data.get('message', 'No message')}")

    def _process_scan_status(self, data: dict):
        """Process scan-specific status updates."""
        import os
        
        progress_percentage = data.get("progressPercentage", 0)
        status_message = data.get("status", "scanning")
        eta_seconds = data.get("etaSeconds")
        total_files_scanned = data.get("totalFilesScanned", 0)
        total_folders_scanned = data.get("totalFoldersScanned", 0)
        estimated_total = data.get("estimatedTotalFiles", 0)
        current_file_path = data.get("currentFile")
        current_folder_path = data.get("currentFolder")

        current_progress_float = progress_percentage / 100.0

        if status_message == "completed":
            if self.app.progress_bar.cget('mode') == 'indeterminate':
                self.app.progress_bar.stop()
            self.app.progress_bar.configure(mode='determinate')
            self.app.progress_bar.set(1.0)
        elif status_message == "failed":
            if self.app.progress_bar.cget('mode') == 'indeterminate':
                self.app.progress_bar.stop()
            self.app.progress_bar.configure(mode='determinate')
            self.app.progress_bar.set(max(0.0, min(1.0, current_progress_float)))
            self.app.status_label.configure(text_color="red")
        elif status_message == "running" and total_files_scanned == 0 and estimated_total > 0 and progress_percentage == 0:
            if self.app.progress_bar.cget('mode') != 'indeterminate':
                self.app.progress_bar.configure(mode='indeterminate')
                self.app.progress_bar.start()
        else: # 'running' with files scanned, or other states
            if self.app.progress_bar.cget('mode') == 'indeterminate':
                self.app.progress_bar.stop()
            self.app.progress_bar.configure(mode='determinate')
            display_value = current_progress_float
            if 0 < current_progress_float < 0.05 and total_files_scanned > 0:
                display_value = 0.05
            elif current_progress_float == 0 and total_files_scanned > 0 and estimated_total > 0:
                 display_value = 0.01
            self.app.progress_bar.set(max(0.0, min(1.0, display_value)))

        details = []
        if current_folder_path and status_message == "running":
            details.append(f"Folder: {os.path.basename(current_folder_path)}")
        if current_file_path and status_message == "running":
            details.append(f"File: {os.path.basename(current_file_path)}")
        
        count_info = f"{total_files_scanned} files"
        if total_folders_scanned > 0:
            count_info += f", {total_folders_scanned} folders"
        
        estimated_total_info = ""
        if estimated_total > 0 and status_message == "running":
             estimated_total_info = f" of ~{estimated_total}"
        
        eta_text = ""
        if eta_seconds is not None and eta_seconds > 0 and status_message == "running":
            if eta_seconds < 60:
                eta_text = f" - ETA: {int(eta_seconds)}s"
            elif eta_seconds < 3600:
                minutes = int(eta_seconds // 60)
                seconds = int(eta_seconds % 60)
                eta_text = f" - ETA: {minutes}m {seconds}s"
            else:
                hours = int(eta_seconds // 3600)
                minutes = int((eta_seconds % 3600) // 60)
                eta_text = f" - ETA: {hours}h {minutes}m"
        
        detail_str = f" - {' | '.join(details)}" if details else ""
        display_status_message = status_message.capitalize() if status_message else "Scanning"
        
        if status_message == "completed":
             status_text = f"Scan Completed: {count_info} processed."
        elif status_message == "failed":
             error_detail = data.get('result', {}).get('error', 'An unknown error occurred.')
             status_text = f"Scan Failed: {error_detail}"
             self.app.status_label.configure(text_color="red")
        else:
             status_text = f"{display_status_message}: {count_info}{estimated_total_info} ({progress_percentage:.1f}%){eta_text}{detail_str}"
        
        self.app.status_label.configure(text=status_text)

    def _process_mapping_generation_status(self, data: dict):
        """Process mapping generation status updates."""
        mg_status = data.get("status", "processing")
        mg_message = data.get("message", "...")
        current_files = data.get("current_file_count", 0)
        total_files = data.get("total_files", 0)
        progress_percentage_val = data.get("progress_percentage", None)

        progress_text = mg_message
        current_progress_value = 0.0

        if progress_percentage_val is not None:
            current_progress_value = float(progress_percentage_val) / 100.0
            progress_text = f"{mg_message} ({progress_percentage_val:.1f}%)"
        elif total_files > 0:
            current_progress_value = float(current_files) / float(total_files)
            progress_text = f"{mg_message} ({current_files}/{total_files} - {current_progress_value*100:.1f}%)"
        elif mg_status == "starting" or mg_status == "collecting_files":
            if self.app.progress_bar.cget('mode') != 'indeterminate':
                self.app.progress_bar.configure(mode='indeterminate')
                self.app.progress_bar.start()
            progress_text = f"{mg_message} (Initializing...)"
        
        if not (mg_status == "starting" or mg_status == "collecting_files") or total_files > 0 or progress_percentage_val is not None:
             if self.app.progress_bar.cget('mode') == 'indeterminate':
                self.app.progress_bar.stop()
             self.app.progress_bar.configure(mode='determinate')
             self.app.progress_bar.set(max(0.0, min(1.0, current_progress_value)))

        if mg_status == "completed" or mg_status == "warning" or mg_status == "finished":
            if self.app.progress_bar.cget('mode') == 'indeterminate': 
                self.app.progress_bar.stop()
            self.app.progress_bar.configure(mode='determinate')
            self.app.progress_bar.set(1.0)
        elif mg_status == "error":
            if self.app.progress_bar.cget('mode') == 'indeterminate': 
                self.app.progress_bar.stop()
            self.app.progress_bar.configure(mode='determinate')
            self.app.status_label.configure(text_color="red")

        self.app.status_label.configure(text=f"Mapping: {progress_text}")
        if mg_status == "error":
            self.app.status_label.configure(text_color="red") 