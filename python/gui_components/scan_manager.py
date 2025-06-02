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
        Implements robust, multi-stage progress reporting via result_queue for ProgressPanel.
        Args:
            source_path: Source directory path
            profile_name: Profile name for normalization
            destination_root: Root destination directory
        """
        import time
        try:
            # print(f"[SCAN_WORKER] Starting scan: {source_path} -> {destination_root} (Profile: {profile_name})")

            # --- Stage 1: Initialization ---
            self.result_queue.put({
                'type': 'progress',
                'stage': 'initialization',
                'status': 'in_progress',
                'percent': 0.0,
                'details': 'Initializing scan...'
            })
            time.sleep(0.1)
            self.result_queue.put({
                'type': 'progress',
                'stage': 'initialization',
                'status': 'completed',
                'percent': 1.0,
                'details': 'Initialization complete.'
            })

            # --- Stage 2: File Collection ---
            self.result_queue.put({
                'type': 'progress',
                'stage': 'collection',
                'status': 'in_progress',
                'percent': 0.0,
                'details': 'Collecting files...'
            })
            # Simulate file collection (replace with actual logic)
            files = []
            for root, dirs, filenames in os.walk(source_path):
                for f in filenames:
                    files.append(os.path.join(root, f))
            total_files = len(files)
            for i, f in enumerate(files):
                if i % max(1, total_files // 50) == 0 or i == total_files - 1:
                    self.result_queue.put({
                        'type': 'progress',
                        'stage': 'collection',
                        'status': 'in_progress',
                        'percent': (i+1)/total_files if total_files else 1.0,
                        'details': f'Collected {i+1} of {total_files} files'
                    })
            self.result_queue.put({
                'type': 'progress',
                'stage': 'collection',
                'status': 'completed',
                'percent': 1.0,
                'details': f'File collection complete. {total_files} files found.'
            })

            # --- Stage 3: Sequence Detection ---
            self.result_queue.put({
                'type': 'progress',
                'stage': 'sequencing',
                'status': 'in_progress',
                'percent': 0.0,
                'details': 'Detecting sequences...'
            })
            # Simulate sequence detection (replace with actual logic)
            num_sequences = max(1, total_files // 10)
            for i in range(num_sequences):
                if i % max(1, num_sequences // 20) == 0 or i == num_sequences - 1:
                    self.result_queue.put({
                        'type': 'progress',
                        'stage': 'sequencing',
                        'status': 'in_progress',
                        'percent': (i+1)/num_sequences,
                        'details': f'Detected {i+1} of {num_sequences} sequences'
                    })
            self.result_queue.put({
                'type': 'progress',
                'stage': 'sequencing',
                'status': 'completed',
                'percent': 1.0,
                'details': f'Sequence detection complete. {num_sequences} sequences.'
            })

            # --- Stage 4: Path Mapping ---
            self.result_queue.put({
                'type': 'progress',
                'stage': 'mapping',
                'status': 'in_progress',
                'percent': 0.0,
                'details': 'Mapping paths...'
            })
            # Simulate mapping (replace with actual logic)
            for i in range(num_sequences):
                if i % max(1, num_sequences // 20) == 0 or i == num_sequences - 1:
                    self.result_queue.put({
                        'type': 'progress',
                        'stage': 'mapping',
                        'status': 'in_progress',
                        'percent': (i+1)/num_sequences,
                        'details': f'Mapped {i+1} of {num_sequences} sequences'
                    })
            self.result_queue.put({
                'type': 'progress',
                'stage': 'mapping',
                'status': 'completed',
                'percent': 1.0,
                'details': f'Path mapping complete.'
            })

            # --- Stage 5: Final Processing ---
            self.result_queue.put({
                'type': 'progress',
                'stage': 'processing',
                'status': 'in_progress',
                'percent': 0.0,
                'details': 'Finalizing...'
            })
            time.sleep(0.1)
            self.result_queue.put({
                'type': 'progress',
                'stage': 'processing',
                'status': 'completed',
                'percent': 1.0,
                'details': 'Processing complete.'
            })

            # --- Call the real scan/normalization logic (replace below with actual logic) ---
            # QTimer.singleShot(0, lambda: self.app.status_label.setText("Starting scan..."))
            result_data_dict = self.app.normalizer.scan_and_normalize_structure(
                base_path=source_path,
                profile_name=profile_name,
                destination_root=destination_root,
                status_callback=self.update_scan_status
            )
            self.result_queue.put({
                "type": "final_success",
                "data": result_data_dict
            })
            
        except Exception as e:
            print(f"[SCAN_WORKER] Exception during scan: {e}")  # Error reporting
            import traceback
            traceback.print_exc()  # Error reporting
            
            error_message = f"Scan failed: {str(e)}"
            # Put error result in queue
            self.result_queue.put({
                "type": "final_error",
                "data": error_message
            })

    def _check_scan_queue(self):
        """Checks the result_queue for progress and final results from the scan worker thread."""
        try:
            result = self.result_queue.get_nowait()  # Non-blocking get from the final result queue

            # Re-enable refresh button only on final result
            if isinstance(result, dict) and result.get("type") in ("final_error", "final_success"):
                self.app.refresh_btn.setEnabled(True)

            # Handle progress updates for the floating ProgressWindowPyQt5
            if isinstance(result, dict) and result.get('type') == 'progress':
                stage = result['stage']
                status = result['status']
                percent = result.get('percent', 0)
                details = result.get('details', '')
                if hasattr(self.app, 'progress_window'):
                    if status == 'in_progress':
                        self.app.progress_window.show_progress(stage, int(percent * 100), details)
                    elif status == 'completed':
                        self.app.progress_window.show_progress(stage + " completed", 100, details)
                        self.app.progress_window.close_progress()
                    elif status == 'error':
                        self.app.progress_window.error(details)
                QTimer.singleShot(50, self._check_scan_queue)
                return


            if isinstance(result, dict) and result.get("type") == "final_error":
                error_data = result.get('data', 'Unknown error during scan.')
                self.app.status_label.setText(f"Scan Failed: {error_data}")
                print(f"Scan failed (from worker): {error_data}")
                # Finish progress with error
                self.app.status_manager.finish_scan_progress(False, error_data)
                if hasattr(self.app, 'progress_panel'):
                    self.app.progress_panel.hide_panel()

            elif isinstance(result, dict) and result.get("type") == "final_success":
                result_data_dict = result.get('data', {})
                source_path = self.app.selected_source_folder.get()

                original_tree_data = result_data_dict.get('original_scan_tree')
                normalized_proposals_list = result_data_dict.get('proposals', [])

                # ---- START DEBUG ----
                # print(f"[SCAN_DEBUG] Type of self.app.tree_manager: {type(self.app.tree_manager)}")  # (Silenced for normal use. Re-enable for troubleshooting.)
                # print(f"[SCAN_DEBUG] hasattr populate_source_tree: {hasattr(self.app.tree_manager, 'populate_source_tree')}")  # (Silenced for normal use. Re-enable for troubleshooting.)
                # print(f"[SCAN_DEBUG] dir(self.app.tree_manager): {dir(self.app.tree_manager)}")  # (Silenced for normal use. Re-enable for troubleshooting.)
                # ---- END DEBUG ----

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
                if hasattr(self.app, 'progress_panel'):
                    self.app.progress_panel.hide_panel()

            else:
                # This case should ideally not happen if _scan_worker only puts final_error/final_success
                print(f"Unexpected item in result_queue: {result}")
                self.app.status_label.setText("Scan finished with unexpected result.")
                self.app.status_manager.finish_scan_progress(False, "Unexpected result")
                if hasattr(self.app, 'progress_panel'):
                    self.app.progress_panel.hide_panel()

        except Empty:  # queue.Empty - no final result yet, keep checking
            # Continue checking with QTimer
            QTimer.singleShot(100, self._check_scan_queue)
        except Exception as e:  # Catch any other unexpected errors during UI update
            self.app.refresh_btn.setEnabled(True)  # Re-enable refresh button on error
            error_msg = f"Error processing scan result: {e}"
            self.app.status_label.setText(error_msg)
            print(error_msg)
            self.app.status_manager.finish_scan_progress(False, error_msg)
            if hasattr(self.app, 'progress_panel'):
                self.app.progress_panel.hide_panel()

    def update_scan_status(self, current_path: str):
        """Callback to update status label during scan. Thread-safe."""
        max_len = 70
        display_path = current_path
        if len(current_path) > max_len:
            display_path = "..." + current_path[-(max_len-3):]
        # Schedule the UI update on the main thread using QTimer
        QTimer.singleShot(0, lambda path=display_path: self.app.status_label.setText(f"Scanning: {path}"))
