# Main application GUI module
print("--- EXECUTING LATEST APP_GUI.PY ---")
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
import json
import os
import threading
from queue import Queue, Empty
import traceback # Added for error logging
from typing import List, Dict, Any, Optional, Callable # Added for type hinting
from python.gui_normalizer_adapter import GuiNormalizerAdapter # Import the Adapter

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
    def _update_adapter_status(self, status_info: dict):
        """Handles status updates from the GuiNormalizerAdapter."""
        # This function will be called by the adapter's status_callback
        # We need to schedule GUI updates on the main thread
        self.after(0, self._process_adapter_status, status_info)

    def _process_adapter_status(self, status_info: dict):
        """Processes status updates in the main GUI thread."""
        status_type = status_info.get("type")
        data = status_info.get("data", {})
        
        if status_type == "scan":
            progress_percentage = data.get("progressPercentage", 0)
            status_message = data.get("status", "scanning")
            current_file = data.get("currentFile")
            current_folder = data.get("currentFolder")
            
            self.progress_bar.set(progress_percentage / 100)
            details = []
            if current_folder: details.append(f"Folder: {os.path.basename(current_folder)}")
            if current_file: details.append(f"File: {os.path.basename(current_file)}")
            
            self.status_label.configure(text=f"Scan: {status_message} ({progress_percentage:.2f}%) {' - '.join(details) if details else ''}")
            if status_message == "completed" or status_message == "failed":
                self.progress_bar.stop() # May not be needed if set(1.0) visually stops it
                # Further actions on completion/failure are handled by _check_scan_queue
        elif status_type == "mapping": # If adapter starts sending mapping progress
            # Handle mapping progress similarly if implemented in adapter
            self.status_label.configure(text=f"Mapping: {data.get('status', 'processing')}...")
        # Add more status types as needed

    def _update_adapter_status(self, status_info: dict):
        """Handles status updates from the GuiNormalizerAdapter. Thread-safe.
        Schedules _process_adapter_status to run in the main GUI thread.
        """
        self.after(0, self._process_adapter_status, status_info)

    def _scan_worker(self, source_path: str, profile_name: str, destination_root: str):
        print(f"DEBUG: _scan_worker started with source='{source_path}', profile='{profile_name}', dest_root='{destination_root}'")
        try:
            if not self.normalizer:
                self.result_queue.put({"type": "final_error", "data": "Normalizer not initialized."})
                return

            # GuiNormalizerAdapter.scan_and_normalize_structure will use _update_adapter_status
            # for intermediate progress updates, which then calls _process_adapter_status in the main thread.
            # It returns the final list of normalized items upon completion.
            print(f"DEBUG: _scan_worker: About to call normalizer.scan_and_normalize_structure")
            normalized_file_list = self.normalizer.scan_and_normalize_structure(
                base_path=source_path,
                profile_name=profile_name,
                destination_root=destination_root,
                status_callback=self._update_adapter_status # Use for intermediate GUI updates
            )
            print(f"DEBUG: _scan_worker: normalizer returned {len(normalized_file_list)} items.")
            # print(f"DEBUG: _scan_worker: normalizer returned data: {{normalized_file_list}}") # Potentially very verbose
            
            results_for_queue = {
                "type": "final_success", 
                "data": normalized_file_list,
                "source_path_base": source_path # For _populate_preview_tree context
            }
            print(f"DEBUG: _scan_worker: Putting results on queue: type='{results_for_queue['type']}', items={len(results_for_queue['data'])}")
            self.result_queue.put(results_for_queue)

        except Exception as e:
            error_message = f"Error in scan worker: {e}\n{traceback.format_exc()}"
            print(error_message) # Log to console
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
                final_data = result.get('data', [])
                source_path = self.selected_source_folder.get() # Get current source path for context
                self._populate_source_tree(final_data, source_path)
                if hasattr(self, 'preview_tree'):
                    self._populate_preview_tree(final_data, source_path)

                num_top_level_items = len(final_data) if isinstance(final_data, list) else 0
                base_name = os.path.basename(source_path) if source_path else "selected folder"
                self.status_label.configure(text=f"Scan Complete. Found {num_top_level_items} items in {base_name}.")
                print(f"Scan complete (from worker). Top-level items: {num_top_level_items}")
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
            original_path = item_data.get('original_path', '') # For reference, not directly in a column
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
            # Associate full data with item_id for easy retrieval
            self.preview_tree.item(item_id, CtkTreeview_Custom_kwargs={"full_data": item_data})

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


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        # self._load_profiles() # This method's functionality is now integrated with GuiNormalizerAdapter initialization and the logic below

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

        # --- Main Content Area (Two Frames side-by-side) ---
        main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        main_content_frame.grid_columnconfigure(0, weight=1) # Source tree pane
        main_content_frame.grid_columnconfigure(1, weight=2) # Preview tree pane
        main_content_frame.grid_rowconfigure(0, weight=1)

        # Left Pane: Source Folder Structure
        source_tree_outer_frame = ctk.CTkFrame(main_content_frame, corner_radius=self.current_corner_radius)
        source_tree_outer_frame.grid(row=0, column=0, padx=(0,5), pady=5, sticky="nsew")
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
        # self.source_tree.bind("<<TreeviewSelect>>", self._on_source_tree_select) # TODO: Implement _on_source_tree_select

        # Right Pane: Preview & Information Area
        preview_outer_frame = ctk.CTkFrame(main_content_frame, corner_radius=self.current_corner_radius)
        preview_outer_frame.grid(row=0, column=1, padx=(5,0), pady=5, sticky="nsew")
        preview_outer_frame.grid_rowconfigure(1, weight=1) # Allow treeview to expand
        preview_outer_frame.grid_rowconfigure(2, weight=0) # Action buttons fixed size
        preview_outer_frame.grid_rowconfigure(3, weight=0) # Info display fixed size
        preview_outer_frame.grid_columnconfigure(0, weight=1)

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
        # TODO: Add checkbox functionality and editing for task/asset

        # Placeholder for Action Buttons (within preview_outer_frame)
        action_buttons_bottom_frame = ctk.CTkFrame(preview_outer_frame, fg_color="transparent")
        action_buttons_bottom_frame.grid(row=2, column=0, padx=5, pady=(5,0), sticky="ew")
        ctk.CTkLabel(action_buttons_bottom_frame, text="Batch Actions: (Copy, Move, etc.) - Coming Soon!").pack(side="left")

        # Placeholder for Information Display (within preview_outer_frame)
        info_display_bottom_frame = ctk.CTkFrame(preview_outer_frame, corner_radius=self.current_corner_radius, height=80) # Fixed height
        info_display_bottom_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
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

        # Ensure the status_frame itself doesn't expand vertically too much if content is small
        # The frame will size to its content (progress bar + label + padding)

    def _select_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_source_folder.set(folder_selected)
            self.status_label.configure(text=f"Source folder: {folder_selected}")

    def _select_destination_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_destination_folder.set(folder_selected)
            self.status_label.configure(text=f"Destination folder: {folder_selected}")

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
        for i in self.source_tree.get_children():
            self.source_tree.delete(i)

        if not items:
            self.source_tree.insert("", "end", text="No items found or directory is empty.", values=("", ""))
            return

        # Sort items: folders first, then files, then by name
        items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))

        for item in items:
            name = item['name']
            item_type = item['type'].capitalize()
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
            item_id = item['path']
            parent_id = os.path.dirname(item['path'])
            # For top-level items, parent_id might be the base_path itself or one level up.
            # We need a consistent way to map filesystem paths to treeview parent IDs.
            # For simplicity here, we'll define a helper for recursive insertion.

        # Helper function to insert items recursively
        def insert_items_recursively(parent_node_id, current_items):
            current_items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
            for item_data in current_items:
                name = item_data['name']
                item_type_cap = item_data['type'].capitalize()
                size_bytes = item_data.get('size')
                path = item_data['path']

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
                
                if item_data['type'] == 'folder':
                    # Only insert and process children if the item is a folder
                    node_id = self.source_tree.insert(parent_node_id, "end", iid=path, text=name, values=(item_type_cap, size_display), open=False)
                    
                    if 'children' in item_data and item_data['children']:
                        # If it's a folder and has children, recursively insert them
                        if not isinstance(item_data['children'], dict) or 'error' not in item_data['children']:
                            insert_items_recursively(node_id, item_data['children'])
                        elif isinstance(item_data['children'], dict) and 'error' in item_data['children']:
                            # Optionally, insert an error node for this folder
                            self.source_tree.insert(node_id, "end", text=f"Error scanning: {item_data['children']['error']}", values=("Error", ""))
                # Files are intentionally skipped for display in the source_tree

        # Start recursive insertion from the root of the treeview (parent_node_id = "")
        insert_items_recursively("", items)

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

if __name__ == '__main__':
    app = CleanIncomingsApp()
    app.mainloop()
