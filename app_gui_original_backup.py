# Main application GUI module
print("--- EXECUTING LATEST APP_GUI.PY ---")
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
import json
import os
import threading
from queue import Queue, Empty
import re
import traceback # Added for error logging
from typing import List, Dict, Any, Optional, Callable # Added for type hinting
from python.gui_normalizer_adapter import GuiNormalizerAdapter # Import the Adapter
import datetime
from python.file_operations_utils.file_management import copy_item, move_item # Added importing the CTk App instance
import uuid # For generating unique transfer IDs

# Appearance and Theme Settings - Should be called before creating the CTk App instance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"

# Path to your custom theme file
# Ensure this path is correct relative to where app_gui.py is located.
# __file__ gives the path of the current script.
_script_dir = os.path.dirname(os.path.abspath(__file__))
custom_theme_path = os.path.join(_script_dir, "themes", "custom_blue.json")

if os.path.exists(custom_theme_path):
    print(f"Loading custom theme from: {custom_theme_path}")
    ctk.set_default_color_theme(custom_theme_path)
else:
    print(f"Custom theme file not found at {custom_theme_path}. Using default blue theme.")
    ctk.set_default_color_theme("blue")  # Fallback to a default theme

class CleanIncomingsApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the map for storing full data associated with preview tree items
        self.preview_tree_item_data_map = {}
        
        # Initialize file transfer tracking
        self.active_transfers = {}  # Dictionary to store FileTransfer instances by transfer_id
        self.current_transfer_info = {
            'file_name': '',
            'speed_mbps': 0.0,
            'eta_str': 'Calculating...',
            'percent': 0.0,
            'status': 'idle'
        }

        self.title("Clean Incomings - CustomTkinter Edition")
        self.geometry("1300x850") # Increased size slightly for new controls

        # These lists are for the settings UI, not for setting the initial theme here
        self.appearance_modes = ["Light", "Dark", "System"]
        self.color_themes = ["blue", "green", "dark-blue"] # Add "custom_blue" if you want it in dropdown
        self.current_corner_radius = 10 # For rounded buttons and frames

        # Variables to store state
        self.selected_source_folder = tk.StringVar()
        self.selected_destination_folder = tk.StringVar()
        self.selected_profile_name = tk.StringVar()
        self.profiles_data = {} 
        self.profile_names = []
        self.accent_widgets = [] # List to store widgets that show accent color
        # Determine config directory path (assuming it's 'config' sibling to 'python' dir where adapter is)
        # This needs to be robust. If app_gui.py is at root, config_dir_path is 'config'.
        # If script_dir is where app_gui.py is, then config is a subfolder.
        # For now, assuming app_gui.py is at the project root G:\My Drive\python\CleanIncomings\
        self._config_dir_path = os.path.join(_script_dir, "config")
        if not os.path.isdir(self._config_dir_path):
            # Fallback if app_gui.py is in a subdirectory, try parent's 'config'
            parent_dir = os.path.dirname(_script_dir)
            fallback_config_path = os.path.join(parent_dir, "config")
            if os.path.isdir(fallback_config_path):
                self._config_dir_path = fallback_config_path
            else:
                # Default to a 'config' folder in the current working directory as a last resort
                # Or raise an error if critical
                print(f"Warning: Config directory not found at {self._config_dir_path} or {fallback_config_path}. Attempting default.")
                self._config_dir_path = os.path.join(os.getcwd(), "config")
                # Consider raising an error here if config is essential for startup
                # For now, GuiNormalizerAdapter will raise error if patterns.json/profiles.json are not found

        print(f"Using config directory: {self._config_dir_path}")

        try:
            self.normalizer = GuiNormalizerAdapter(config_dir_path=self._config_dir_path)
            self.profile_names = self.normalizer.get_profile_names() # Load profile names from adapter
            if self.profile_names:
                self.selected_profile_name.set(self.profile_names[0])
            else:
                self.status_label.configure(text="Error: No profiles found. Check logs.")
                print("Error: No profiles loaded from adapter.")
        except Exception as e:
            self.normalizer = None # Ensure it's None if init fails
            self.profile_names = []
            error_message = f"Failed to initialize Normalizer: {e}. Check config path and files."
            print(error_message)
            # Display error in GUI, e.g., in status_label, after widgets are created
            # We'll update status_label in _create_widgets or _load_profiles if it's already created there
            # For now, just printing. The _load_profiles method might be better place for this UI update.
            # self.status_label.configure(text=error_message) # This line might fail if status_label not yet created
            # Consider a popup or a more prominent error display if initialization fails critically.
            # For now, the program might continue with self.normalizer as None, buttons should check this.

        self._create_widgets()
        self._setup_treeview_style() # Initial Treeview style setup
        self._load_profiles() # This method's functionality is now integrated with GuiNormalizerAdapter initialization and the logic below

        # Configure profile_combobox based on profiles loaded by GuiNormalizerAdapter
        # This assumes self.profile_names was populated during GuiNormalizerAdapter instantiation earlier in __init__
        if hasattr(self, 'profile_combobox'): # Ensure profile_combobox widget exists
            if self.normalizer and self.profile_names:
                self.profile_combobox.configure(values=self.profile_names)
                if self.profile_names: # Set default if not empty
                    default_profile_to_set = self.profile_names[0]
                    self.profile_combobox.set(default_profile_to_set)
                    self.selected_profile_name.set(default_profile_to_set) # Sync the tk.StringVar
                else:
                    # No profiles, but normalizer is fine (empty profiles list)
                    if hasattr(self, 'status_label'): self.status_label.configure(text="No profiles available in config.")
                    self.profile_combobox.configure(values=["No Profiles Available"], state="disabled")
                    self.profile_combobox.set("No Profiles Available")
            elif self.normalizer is None:
                # Normalizer failed to initialize
                if hasattr(self, 'status_label'): self.status_label.configure(text="Normalizer error. Check logs.")
                self.profile_combobox.configure(values=["Error: Profiles N/A"], state="disabled")
                self.profile_combobox.set("Error: Profiles N/A")
            else: # Normalizer exists, but self.profile_names is empty/None (should be caught by first 'if' really)
                if hasattr(self, 'status_label'): self.status_label.configure(text="No profiles found after init.")
                self.profile_combobox.configure(values=["No Profiles Loaded"], state="disabled")
                self.profile_combobox.set("No Profiles Loaded")
        else:
            # This case should ideally not happen if _create_widgets ran correctly
            print("[CRITICAL] CleanIncomingsApp.__init__: profile_combobox widget not found when trying to configure it.")
            if hasattr(self, 'status_label'): self.status_label.configure(text="GUI Error: Profile dropdown missing.")

    def _update_adapter_status(self, status_data: Dict[str, Any]):
        """
        Handles status messages from file operations (copy_item, move_item).
        Processes detailed progress information including percent, speed, ETA, and transfer_id.
        This method is thread-safe and schedules UI updates on the main thread.
        """
        try:
            status_type = status_data.get('type', '')
            data = status_data.get('data', {})
            
            # Extract common fields
            status = data.get('status', '')
            message = data.get('message', '')
            file_path = data.get('file_path', '')
            transfer_id = data.get('transfer_id', '')
            
            # Extract detailed progress fields (if present)
            percent = data.get('percent', 0.0)
            speed_mbps = data.get('speed_mbps', 0.0)
            eta_str = data.get('eta_str', 'Calculating...')
            transferred_bytes = data.get('transferred_bytes', 0)
            total_bytes = data.get('total_bytes', 0)
            
            # Get file name for display
            file_name = os.path.basename(file_path) if file_path else 'Unknown file'
            
            self._add_log_message(f"Status update: {status_type} - {message}", "DEBUG")
            
            # Schedule UI updates on the main thread
            if status_type.startswith('file_operation_'):
                operation_type = status_type.replace('file_operation_', '')
                
                if operation_type == 'progress':
                    self._schedule_progress_update(file_name, percent, speed_mbps, eta_str, status)
                elif operation_type in ['success', 'error', 'cancelled']:
                    self._schedule_completion_update(message, operation_type)
                else:
                    # Generic status update
                    self.after(0, lambda msg=message: self.status_label.configure(text=msg))
            
        except Exception as e:
            error_msg = f"Error processing status update: {e}"
            self._add_log_message(error_msg, "ERROR")
            print(f"_update_adapter_status error: {e}")

    def _schedule_progress_update(self, file_name: str, percent: float, speed_mbps: float, eta_str: str, status: str):
        """Schedules a progress update on the main thread."""
        def update_progress():
            try:
                # Update progress bar
                self.progress_bar.set(percent / 100.0)  # CTkProgressBar expects 0.0-1.0
                self.progress_bar.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
                
                # Update main status label
                if status == 'paused':
                    status_text = f"Paused: {file_name} ({percent:.1f}%)"
                else:
                    status_text = f"Copying: {file_name} ({percent:.1f}%)"
                self.status_label.configure(text=status_text)
                
                # Update transfer details label with speed and ETA
                if status == 'paused':
                    details_text = "Transfer paused"
                elif speed_mbps > 0:
                    details_text = f"Speed: {speed_mbps:.1f} MB/s • ETA: {eta_str}"
                else:
                    details_text = "Calculating transfer speed..."
                self.transfer_details_label.configure(text=details_text)
                
                # Update current transfer info for potential future use
                self.current_transfer_info.update({
                    'file_name': file_name,
                    'speed_mbps': speed_mbps,
                    'eta_str': eta_str,
                    'percent': percent,
                    'status': status
                })
                
            except Exception as e:
                self._add_log_message(f"Error updating progress UI: {e}", "ERROR")
        
        self.after(0, update_progress)

    def _schedule_completion_update(self, message: str, completion_type: str):
        """Schedules a completion update on the main thread."""
        def update_completion():
            try:
                # Hide progress bar and reset it
                self.progress_bar.grid_remove()
                self.progress_bar.set(0.0)
                
                # Update status label based on completion type
                if completion_type == 'success':
                    self.status_label.configure(text=message)
                elif completion_type == 'error':
                    self.status_label.configure(text=f"Error: {message}")
                elif completion_type == 'cancelled':
                    self.status_label.configure(text=f"Cancelled: {message}")
                
                # Clear transfer details
                self.transfer_details_label.configure(text="")
                
                # Reset current transfer info
                self.current_transfer_info.update({
                    'file_name': '',
                    'speed_mbps': 0.0,
                    'eta_str': 'Calculating...',
                    'percent': 0.0,
                    'status': 'idle'
                })
            except Exception as e:
                self._add_log_message(f"Error updating completion UI: {e}", "ERROR")
    def _process_adapter_status(self, status_info: dict):
        """Processes status updates in the main GUI thread."""
        status_type = status_info.get("type")
        data = status_info.get("data", {})

        # Ensure progress bar is visible and reset color before processing
        self.progress_bar.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        try:
            default_text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            if isinstance(default_text_color, tuple): # (light_mode_color, dark_mode_color)
                 current_mode = ctk.get_appearance_mode()
                 default_text_color = default_text_color[0] if current_mode == "Light" else default_text_color[1]
            self.status_label.configure(text_color=default_text_color)
        except Exception:
             self.status_label.configure(text_color="black") # Fallback

        if status_type == "scan":
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
                if self.progress_bar.cget('mode') == 'indeterminate':
                    self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                self.progress_bar.set(1.0)
            elif status_message == "failed":
                if self.progress_bar.cget('mode') == 'indeterminate':
                    self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                self.progress_bar.set(max(0.0, min(1.0, current_progress_float)))
                self.status_label.configure(text_color="red")
            elif status_message == "running" and total_files_scanned == 0 and estimated_total > 0 and progress_percentage == 0:
                if self.progress_bar.cget('mode') != 'indeterminate': # Check if not already indeterminate
                    self.progress_bar.configure(mode='indeterminate')
                    self.progress_bar.start()
            else: # 'running' with files scanned, or other states
                if self.progress_bar.cget('mode') == 'indeterminate':
                    self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                display_value = current_progress_float
                if 0 < current_progress_float < 0.05 and total_files_scanned > 0:
                    display_value = 0.05
                elif current_progress_float == 0 and total_files_scanned > 0 and estimated_total > 0:
                     display_value = 0.01 # Show minimal progress if scan started but percentage is still zero
                self.progress_bar.set(max(0.0, min(1.0, display_value)))

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
                 self.status_label.configure(text_color="red") # Ensure color is red for failed scan
            else:
                 status_text = f"{display_status_message}: {count_info}{estimated_total_info} ({progress_percentage:.1f}%){eta_text}{detail_str}"
            
            self.status_label.configure(text=status_text)

        elif status_type == "mapping_generation":
            mg_status = data.get("status", "processing")
            mg_message = data.get("message", "...")
            current_files = data.get("current_file_count", 0)
            total_files = data.get("total_files", 0)
            progress_percentage_val = data.get("progress_percentage", None)

            progress_text = mg_message
            current_progress_value = 0.0 # This is float 0.0-1.0

            if progress_percentage_val is not None:
                current_progress_value = float(progress_percentage_val) / 100.0
                progress_text = f"{mg_message} ({progress_percentage_val:.1f}%)"
            elif total_files > 0:
                current_progress_value = float(current_files) / float(total_files)
                progress_text = f"{mg_message} ({current_files}/{total_files} - {current_progress_value*100:.1f}%)"
            elif mg_status == "starting" or mg_status == "collecting_files":
                if self.progress_bar.cget('mode') != 'indeterminate': # Check if not already indeterminate
                    self.progress_bar.configure(mode='indeterminate')
                    self.progress_bar.start()
                progress_text = f"{mg_message} (Initializing...)"
            
            if not (mg_status == "starting" or mg_status == "collecting_files") or total_files > 0 or progress_percentage_val is not None:
                 if self.progress_bar.cget('mode') == 'indeterminate':
                    self.progress_bar.stop()
                 self.progress_bar.configure(mode='determinate')
                 self.progress_bar.set(max(0.0, min(1.0, current_progress_value)))

            if mg_status == "completed" or mg_status == "warning" or mg_status == "finished":
                if self.progress_bar.cget('mode') == 'indeterminate': self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                self.progress_bar.set(1.0)
            elif mg_status == "error":
                if self.progress_bar.cget('mode') == 'indeterminate': self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                self.status_label.configure(text_color="red")

            self.status_label.configure(text=f"Mapping: {progress_text}")
            if mg_status == "error":
                self.status_label.configure(text_color="red")
        
        else:
            self._add_log_message(f"Received unhandled status type: {status_type} with data: {data}", "WARNING")
            self.status_label.configure(text=f"Status: {status_type} - {data.get('message', 'No message')}")
    def _scan_worker(self, source_path: str, profile_name: str, destination_root: str):
        """Worker thread method that performs scanning and normalization using GuiNormalizerAdapter."""
        print(f"DEBUG: _scan_worker started with source='{source_path}', profile='{profile_name}', dest_root='{destination_root}'")
        self._add_log_message(f"Scan worker started for source: '{os.path.basename(source_path)}', profile: '{profile_name}'.")
        try:
            if not self.normalizer:
                self.result_queue.put({"type": "final_error", "data": "Normalizer not initialized."})
                return

            # GuiNormalizerAdapter.scan_and_normalize_structure will use _update_adapter_status
            # for intermediate progress updates, which then calls _process_adapter_status in the main thread.
            # It returns the final list of normalized items upon completion.
            print(f"DEBUG: _scan_worker: About to call normalizer.scan_and_normalize_structure")
            scan_and_norm_results = self.normalizer.scan_and_normalize_structure(
                base_path=source_path,
                profile_name=profile_name,
                destination_root=destination_root,
                status_callback=self._schedule_general_adapter_processing # Use for intermediate GUI updates
            )
            print(f"DEBUG: _scan_worker: normalizer returned data structure with keys: {scan_and_norm_results.keys() if isinstance(scan_and_norm_results, dict) else 'Not a dict'}")

            results_for_queue = {
                "type": "final_success",
                "data": scan_and_norm_results, # Pass the whole dict
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
            self._add_log_message(f"Scan worker successfully processed, generated {num_proposals_final} proposals for '{os.path.basename(source_path)}'.")

        except Exception as e:
            error_message = f"Error in scan worker: {e}\n{traceback.format_exc()}"
            print(error_message) # Log to console
            self._add_log_message(f"Error in scan worker for '{os.path.basename(source_path)}': {e}", level="ERROR")
            self.result_queue.put({"type": "final_error", "data": error_message})

    def _check_scan_queue(self):
        """Checks the result_queue for final results from the scan worker thread."""
        try:
            result = self.result_queue.get_nowait() # Non-blocking get from the final result queue

            # Stop progress bar and hide it ONLY when a final result is processed.
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self.refresh_btn.configure(state=tk.NORMAL) # Re-enable scan button

            if isinstance(result, dict) and result.get("type") == "final_error":
                error_data = result.get('data', 'Unknown error during scan.')
                self.status_label.configure(text=f"Scan Failed: {error_data}")
                print(f"Scan failed (from worker): {error_data}")
            elif isinstance(result, dict) and result.get("type") == "final_success":
                result_data_dict = result.get('data', {}) # This is now {'original_scan_tree': ..., 'proposals': ...}
                source_path = self.selected_source_folder.get()

                original_tree_data = result_data_dict.get('original_scan_tree')
                normalized_proposals_list = result_data_dict.get('proposals', [])

                if original_tree_data and isinstance(original_tree_data, dict):
                    # _populate_source_tree expects a list of the root's children
                    self._populate_source_tree(original_tree_data.get('children', []), source_path)
                else:
                    self._populate_source_tree([], source_path) # Pass empty list if no tree data
                
                if hasattr(self, 'preview_tree'):
                    self._populate_preview_tree(normalized_proposals_list, source_path)

                num_proposals = len(normalized_proposals_list)
                base_name = os.path.basename(source_path) if source_path else "selected folder"
                self.status_label.configure(text=f"Scan Complete. Generated {num_proposals} proposals from {base_name}.")
                print(f"Scan complete (from worker). Generated proposals: {num_proposals}")
            else:
                # This case should ideally not happen if _scan_worker only puts final_error/final_success
                print(f"Unexpected item in result_queue: {result}")
                self.status_label.configure(text="Scan finished with unexpected result.")

        except Empty: # queue.Empty - no final result yet, keep checking
            self.after(100, self._check_scan_queue)
        except Exception as e: # Catch any other unexpected errors during UI update in _check_scan_queue
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self.refresh_btn.configure(state=tk.NORMAL) # Re-enable refresh button on error too
            error_msg = f"Error processing scan result: {e}\n{traceback.format_exc()}"
            self.status_label.configure(text=error_msg)
            print(error_msg)

    def _populate_preview_tree(self, normalized_file_list: List[Dict[str, Any]], source_path_base: str):
        """Populates the preview_tree with the flat list of normalized file/sequence data."""
        if not hasattr(self, 'preview_tree'):
            print("Preview tree not available.")
            return

        for i in self.preview_tree.get_children():
            self.preview_tree.delete(i)
        if hasattr(self, 'preview_tree_item_data_map'):
            self.preview_tree_item_data_map.clear()

        if not normalized_file_list:
            self.status_label.configure(text="No files/sequences found or processed.")
            print("No data for preview tree.")
            return

        # Columns: ('filename', 'tags', 'task', 'asset', 'new_path')
        for item_data in normalized_file_list:
            filename = item_data.get('filename', 'N/A')
            tags = ", ".join(item_data.get('matched_tags', []))
            task = item_data.get('normalized_parts', {}).get('task', '')
            asset = item_data.get('normalized_parts', {}).get('asset', '')
            new_path = item_data.get('new_destination_path', '')
            original_path = item_data.get('source_path', '') # For reference, not directly in a column
            item_id = item_data.get('id', original_path) # Use original_path as fallback ID
            status = item_data.get('status', 'unknown')
            error_msg = item_data.get('error_message')

            # Customize appearance based on status
            tag_list_for_style = []
            if status == 'error' or error_msg:
                tag_list_for_style.append('error')
                tags = f"ERROR: {error_msg[:50]}{'...' if error_msg and len(error_msg) > 50 else ''}" # Show error in tags
            elif status == 'manual':
                tag_list_for_style.append('manual')
            elif status == 'unmatched':
                tag_list_for_style.append('unmatched')
            
            # Store the full item_data with the treeview item for later use (e.g. on apply)
            self.preview_tree.insert('', 'end', iid=item_id, text="☐", 
                                     values=(filename, tags, task, asset, new_path),
                                     tags=tuple(tag_list_for_style),
                                     open=False)
            if hasattr(self, 'preview_tree_item_data_map'):
                self.preview_tree_item_data_map[item_id] = item_data

        # Configure styles for different statuses
        # Assuming Treeview has methods like tag_configure or similar through style
        # This might need adjustment based on CTkTreeView capabilities or direct ttk.Style use
        # For ttk.Treeview:
        # self.preview_tree.tag_configure('error', background='pink', foreground='red')
        # self.preview_tree.tag_configure('manual', background='lightyellow', foreground='orange')
        # self.preview_tree.tag_configure('unmatched', background='lightgrey')
        # For CTkTreeView, this styling might be different or need to be handled via its specific API if available
        # For now, the tags are set; actual visual styling based on tags needs to be ensured by the Treeview's capabilities.

        self.status_label.configure(text=f"Preview populated with {len(normalized_file_list)} items from {os.path.basename(source_path_base)}.")
        print(f"Preview tree populated with {len(normalized_file_list)} items.")
        self._update_action_button_states() # Update button states after populating tree

    def _on_scan_button_click(self):
        source_path = self.selected_source_folder.get()
        profile_name = self.selected_profile_name.get()
        destination_root = self.selected_destination_folder.get()

        if not source_path:
            self.status_label.configure(text="Please select a source folder.")
            return
        if not profile_name:
            self.status_label.configure(text="Please select a profile.")
            return
        if not destination_root:
            self.status_label.configure(text="Please select a destination root folder.")
            return
        
        if not self.normalizer:
            self.status_label.configure(text="Error: Normalizer not available. Check logs.")
            return

        self.progress_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.progress_bar.start()
        self.status_label.configure(text=f"Scanning {os.path.basename(source_path)} with profile '{profile_name}'...")

        # Clear previous preview results
        if hasattr(self, 'preview_tree'):
            for i in self.preview_tree.get_children():
                self.preview_tree.delete(i)

        self.result_queue = Queue()
        thread_args = (source_path, profile_name, destination_root)
        self.scan_thread = threading.Thread(target=self._scan_worker, args=thread_args, daemon=True)
        self.scan_thread.start()
        self.after(100, self._check_scan_queue) # Start checking the queue

    def _update_action_button_states(self, event=None): # event is passed by TreeviewSelect
        """Enable/disable copy/move buttons based on selection and destination folder."""
        has_selection = bool(self.preview_tree.selection())
        has_destination = bool(self.selected_destination_folder.get())
        buttons_state = tk.NORMAL if has_selection and has_destination else tk.DISABLED

        if hasattr(self, 'copy_selected_btn'):
            self.copy_selected_btn.configure(state=buttons_state)
        if hasattr(self, 'move_selected_btn'):
            self.move_selected_btn.configure(state=buttons_state)

    def _setup_treeview_style(self):
        style = ttk.Style(self)
        current_mode = ctk.get_appearance_mode()

        active_color_theme_name = self.color_theme_menu.get() # e.g. "blue", "green"

        # Define base colors for Treeview (non-selected parts)
        if current_mode == "Light":
            bg_color = "#FFFFFF"  # White background for light mode
            text_color = "#000000"  # Black text for light mode
            header_bg_color = "#EAEAEA" # Light gray for header
            header_text_color = "#000000"
        else:  # Dark Mode
            bg_color = "#2B2B2B"  # Dark gray background for dark mode
            text_color = "#FFFFFF"  # White text for dark mode
            header_bg_color = "#3C3C3C" # Slightly lighter dark gray for header
            header_text_color = "#FFFFFF"

        # Attempt to get accent color from the current CustomTkinter theme for SELECTION
        # Default to a sensible blue if theme colors are not available or not suitable
        default_selected_fg_light = "#3B8ED0" # Default blue for light mode selection
        default_selected_fg_dark = "#1F6AA5"   # Default blue for dark mode selection

        try:
            button_theme = ctk.ThemeManager.theme["CTkButton"]
            raw_selected_color = button_theme["fg_color"][0 if current_mode == "Light" else 1]
            raw_header_active_bg = button_theme["hover_color"][0 if current_mode == "Light" else 1]

            # Validate selected_color
            try:
                self.winfo_rgb(raw_selected_color) # Test if it's a valid Tk color
                selected_color = raw_selected_color
            except tk.TclError:
                selected_color = default_selected_fg_light if current_mode == "Light" else default_selected_fg_dark

            # Validate header_active_bg_color
            try:
                self.winfo_rgb(raw_header_active_bg)
                header_active_bg_color = raw_header_active_bg
            except tk.TclError:
                header_active_bg_color = selected_color # Fallback to validated selected_color

            # Determine selected_text_color based on the validated selected_color's brightness
            try:
                r, g, b = self.winfo_rgb(selected_color) # Use validated selected_color
                brightness = (r/256 * 0.299 + g/256 * 0.587 + b/256 * 0.114)
                selected_text_color = "#000000" if brightness > 128 else "#FFFFFF"
            except tk.TclError: # Should not happen if selected_color is validated, but as a safeguard
                selected_text_color = "#FFFFFF" if current_mode == "Dark" else "#000000"
                
        except (KeyError, AttributeError, TypeError):
            # Fallback for entire block if theme properties are missing
            selected_color = default_selected_fg_light if current_mode == "Light" else default_selected_fg_dark
            selected_text_color = "#FFFFFF" if (self.winfo_rgb(selected_color)[0]/256 * 0.299 + self.winfo_rgb(selected_color)[1]/256 * 0.587 + self.winfo_rgb(selected_color)[2]/256 * 0.114) <= 128 else "#000000"
            header_active_bg_color = selected_color

        style.theme_use("default") # Start with a basic theme to override for ttk

        style.configure("Treeview",
                        background=bg_color, # This is for cell background, might be overridden by fieldbackground
                        foreground=text_color, # Text color for items
                        fieldbackground=bg_color, # General background for the Treeview widget area
                        borderwidth=1,
                        relief="solid")
        style.map("Treeview",
                  background=[('selected', selected_color), ('focus', selected_color)],
                  foreground=[('selected', selected_text_color), ('focus', selected_text_color)])

        style.configure("Treeview.Heading",
                        background=header_bg_color,
                        foreground=header_text_color,
                        font=('Segoe UI', 9, 'bold'), # Added font styling
                        relief="flat",
                        padding=(5, 5))
        style.map("Treeview.Heading",
                  background=[('active', header_active_bg_color), ('!active', header_bg_color)],
                  relief=[('active', 'groove')])

        self.source_tree.configure(style="Treeview")
        self.preview_tree.configure(style="Treeview")

        self.update_idletasks()
        self.update()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Allow main content area to expand
        self.grid_rowconfigure(3, weight=1) # Allow log textbox area to expand

        # --- Top Control Frame ---
        top_control_frame = ctk.CTkFrame(self, corner_radius=0)
        top_control_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        # top_control_frame.grid_columnconfigure(5, weight=1) # For theme controls to potentially expand

        # Profile Selection
        profile_label = ctk.CTkLabel(top_control_frame, text="Profile:")
        profile_label.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.profile_combobox = ctk.CTkComboBox(
            top_control_frame, 
            variable=self.selected_profile_name, 
            state="readonly",
            width=200,
            corner_radius=self.current_corner_radius
        )
        self.profile_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.accent_widgets.append(self.profile_combobox)

        # Source Folder Button
        source_btn = ctk.CTkButton(top_control_frame, text="Select Source", command=self._select_source_folder, corner_radius=self.current_corner_radius)
        source_btn.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.accent_widgets.append(source_btn)
        self.source_folder_label = ctk.CTkLabel(top_control_frame, textvariable=self.selected_source_folder, anchor="w") # Wraplength can be useful
        self.source_folder_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew", columnspan=3)

        # Destination Folder Button
        dest_btn = ctk.CTkButton(top_control_frame, text="Select Destination", command=self._select_destination_folder, corner_radius=self.current_corner_radius)
        dest_btn.grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
        self.accent_widgets.append(dest_btn)
        self.dest_folder_label = ctk.CTkLabel(top_control_frame, textvariable=self.selected_destination_folder, anchor="w")
        self.dest_folder_label.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=3)

        # Action Buttons Frame (Refresh, Settings)
        action_buttons_frame = ctk.CTkFrame(top_control_frame, fg_color="transparent")
        action_buttons_frame.grid(row=0, column=2, padx=10, pady=0, sticky="e")

        self.refresh_btn = ctk.CTkButton(action_buttons_frame, text="Refresh/Scan", command=self._refresh_scan_data, corner_radius=self.current_corner_radius, width=120)
        self.refresh_btn.pack(side="left", padx=(0,5))
        self.accent_widgets.append(self.refresh_btn)
        print("DEBUG: _create_widgets: self.refresh_btn command assigned to self._refresh_scan_data", flush=True)

        settings_btn = ctk.CTkButton(action_buttons_frame, text="Settings", command=self._open_settings_window, corner_radius=self.current_corner_radius, width=100)
        settings_btn.pack(side="left", padx=5)
        self.accent_widgets.append(settings_btn)
        
        # Theme Controls Frame
        theme_controls_frame = ctk.CTkFrame(top_control_frame, fg_color="transparent")
        theme_controls_frame.grid(row=0, column=3, padx=(20,10), pady=0, sticky="e")
        top_control_frame.grid_columnconfigure(3, weight=1) # Make this column take extra space

        appearance_label = ctk.CTkLabel(theme_controls_frame, text="Mode:")
        appearance_label.pack(side="left", padx=(0,5))
        self.appearance_mode_menu = ctk.CTkOptionMenu(theme_controls_frame, values=self.appearance_modes,
                                                       command=self._change_appearance_mode_event, corner_radius=self.current_corner_radius)
        self.appearance_mode_menu.pack(side="left", padx=(0,10))
        self.accent_widgets.append(self.appearance_mode_menu)

        color_theme_label = ctk.CTkLabel(theme_controls_frame, text="Color:")
        color_theme_label.pack(side="left", padx=(0,5))
        self.color_theme_menu = ctk.CTkOptionMenu(theme_controls_frame, values=self.color_themes,
                                                 command=self._change_color_theme_event, corner_radius=self.current_corner_radius)
        self.color_theme_menu.pack(side="left")
        self.accent_widgets.append(self.color_theme_menu)
        self.color_theme_menu.set(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"]) # Set initial value

        # --- Main Content Area (Paned Window for resizable panes) ---
        main_content_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_content_pane.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Left Pane: Source Folder Structure
        source_tree_outer_frame = ctk.CTkFrame(main_content_pane, corner_radius=self.current_corner_radius)
        source_tree_outer_frame.grid_rowconfigure(1, weight=1)
        source_tree_outer_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(source_tree_outer_frame, text="Source Folder Structure").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.source_tree = ttk.Treeview(source_tree_outer_frame, columns=("type", "size"), selectmode="browse")
        self.source_tree.heading("#0", text="Name", anchor="w")
        self.source_tree.heading("type", text="Type", anchor="w")
        self.source_tree.heading("size", text="Size", anchor="w")
        self.source_tree.column("#0", stretch=tk.YES, minwidth=150)
        self.source_tree.column("type", width=80, stretch=tk.NO, anchor="center")
        self.source_tree.column("size", width=80, stretch=tk.NO, anchor="e")
        self.source_tree.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        main_content_pane.add(source_tree_outer_frame, weight=1)
        # self.source_tree.bind("<<TreeviewSelect>>", self._on_source_tree_select) # TODO: Implement _on_source_tree_select

        # Right Pane: Preview & Information Area
        preview_outer_frame = ctk.CTkFrame(main_content_pane, corner_radius=self.current_corner_radius)
        preview_outer_frame.grid_rowconfigure(1, weight=1) # Treeview
        preview_outer_frame.grid_rowconfigure(2, weight=0) # Horizontal scrollbar (NEW)
        preview_outer_frame.grid_rowconfigure(3, weight=0) # Action buttons (was 2)
        preview_outer_frame.grid_rowconfigure(4, weight=0) # Info display (was 3)
        preview_outer_frame.grid_columnconfigure(0, weight=1)
        main_content_pane.add(preview_outer_frame, weight=2)

        ctk.CTkLabel(preview_outer_frame, text="Preview & Actions").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.preview_tree_columns = ("filename", "tags", "task", "asset", "new_path")
        self.preview_tree = ttk.Treeview(preview_outer_frame, columns=self.preview_tree_columns, show="tree headings", selectmode="extended")
        
        self.preview_tree.heading("#0", text="Sel") # For checkbox text via item's text property
        self.preview_tree.heading("filename", text="File/Sequence Name")
        self.preview_tree.heading("tags", text="Matched Tags")
        self.preview_tree.heading("task", text="Task") # Editable
        self.preview_tree.heading("asset", text="Asset") # Editable
        self.preview_tree.heading("new_path", text="New Destination Path")

        self.preview_tree.column("#0", width=40, stretch=tk.NO, anchor="center", minwidth=30) # Checkbox column
        self.preview_tree.column("filename", width=250, stretch=tk.YES, minwidth=150)
        self.preview_tree.column("tags", width=120, stretch=tk.NO, minwidth=80)
        self.preview_tree.column("task", width=100, stretch=tk.NO, minwidth=80) 
        self.preview_tree.column("asset", width=100, stretch=tk.NO, minwidth=80)
        self.preview_tree.column("new_path", width=300, stretch=tk.YES, minwidth=200)

        self.preview_tree.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.preview_tree.bind("<<TreeviewSelect>>", self._update_action_button_states)

        # Horizontal Scrollbar for Preview Tree
        preview_h_scrollbar = ttk.Scrollbar(preview_outer_frame, orient='horizontal', command=self.preview_tree.xview)
        self.preview_tree.configure(xscrollcommand=preview_h_scrollbar.set)
        preview_h_scrollbar.grid(row=2, column=0, padx=5, pady=(0,5), sticky="ew")

        # TODO: Add checkbox functionality and editing for task/asset

        # Placeholder for Action Buttons (within preview_outer_frame)
        action_buttons_bottom_frame = ctk.CTkFrame(preview_outer_frame, fg_color="transparent")
        action_buttons_bottom_frame.grid(row=3, column=0, padx=5, pady=(5,0), sticky="ew") # Shifted to row 3
        # ctk.CTkLabel(action_buttons_bottom_frame, text="Batch Actions: (Copy, Move, etc.) - Coming Soon!").pack(side="left")

        self.copy_selected_btn = ctk.CTkButton(
            action_buttons_bottom_frame, 
            text="Copy Selected", 
            command=self._on_copy_selected_click, 
            state="disabled",
            corner_radius=self.current_corner_radius
        )
        self.copy_selected_btn.pack(side="left", padx=(0,5))
        self.accent_widgets.append(self.copy_selected_btn)

        self.move_selected_btn = ctk.CTkButton(
            action_buttons_bottom_frame, 
            text="Move Selected", 
            command=self._on_move_selected_click, 
            state="disabled",
            corner_radius=self.current_corner_radius
        )
        self.move_selected_btn.pack(side="left", padx=5)
        self.accent_widgets.append(self.move_selected_btn)

        # Placeholder for Information Display (within preview_outer_frame)
        info_display_bottom_frame = ctk.CTkFrame(preview_outer_frame, corner_radius=self.current_corner_radius, height=80) # Fixed height
        info_display_bottom_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew") # Shifted to row 4
        info_display_bottom_frame.pack_propagate(False) # Prevent shrinking
        ctk.CTkLabel(info_display_bottom_frame, text="Details of selected item - Coming Soon!").pack(padx=5, pady=5, anchor="nw")

        # --- Bottom Status Frame ---
        status_frame = ctk.CTkFrame(self, corner_radius=0)
        status_frame.grid(row=2, column=0, padx=0, pady=(5,0), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1) # Allow horizontal expansion
        # status_frame.grid_rowconfigure(0) # Progress bar row - default behavior
        # status_frame.grid_rowconfigure(1) # Status label row - default behavior

        self.progress_bar = ctk.CTkProgressBar(status_frame, orientation="horizontal", mode="indeterminate", corner_radius=self.current_corner_radius, height=20) # Try setting a modest height
        # Progress bar will be gridded in _refresh_scan_data when needed

        self.status_label = ctk.CTkLabel(status_frame, text="Welcome to Clean Incomings! Select a profile and folders to begin.", anchor="w")
        # Increased pady for status label, especially bottom padding
        self.status_label.grid(row=1, column=0, padx=10, pady=(5,10), sticky="ew") 
        
        # Add transfer details label for speed/ETA information
        self.transfer_details_label = ctk.CTkLabel(status_frame, text="", anchor="w", font=("Segoe UI", 10))
        self.transfer_details_label.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")

        # --- Log Textbox Frame ---
        log_textbox_frame = ctk.CTkFrame(self, corner_radius=self.current_corner_radius)
        log_textbox_frame.grid(row=3, column=0, padx=10, pady=(5,10), sticky="nsew")
        log_textbox_frame.grid_rowconfigure(0, weight=1)
        log_textbox_frame.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(
            log_textbox_frame, 
            wrap='word', 
            state='disabled', 
            corner_radius=self.current_corner_radius,
            height=150
        )
        self.log_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _select_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_source_folder.set(folder_selected)
            self.status_label.configure(text=f"Source folder: {folder_selected}")

    def _select_destination_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_destination_folder.set(folder_selected)
            self.status_label.configure(text=f"Destination: {folder_selected}")
            self._update_action_button_states() # Update button states when destination changes

    def _refresh_scan_data(self):
        print("--- _refresh_scan_data ENTERED ---", flush=True)
        print(f"DEBUG: _refresh_scan_data: self.normalizer is {'VALID' if self.normalizer else 'NONE'}", flush=True)
        # Stop any existing scan worker gracefully if possible (not implemented here)
        # For now, just clear the tree and proceed with a new scaname.get()
        source_path = self.selected_source_folder.get()
        profile_name = self.selected_profile_name.get()
        destination_root = self.selected_destination_folder.get()

        if not source_path or not os.path.isdir(source_path):
            self.status_label.configure(text="Error: Please select a valid source folder.")
            print("Scan aborted: No source folder selected.", flush=True)
            return
        if not profile_name:
            self.status_label.configure(text="Error: Please select a profile.")
            print("Scan aborted: No profile selected.", flush=True)
            return
        if not destination_root: # Consider adding os.path.isdir(destination_root) for completeness
            self.status_label.configure(text="Error: Please select a destination folder.")
            print("Scan aborted: No destination folder selected.", flush=True)
            return
        
        if not self.normalizer:
            self.status_label.configure(text="Error: Normalizer not available. Check logs.")
            print("Scan aborted: Normalizer not available. Check logs.", flush=True)
            return

        self.status_label.configure(text=f"Preparing to scan {os.path.basename(source_path)} with profile '{profile_name}'...")
        print(f"DEBUG: _refresh_scan_data: source_path='{source_path}', profile_name='{profile_name}', destination_root='{destination_root}'", flush=True)
        
        # Clear previous data from treeviews
        if hasattr(self, 'source_tree'):
            for i in self.source_tree.get_children():
                self.source_tree.delete(i)
        if hasattr(self, 'preview_tree'): 
            for i in self.preview_tree.get_children():
                self.preview_tree.delete(i)

        self.refresh_btn.configure(state=tk.DISABLED) # Disable button during scan
        self.progress_bar.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        self.progress_bar.start()

        self.result_queue = Queue() 
        
        thread_args = (source_path, profile_name, destination_root)
        print(f"DEBUG: _refresh_scan_data: Starting thread with args: {thread_args}", flush=True)
        self.scan_thread = threading.Thread(target=self._scan_worker, args=thread_args, daemon=True)
        self.scan_thread.start()

        self.after(100, self._check_scan_queue)

    def _open_settings_window(self):
        print("Open settings window called")
        # TODO: Implement settings window (perhaps using CTkToplevel)

    def _update_scan_status(self, current_path):
        """Callback to update status label during scan. Thread-safe."""
        max_len = 70
        display_path = current_path
        if len(current_path) > max_len:
            display_path = "..." + current_path[-(max_len-3):]
        # Schedule the UI update on the main thread
        self.after(0, lambda path=display_path: self.status_label.configure(text=f"Scanning: {path}"))

    def _populate_source_tree(self, items, base_path):
        """Populates the source_tree with scanned items."""
        # Clear existing items
        # self._add_log_message(f"Clearing existing source tree items.", level="DEBUG")
        for i in self.source_tree.get_children():
            self.source_tree.delete(i)
        # self._add_log_message(f"Source tree cleared. Starting to populate with {len(items) if items else 0} top-level items from base: {base_path}", level="DEBUG")

        if not items:
            self.source_tree.insert("", "end", text="No items found or directory is empty.", values=("", ""))
            return

        # Sort items: folders first, then files, then by name. Use .get() for safety.
        items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))

        for item in items:
            name = item.get('name', 'Unnamed Item')
            item_type = item.get('type', 'file').capitalize()
            size_bytes = item.get('size', '')
            
            # Format size for display
            if isinstance(size_bytes, (int, float)):
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024**2:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024**3:
                    size_str = f"{size_bytes/1024**2:.1f} MB"
                else:
                    size_str = f"{size_bytes/1024**3:.1f} GB"
            else:
                size_str = "N/A" if item_type == "Folder" else ""

            # Insert the item into the tree under the correct parent (root for top-level)
            # The item's path can serve as a unique ID for the treeview item
            item_id = item.get('path')
            if not item_id:
                # Fallback if path is somehow missing, log and skip or use a placeholder
                self._add_log_message(f"Item missing 'path', cannot add to source tree: {item}", level="WARNING")
                continue
            parent_id = os.path.dirname(item['path'])
            # For top-level items, parent_id might be the base_path itself or one level up.
            # We need a consistent way to map filesystem paths to treeview parent IDs.
            # For simplicity here, we'll define a helper for recursive insertion.

        # Helper function to insert items recursively
        def insert_items_recursively(parent_node_id, current_items):
            current_items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))
            for item_data in current_items:
                name = item_data.get('name', 'Unnamed Item')
                item_type_cap = item_data.get('type', 'file').capitalize()
                size_bytes = item_data.get('size')
                path = item_data.get('path')
                # self._add_log_message(f"Processing item: '{name}' (Type: {item_type_cap}, Path: {path}) for parent ID: '{parent_node_id or 'ROOT'}'", level="DEBUG")

                if not path:
                    self._add_log_message(f"Item missing 'path' in recursive insert, cannot add to source tree: {item_data}", level="WARNING")
                    continue

                if isinstance(size_bytes, (int, float)):
                    if size_bytes < 1024:
                        size_display = f"{size_bytes} B"
                    elif size_bytes < 1024**2:
                        size_display = f"{size_bytes/1024:.1f} KB"
                    elif size_bytes < 1024**3:
                        size_display = f"{size_bytes/1024**2:.1f} MB"
                    else:
                        size_display = f"{size_bytes/1024**3:.1f} GB"
                else:
                    size_display = "N/A" if item_type_cap == "Folder" else ""
                
                if item_data.get('type') == 'folder':
                    # Only insert and process children if the item is a folder
                    node_id = self.source_tree.insert(parent_node_id, "end", iid=path, text=name, values=(item_type_cap, size_display), open=False)
                    # self._add_log_message(f"Inserted folder: '{name}' (Path: {path}) with node ID: '{node_id}' under parent: '{parent_node_id or 'ROOT'}'", level="DEBUG")
                    
                    if 'children' in item_data and item_data['children']:
                        # If it's a folder and has children, recursively insert them
                        if not isinstance(item_data['children'], dict) or 'error' not in item_data['children']:
                            # self._add_log_message(f"Recursively processing {len(item_data['children'])} children of folder: '{name}' (Node ID: {node_id})", level="DEBUG")
                            insert_items_recursively(node_id, item_data['children'])
                        elif isinstance(item_data['children'], dict) and 'error' in item_data['children']:
                            # Optionally, insert an error node for this folder
                            self.source_tree.insert(node_id, "end", text=f"Error scanning: {item_data['children']['error']}", values=("Error", ""))
                # Files are intentionally skipped for display in the source_tree

        # Start recursive insertion from the root of the treeview (parent_node_id = "")
        self._add_log_message(f"Initiating recursive insertion into source tree for {len(items) if items else 0} items.", level="DEBUG")
        insert_items_recursively("", items)
        self._add_log_message(f"Finished populating source tree.", level="DEBUG")

    def _change_appearance_mode_event(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        self._setup_treeview_style() # Re-apply style for Treeview
        self.status_label.configure(text=f"Appearance mode changed to {new_mode}")

    def _change_color_theme_event(self, new_color_theme: str):
        """Handles changing the color theme."""
        ctk.set_default_color_theme(new_color_theme)
        
        current_mode = ctk.get_appearance_mode()
        mode_idx = 0 if current_mode == "Light" else 1

        for widget in self.accent_widgets:
            try:
                if isinstance(widget, ctk.CTkButton):
                    fg_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"][mode_idx]
                    hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"][mode_idx]
                    border_color = ctk.ThemeManager.theme["CTkButton"]["border_color"][mode_idx]
                    text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"][mode_idx]
                    widget.configure(fg_color=fg_color, hover_color=hover_color, border_color=border_color, text_color=text_color)
                
                elif isinstance(widget, (ctk.CTkComboBox, ctk.CTkOptionMenu)):
                    # For ComboBox and OptionMenu, colors are slightly different
                    # Main widget part (looks like a button)
                    fg_color = ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"][mode_idx]
                    hover_color = ctk.ThemeManager.theme["CTkOptionMenu"]["button_hover_color"][mode_idx]
                    text_color = ctk.ThemeManager.theme["CTkOptionMenu"]["text_color"][mode_idx]
                    # Dropdown arrow color might be tied to text_color or a specific dropdown_arrow_color
                    # border_color = ctk.ThemeManager.theme["CTkOptionMenu"]["border_color"][mode_idx] # If applicable
                    
                    widget.configure(fg_color=fg_color, # This is often the main background of the widget part
                                     button_color=fg_color, # Explicitly set button part color
                                     button_hover_color=hover_color,
                                     text_color=text_color,
                                     # dropdown_fg_color, dropdown_hover_color, dropdown_text_color for the menu itself
                                     dropdown_fg_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_fg_color"][mode_idx],
                                     dropdown_hover_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_hover_color"][mode_idx],
                                     dropdown_text_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_text_color"][mode_idx]
                                     )
            except Exception as e:
                print(f"Error applying theme to widget {widget}: {e}")

        self._setup_treeview_style() # Re-apply style for Treeview
        self.status_label.configure(text=f"Color theme changed to {new_color_theme}")
        self.color_theme_menu.set(new_color_theme)
        
        self.update_idletasks()
        self.update() # Standard Tkinter updates

    def _on_copy_selected_click(self):
        selected_tree_item_ids = self.preview_tree.selection() # Get standard Tkinter treeview selections
        if not selected_tree_item_ids:
            self._add_log_message("No items selected in the preview tree for copying.", "WARNING")
            return

        items_to_process = []
        for tree_item_id in selected_tree_item_ids:
            if tree_item_id in self.preview_tree_item_data_map:
                item_data = self.preview_tree_item_data_map[tree_item_id]
                items_to_process.append(item_data)
            else:
                self._add_log_message(f"Data not found for selected tree item ID: {tree_item_id}", "WARNING")

        if not items_to_process:
            self._add_log_message("No valid data found for any selected items to copy.", "WARNING")
            return

        self._add_log_message(f"Initiating copy for {len(items_to_process)} selected item(s).", "INFO")

        destination_root = self.selected_destination_folder.get()
        if not destination_root:
            self._add_log_message("Destination folder not set. Cannot copy items.", "ERROR")
            return

        for item_data in items_to_process:
            # Check if this is a sequence
            # original_item = item_data.get('original_item', {}) # This was incorrect for item_type
            item_type = item_data.get('type', 'file') # Correct: get type directly from item_data
            
            # Debug logging
            print(f"DEBUG: Processing item with type: {item_type}")
            # print(f"DEBUG: Original item keys: {list(original_item.keys()) if original_item else 'None'}") # Commented out to fix NameError
            print(f"DEBUG: Item data keys: {list(item_data.keys())}")
            
            if item_type == 'Sequence': # Match capitalized 'Sequence' from adapter
                # Handle sequence copy - copy each individual file
                print(f"DEBUG: Detected sequence, calling _copy_sequence_files")
                self._copy_sequence_files(item_data)
            else:
                # Handle single file copy
                source_path = item_data.get('source_path')
                target_path = item_data.get('new_destination_path')
                
                print(f"DEBUG: Detected single file, source: {source_path}")
                print(f"DEBUG: Target: {target_path}")

                if source_path and target_path:
                    self._add_log_message(f"Queueing copy: {source_path} -> {target_path}", "INFO")
                    thread = threading.Thread(
                        target=self._execute_file_operation_worker,
                        args=(copy_item, source_path, target_path, self._update_adapter_status),
                        daemon=True
                    )
                    thread.start()
                else:
                    item_name = item_data.get('filename', 'Unknown item')
                    self._add_log_message(f"Skipping copy for '{item_name}'. Missing source or target path. Source: {source_path}, Target: {target_path}", "WARNING")

    def _on_move_selected_click(self):
        selected_tree_item_ids = self.preview_tree.selection() # Get standard Tkinter treeview selections
        if not selected_tree_item_ids:
            self._add_log_message("No items selected in the preview tree for moving.", "WARNING")
            return

        items_to_process = []
        for tree_item_id in selected_tree_item_ids:
            if tree_item_id in self.preview_tree_item_data_map:
                item_data = self.preview_tree_item_data_map[tree_item_id]
                items_to_process.append(item_data)
            else:
                self._add_log_message(f"Data not found for selected tree item ID: {tree_item_id}", "WARNING")

        if not items_to_process:
            self._add_log_message("No valid data found for any selected items to move.", "WARNING")
            return

        self._add_log_message(f"Initiating move for {len(items_to_process)} selected item(s).", "INFO")

        destination_root = self.selected_destination_folder.get()
        if not destination_root:
            self._add_log_message("Destination folder not set. Cannot move items.", "ERROR")
            return

        for item_data in items_to_process:
            # Check if this is a sequence
            # original_item = item_data.get('original_item', {}) # This was incorrect for item_type
            item_type = item_data.get('type', 'file') # Correct: get type directly from item_data
            
            # Debug logging for move operation (original_item related print commented)
            # print(f"DEBUG: Original item keys: {list(original_item.keys()) if original_item else 'None'}") # Commented out to fix NameError
            print(f"DEBUG: Item data keys for move: {list(item_data.keys())}")

            if item_type == 'Sequence': # Match capitalized 'Sequence' from adapter
                # Handle sequence move - move each individual file
                self._move_sequence_files(item_data)
            else:
                # Handle single file move
                source_path = item_data.get('source_path')
                target_path = item_data.get('new_destination_path')

                if source_path and target_path:
                    self._add_log_message(f"Queueing move: {source_path} -> {target_path}", "INFO")
                    thread = threading.Thread(
                        target=self._execute_file_operation_worker,
                        args=(move_item, source_path, target_path, self._update_adapter_status),
                        daemon=True
                    )
                    thread.start()
                else:
                    item_name = item_data.get('filename', 'Unknown item')
                    self._add_log_message(f"Skipping move for '{item_name}'. Missing source or target path. Source: {source_path}, Target: {target_path}", "WARNING")

    def _schedule_general_adapter_processing(self, status_data):
        # Implement the logic for scheduling general adapter processing
        pass

    def _append_to_log_textbox(self, formatted_message: str):
        """Appends a message to the log_textbox. Must be called from the main GUI thread."""
        if not hasattr(self, 'log_textbox') or self.log_textbox is None:
            print(f"Log (UI not ready): {formatted_message}") # Fallback if log_textbox not ready
            return
        try:
            self.log_textbox.configure(state='normal')
            self.log_textbox.insert('end', formatted_message + "\n")
            self.log_textbox.configure(state='disabled')
            self.log_textbox.see('end')
        except tk.TclError as e:
            # This can happen if the widget is destroyed or not fully initialized
            print(f"Error appending to log textbox: {e} - Message: {formatted_message}")

    def _add_log_message(self, message: str, level: str = "INFO"):
        """Adds a message to the log display. Thread-safe."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
        
        # Always print to console for backend/debug visibility
        print(formatted_message)

        if hasattr(self, 'log_textbox') and self.log_textbox.winfo_exists():
            if threading.current_thread() is threading.main_thread():
                self._append_to_log_textbox(formatted_message)
            else:
                # Schedule the UI update to run in the main thread
                self.after(0, lambda msg=formatted_message: self._append_to_log_textbox(msg))
        else:
            # If log_textbox doesn't exist or isn't ready, queue messages or handle differently if needed
            # For now, they are just printed to console.
            pass

    def _load_profiles(self):
        profiles_path = os.path.join(os.path.dirname(__file__), "config", "profiles.json")
        try:
            if not os.path.exists(profiles_path):
                self.status_label.configure(text=f"Error: profiles.json not found at {profiles_path}")
                self.profile_combobox.configure(values=[])
                return

            with open(profiles_path, 'r') as f:
                self.profiles_data = json.load(f)
            
            self.profile_names = list(self.profiles_data.keys())
            self.profile_combobox.configure(values=self.profile_names)
            if self.profile_names:
                self.selected_profile_name.set(self.profile_names[0])
                self.status_label.configure(text=f"Profiles loaded. Selected: {self.profile_names[0]}")
            else:
                self.status_label.configure(text="No profiles found in profiles.json.")
        except Exception as e:
            self.status_label.configure(text=f"Error loading profiles: {str(e)}")
            self.profile_combobox.configure(values=[])
            print(f"Error loading profiles: {e}")


    def _execute_file_operation_worker(self, operation_func: Callable, source_path: str, destination_path: str, status_callback: Callable):
        """Worker function to execute a file operation (copy or move).
        Generates a transfer_id and passes it to the operation_func.
        """
        operation_name = "Copy" if operation_func == copy_item else "Move"
        transfer_id = uuid.uuid4().hex
        try:
            self._add_log_message(f"{operation_name} worker (ID: {transfer_id}) started for: {os.path.basename(source_path)} -> {destination_path}", "DEBUG")
            # The destination_path here is the full file path for the destination.
            # file_management.copy_item and move_item expect the full destination file path.
            # Pass the generated transfer_id to the operation function.
            operation_func(source_path, destination_path, status_callback, transfer_id)
            # Success message is handled by the status_callback from file_management
        except Exception as e:
            error_msg = f"Error during {operation_name.lower()} of {os.path.basename(source_path)} (ID: {transfer_id}): {e}"
            self._add_log_message(error_msg, "ERROR")
            # Also send to status_callback if not already handled by operation_func's internal error reporting
            status_callback({
                "type": "file_operation_error",
                "data": {
                    "status": "ERROR",
                    "message": error_msg,
                    "file_path": source_path,
                    "transfer_id": transfer_id
                }
            })

    def _copy_sequence_files(self, item_data):
        """Copy all individual files in a sequence."""
        sequence_info = item_data.get('sequence_info', {}) # Corrected key
        files_list = sequence_info.get('files', [])
        target_template = item_data.get('new_destination_path', '')
        
        # Debug logging
        # print(f"DEBUG: _copy_sequence_files called")
        # print(f"DEBUG: sequence_info content: {sequence_info}")
        # print(f"DEBUG: sequence_info keys: {list(sequence_info.keys()) if sequence_info else 'None'}")
        # print(f"DEBUG: sequence_info['source_dir']: {sequence_info.get('source_dir')}")
        # print(f"DEBUG: Files list length: {len(files_list) if files_list else 0}")
        # print(f"DEBUG: Target template: {target_template}")
        
        if not files_list:
            self._add_log_message("No files found in sequence data", "WARNING")
            # print(f"DEBUG: sequence_info content (when no files_list): {sequence_info}")
            return
            
        if not target_template:
            self._add_log_message("No target path template found for sequence", "WARNING")
            return
            
        # Extract target directory and template filename
        target_dir = os.path.dirname(target_template)
        target_filename_template = os.path.basename(target_template)
        
        self._add_log_message(f"Starting copy of {len(files_list)} files in sequence", "INFO")
        
        for i, file_info in enumerate(files_list):
            source_file_path = file_info.get('path', '')
            source_filename = file_info.get('name', '')
            print(f"DEBUG: File {i+1}/{len(files_list)}: {source_filename}")
            print(f"DEBUG: Source path: {source_file_path}")
            if not source_file_path or not os.path.exists(source_file_path):
                self._add_log_message(f"Source file not found: {source_file_path}", "WARNING")
                continue
            target_filename = source_filename    
            target_file_path = os.path.join(target_dir, target_filename)
            print(f"DEBUG: Target file path: {target_file_path}")
            # Start copy operation for this file
            thread = threading.Thread(
                target=self._execute_file_operation_worker,
                args=(copy_item, source_file_path, target_file_path, self._update_adapter_status),
                daemon=True
            )
            thread.start()

    def _move_sequence_files(self, item_data):
        """Move all individual files in a sequence."""
        sequence_info = item_data.get('sequence_info', {}) # Corrected key
        files_list = sequence_info.get('files', [])
        target_template = item_data.get('new_destination_path', '')

        print(f"DEBUG: _move_sequence_files called")
        print(f"DEBUG: sequence_info content: {sequence_info}")
        print(f"DEBUG: sequence_info keys: {list(sequence_info.keys()) if sequence_info else 'None'}")
        print(f"DEBUG: sequence_info['source_dir']: {sequence_info.get('source_dir')}")
        print(f"DEBUG: Files list length: {len(files_list) if files_list else 0}")
        print(f"DEBUG: Target template: {target_template}")

        if not files_list:
            self._add_log_message("No files found in sequence data", "WARNING")
            # print(f"DEBUG: sequence_info content (when no files_list): {sequence_info}")
            return
            
        if not target_template:
            self._add_log_message("No target path template found for sequence", "WARNING")
            return
            
        # Extract target directory and template filename
        target_dir = os.path.dirname(target_template)
        target_filename_template = os.path.basename(target_template)
        
        self._add_log_message(f"Starting move of {len(files_list)} files in sequence", "INFO")
        
        for file_info in files_list:
            source_file_path = file_info.get('path', '')
            source_filename = file_info.get('name', '')
            target_filename = source_filename # If no placeholder, use original (should ideally not happen for sequences)
            
            if not source_file_path or not os.path.exists(source_file_path):
                self._add_log_message(f"Source file not found: {source_file_path}", "WARNING")
                continue
                
            target_file_path = os.path.join(target_dir, target_filename)
            
            # Start move operation for this file
            thread = threading.Thread(
                target=self._execute_file_operation_worker,
                args=(move_item, source_file_path, target_file_path, self._update_adapter_status),
                daemon=True
            )
            thread.start()

if __name__ == '__main__':
    app = CleanIncomingsApp()
    app.mainloop()
