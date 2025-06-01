"""
Scan Manager Module

Handles scanning operations and queue management functionality
for the Clean Incomings GUI application.
"""

import os
import threading
import traceback
import tkinter as tk
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
            self.app.status_label.configure(text="Please select a source folder.")
            return
        if not profile_name:
            self.app.status_label.configure(text="Please select a profile.")
            return
        if not destination_root:
            self.app.status_label.configure(text="Please select a destination root folder.")
            return
        
        if not self.app.normalizer:
            self.app.status_label.configure(text="Error: Normalizer not available. Check logs.")
            return

        # Start the new multi-stage progress system
        self.app.status_manager.start_scan_progress()
        
        # Quick validation before starting scan
        if self._validate_scan_inputs(source_path, profile_name, destination_root):
            self.app.status_manager.complete_validation_stage()
        else:
            self.app.status_manager.finish_scan_progress(False, "Validation failed")
            return

        # Clear previous preview results
        if hasattr(self.app, 'preview_tree'):
            for i in self.app.preview_tree.get_children():
                self.app.preview_tree.delete(i)

        self.result_queue = Queue()
        thread_args = (source_path, profile_name, destination_root)
        self.scan_thread = threading.Thread(target=self._scan_worker, args=thread_args, daemon=True)
        self.scan_thread.start()
        self.app.after(100, self._check_scan_queue)  # Start checking the queue

    def refresh_scan_data(self):
        """Refresh/rescan the data."""
        print("--- _refresh_scan_data ENTERED ---", flush=True)
        print(f"DEBUG: _refresh_scan_data: self.normalizer is {'VALID' if self.app.normalizer else 'NONE'}", flush=True)
        
        source_path = self.app.selected_source_folder.get()
        profile_name = self.app.selected_profile_name.get()
        destination_root = self.app.selected_destination_folder.get()

        # Start the new multi-stage progress system
        self.app.status_manager.start_scan_progress()

        # Validation stage
        if not self._validate_scan_inputs(source_path, profile_name, destination_root):
            self.app.status_manager.finish_scan_progress(False, "Validation failed")
            return

        self.app.status_manager.complete_validation_stage()

        # Clear previous data from treeviews
        if hasattr(self.app, 'source_tree'):
            for i in self.app.source_tree.get_children():
                self.app.source_tree.delete(i)
        if hasattr(self.app, 'preview_tree'): 
            for i in self.app.preview_tree.get_children():
                self.app.preview_tree.delete(i)

        self.app.refresh_btn.configure(state=tk.DISABLED)  # Disable button during scan

        self.result_queue = Queue() 
        
        thread_args = (source_path, profile_name, destination_root)
        print(f"DEBUG: _refresh_scan_data: Starting thread with args: {thread_args}", flush=True)
        self.scan_thread = threading.Thread(target=self._scan_worker, args=thread_args, daemon=True)
        self.scan_thread.start()

        self.app.after(100, self._check_scan_queue)

    def _validate_scan_inputs(self, source_path: str, profile_name: str, destination_root: str) -> bool:
        """Validate scan inputs and show appropriate errors."""
        if not source_path or not os.path.isdir(source_path):
            self.app.status_label.configure(text="Error: Please select a valid source folder.")
            print("Scan aborted: No valid source folder selected.", flush=True)
            return False
        if not profile_name:
            self.app.status_label.configure(text="Error: Please select a profile.")
            print("Scan aborted: No profile selected.", flush=True)
            return False
        if not destination_root:
            self.app.status_label.configure(text="Error: Please select a destination folder.")
            print("Scan aborted: No destination folder selected.", flush=True)
            return False
        
        if not self.app.normalizer:
            self.app.status_label.configure(text="Error: Normalizer not available. Check logs.")
            print("Scan aborted: Normalizer not available. Check logs.", flush=True)
            return False

        return True

    def _scan_worker(self, source_path: str, profile_name: str, destination_root: str):
        """Worker thread method that performs scanning and normalization using GuiNormalizerAdapter."""
        print(f"DEBUG: _scan_worker started with source='{source_path}', profile='{profile_name}', dest_root='{destination_root}'")
        self.app.status_manager.add_log_message(f"Scan worker started for source: '{os.path.basename(source_path)}', profile: '{profile_name}'.")
        try:
            if not self.app.normalizer:
                self.result_queue.put({"type": "final_error", "data": "Normalizer not initialized."})
                return

            # Apply current thread settings to the scanner before scanning
            if hasattr(self.app.normalizer, 'scanner'):
                scan_threads = getattr(self.app, 'current_scan_threads', 4)
                self.app.normalizer.scanner.max_workers_local = scan_threads
                self.app.normalizer.scanner.max_workers_network = max(2, scan_threads // 2)  # Use half for network
                print(f"DEBUG: Applied scan thread settings: local={scan_threads}, network={self.app.normalizer.scanner.max_workers_network}")

            print(f"DEBUG: _scan_worker: About to call normalizer.scan_and_normalize_structure")
            scan_and_norm_results = self.app.normalizer.scan_and_normalize_structure(
                base_path=source_path,
                profile_name=profile_name,
                destination_root=destination_root,
                status_callback=self._schedule_general_adapter_processing
            )
            print(f"DEBUG: _scan_worker: normalizer returned data structure with keys: {scan_and_norm_results.keys() if isinstance(scan_and_norm_results, dict) else 'Not a dict'}")

            results_for_queue = {
                "type": "final_success",
                "data": scan_and_norm_results,
                "source_path_base": source_path
            }
            data_summary = 'Not a dict'
            if isinstance(scan_and_norm_results, dict):
                num_proposals = len(scan_and_norm_results.get('proposals', []))
                tree_exists = 'Yes' if scan_and_norm_results.get('original_scan_tree') else 'No'
                data_summary = f"Proposals: {num_proposals}, Tree_exists: {tree_exists}"
            print(f"DEBUG: _scan_worker: Putting results on queue: type='{results_for_queue['type']}', data_summary: {data_summary}")
            self.result_queue.put(results_for_queue)
            num_proposals_final = len(scan_and_norm_results.get('proposals', [])) if isinstance(scan_and_norm_results, dict) else 0
            self.app.status_manager.add_log_message(f"Scan worker successfully processed, generated {num_proposals_final} proposals for '{os.path.basename(source_path)}'.")

        except Exception as e:
            error_message = f"Error in scan worker: {e}\n{traceback.format_exc()}"
            print(error_message)  # Log to console
            self.app.status_manager.add_log_message(f"Error in scan worker for '{os.path.basename(source_path)}': {e}", level="ERROR")
            self.result_queue.put({"type": "final_error", "data": error_message})

    def _check_scan_queue(self):
        """Checks the result_queue for final results from the scan worker thread."""
        try:
            result = self.result_queue.get_nowait()  # Non-blocking get from the final result queue

            # Re-enable refresh button
            self.app.refresh_btn.configure(state=tk.NORMAL)

            if isinstance(result, dict) and result.get("type") == "final_error":
                error_data = result.get('data', 'Unknown error during scan.')
                self.app.status_label.configure(text=f"Scan Failed: {error_data}")
                print(f"Scan failed (from worker): {error_data}")
                
                # Finish progress with error
                self.app.status_manager.finish_scan_progress(False, error_data)
                
            elif isinstance(result, dict) and result.get("type") == "final_success":
                result_data_dict = result.get('data', {})
                source_path = self.app.selected_source_folder.get()

                original_tree_data = result_data_dict.get('original_scan_tree')
                normalized_proposals_list = result_data_dict.get('proposals', [])

                if original_tree_data and isinstance(original_tree_data, dict):
                    # _populate_source_tree expects a list of the root's children
                    self.app.tree_manager.populate_source_tree(original_tree_data.get('children', []), source_path)
                else:
                    self.app.tree_manager.populate_source_tree([], source_path)  # Pass empty list if no tree data
                
                if hasattr(self.app, 'preview_tree'):
                    self.app.tree_manager.populate_preview_tree(normalized_proposals_list, source_path)

                num_proposals = len(normalized_proposals_list)
                base_name = os.path.basename(source_path) if source_path else "selected folder"
                self.app.status_label.configure(text=f"Scan Complete. Generated {num_proposals} proposals from {base_name}.")
                print(f"Scan complete (from worker). Generated proposals: {num_proposals}")
                
                # Finish progress successfully
                self.app.status_manager.finish_scan_progress(True)
                
            else:
                # This case should ideally not happen if _scan_worker only puts final_error/final_success
                print(f"Unexpected item in result_queue: {result}")
                self.app.status_label.configure(text="Scan finished with unexpected result.")
                self.app.status_manager.finish_scan_progress(False, "Unexpected result")

        except Empty:  # queue.Empty - no final result yet, keep checking
            self.app.after(100, self._check_scan_queue)
        except Exception as e:  # Catch any other unexpected errors during UI update in _check_scan_queue
            self.app.refresh_btn.configure(state=tk.NORMAL)  # Re-enable refresh button on error too
            error_msg = f"Error processing scan result: {e}\n{traceback.format_exc()}"
            self.app.status_label.configure(text=error_msg)
            print(error_msg)
            self.app.status_manager.finish_scan_progress(False, error_msg)

    def _schedule_general_adapter_processing(self, status_data):
        """Schedule general adapter processing on the main thread."""
        self.app.after(0, lambda: self.app.status_manager.process_adapter_status(status_data))

    def update_scan_status(self, current_path: str):
        """Callback to update status label during scan. Thread-safe."""
        max_len = 70
        display_path = current_path
        if len(current_path) > max_len:
            display_path = "..." + current_path[-(max_len-3):]
        # Schedule the UI update on the main thread
        self.app.after(0, lambda path=display_path: self.app.status_label.configure(text=f"Scanning: {path}")) 