"""
Scan Manager Module - PyQt5 Compatible

Handles scanning operations and queue management functionality
for the Clean Incomings GUI application.
"""

import os
import threading
import traceback
from PyQt5.QtCore import QTimer
from queue import Queue, Empty
from typing import Dict, Any, Optional


class ScanManager:
    """Manages scanning operations and queue processing for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the ScanManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.result_queue = None
        self.scan_thread = None

    def on_scan_button_click(self):
        """Handle scan button click."""
        source_path = self.app.selected_source_folder.get()
        profile_name = self.app.selected_profile_name.get()
        destination_root = self.app.selected_destination_folder.get()

        if not source_path:
            self.app.status_label.setText("Please select a source folder.")
            return
        if not profile_name:
            self.app.status_label.setText("Please select a profile.")
            return
        if not destination_root:
            self.app.status_label.setText("Please select a destination root folder.")
            return
        
        if not self.app.normalizer:
            self.app.status_label.setText("Error: Normalizer not available. Check logs.")
            return

        # Start the scan progress system
        self.app.status_manager.start_scan_progress()

        # Disable the refresh button during scan (PyQt5)
        self.app.refresh_btn.setEnabled(False)
        
        # Initialize result queue for thread communication
        self.result_queue = Queue()
        
        # Start scanning in a separate thread
        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(source_path, profile_name, destination_root),
            daemon=True
        )
        self.scan_thread.start()
        
        # Start checking for results using QTimer
        self._check_scan_queue()

    def refresh_scan_data(self):
        """Refresh/rescan the data - alias for on_scan_button_click."""
        self.on_scan_button_click()

    def _scan_worker(self, source_path: str, profile_name: str, destination_root: str):
        """
        Worker method that runs in a separate thread to perform scanning.
        
        Args:
            source_path: Source directory path
            profile_name: Profile name for normalization
            destination_root: Root destination directory
        """
        try:
            print(f"[SCAN_WORKER] Starting scan: {source_path} -> {destination_root} (Profile: {profile_name})")
            
            # Update status on main thread
            QTimer.singleShot(0, lambda: self.app.status_label.setText("Starting scan..."))
            
            # Run the scan/normalization process
            result_data_dict = self.app.normalizer.scan_and_build_proposals(
                source_root=source_path,
                destination_root=destination_root,
                profile_name=profile_name,
                status_callback=self.update_scan_status
            )
            
            # Get original tree data from adapter
            original_tree_data = self.app.normalizer.get_last_scan_tree_data()
            result_data_dict['tree_data'] = original_tree_data
            
            # Put successful result in queue
            self.result_queue.put({
                "type": "final_success",
                "data": result_data_dict
            })
            
        except Exception as e:
            print(f"[SCAN_WORKER] Exception during scan: {e}")
            import traceback
            traceback.print_exc()
            
            error_message = f"Scan failed: {str(e)}"
            # Put error result in queue
            self.result_queue.put({
                "type": "final_error",
                "data": error_message
            })

    def _check_scan_queue(self):
        """Checks the result_queue for final results from the scan worker thread."""
        try:
            result = self.result_queue.get_nowait()  # Non-blocking get from the final result queue

            # Re-enable refresh button
            self.app.refresh_btn.setEnabled(True)

            if isinstance(result, dict) and result.get("type") == "final_error":
                error_data = result.get('data', 'Unknown error during scan.')
                self.app.status_label.setText(f"Scan Failed: {error_data}")
                print(f"Scan failed (from worker): {error_data}")
                
                # Finish progress with error
                self.app.status_manager.finish_scan_progress(False, error_data)
                
            elif isinstance(result, dict) and result.get("type") == "final_success":
                result_data_dict = result.get('data', {})
                source_path = self.app.selected_source_folder.get()

                original_tree_data = result_data_dict.get('original_scan_tree')
                normalized_proposals_list = result_data_dict.get('proposals', [])

                if original_tree_data and isinstance(original_tree_data, dict):
                    # Populate source tree with children data
                    self.app.tree_manager.populate_source_tree(original_tree_data.get('children', []), source_path)
                else:
                    self.app.tree_manager.populate_source_tree([], source_path)  # Pass empty list if no tree data
                
                # Populate preview tree
                if hasattr(self.app, 'preview_tree'):
                    self.app.tree_manager.populate_preview_tree(normalized_proposals_list, source_path)

                num_proposals = len(normalized_proposals_list)
                base_name = os.path.basename(source_path) if source_path else "selected folder"
                self.app.status_label.setText(f"Scan Complete. Generated {num_proposals} proposals from {base_name}.")
                print(f"Scan complete (from worker). Generated proposals: {num_proposals}")
                
                # Finish progress successfully
                self.app.status_manager.finish_scan_progress(True)
                
            else:
                # This case should ideally not happen if _scan_worker only puts final_error/final_success
                print(f"Unexpected item in result_queue: {result}")
                self.app.status_label.setText("Scan finished with unexpected result.")
                self.app.status_manager.finish_scan_progress(False, "Unexpected result")

        except Empty:  # queue.Empty - no final result yet, keep checking
            # Continue checking with QTimer
            QTimer.singleShot(100, self._check_scan_queue)
        except Exception as e:  # Catch any other unexpected errors during UI update
            self.app.refresh_btn.setEnabled(True)  # Re-enable refresh button on error
            error_msg = f"Error processing scan result: {e}"
            self.app.status_label.setText(error_msg)
            print(error_msg)
            self.app.status_manager.finish_scan_progress(False, error_msg)

    def update_scan_status(self, current_path: str):
        """Callback to update status label during scan. Thread-safe."""
        max_len = 70
        display_path = current_path
        if len(current_path) > max_len:
            display_path = "..." + current_path[-(max_len-3):]
        # Schedule the UI update on the main thread using QTimer
        QTimer.singleShot(0, lambda path=display_path: self.app.status_label.setText(f"Scanning: {path}"))
