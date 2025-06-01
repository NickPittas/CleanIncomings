"""
Widget Factory Module

Handles widget creation and layout functionality
for the Clean Incomings GUI application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox  # Added messagebox
import customtkinter as ctk
from .progress_panel import ProgressPanel
import os
from .file_operations_progress import FileOperationsProgressPanel
from .vlc_player_window import VLCPlayerWindow  # Added import


class WidgetFactory:
    """Creates and configures widgets for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the WidgetFactory.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance

    def create_widgets(self):
        """Create all widgets for the application."""
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_rowconfigure(1, weight=1)  # Main paned window area

        # Create all widget sections
        self._create_top_control_frame()
        self._create_main_resizable_layout()

    def _create_top_control_frame(self):
        """Create the top control frame with profile selection, folder buttons, and theme controls."""
        top_control_frame = ctk.CTkFrame(self.app, corner_radius=0)
        top_control_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        
        # Store reference for theme application
        self.app.control_panel_frame = top_control_frame

        # Profile Selection
        profile_label = ctk.CTkLabel(top_control_frame, text="Profile:")
        profile_label.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.app.profile_combobox = ctk.CTkComboBox(
            top_control_frame, 
            variable=self.app.selected_profile_name, 
            state="readonly",
            width=200,
            corner_radius=self.app.current_corner_radius
        )
        self.app.profile_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.app.accent_widgets.append(self.app.profile_combobox)

        # Source Folder Button + Editable Entry
        source_btn = ctk.CTkButton(top_control_frame, text="Select Source", command=self._select_source_folder, corner_radius=self.app.current_corner_radius, width=120)
        source_btn.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.app.accent_widgets.append(source_btn)
        
        # Make source folder editable
        self.app.source_folder_entry = ctk.CTkEntry(
            top_control_frame, 
            textvariable=self.app.selected_source_folder, 
            placeholder_text="Enter or select source folder path...",
            corner_radius=self.app.current_corner_radius
        )
        self.app.source_folder_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew", columnspan=3)
        self.app.source_folder_entry.bind("<KeyRelease>", self._validate_folder_entries)

        # Destination Folder Button + Editable Entry
        dest_btn = ctk.CTkButton(top_control_frame, text="Select Destination", command=self._select_destination_folder, corner_radius=self.app.current_corner_radius, width=120)
        dest_btn.grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
        self.app.accent_widgets.append(dest_btn)
        
        # Make destination folder editable
        self.app.dest_folder_entry = ctk.CTkEntry(
            top_control_frame, 
            textvariable=self.app.selected_destination_folder, 
            placeholder_text="Enter or select destination folder path...",
            corner_radius=self.app.current_corner_radius
        )
        self.app.dest_folder_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=3)
        self.app.dest_folder_entry.bind("<KeyRelease>", self._validate_folder_entries)

        # Action Buttons Frame (Refresh, Settings)
        action_buttons_frame = ctk.CTkFrame(top_control_frame, fg_color="transparent")
        action_buttons_frame.grid(row=0, column=2, padx=10, pady=0, sticky="e")

        self.app.refresh_btn = ctk.CTkButton(action_buttons_frame, 
                                            text="Refresh/Scan", 
                                            image=self.app.theme_manager.get_icon_image('refresh'),
                                            command=self.app.scan_manager.refresh_scan_data, 
                                            corner_radius=self.app.current_corner_radius, 
                                            width=150)
        self.app.refresh_btn.pack(side="left", padx=(0,5))
        self.app.accent_widgets.append(self.app.refresh_btn)

        settings_btn = ctk.CTkButton(action_buttons_frame, 
                                    text="Settings", 
                                    image=self.app.theme_manager.get_icon_image('settings'),
                                    command=self._open_settings_window, 
                                    corner_radius=self.app.current_corner_radius, 
                                    width=130)
        settings_btn.pack(side="left", padx=5)
        self.app.accent_widgets.append(settings_btn)
        
        # Theme Controls Frame
        theme_controls_frame = ctk.CTkFrame(top_control_frame, fg_color="transparent")
        theme_controls_frame.grid(row=0, column=3, padx=(20,10), pady=0, sticky="e")
        top_control_frame.grid_columnconfigure(3, weight=1)  # Make this column take extra space

        appearance_label = ctk.CTkLabel(theme_controls_frame, 
                                        text="Mode:",
                                        image=self.app.theme_manager.get_icon_image('info'),
                                        compound="left")
        appearance_label.pack(side="left", padx=(0,5))
        self.app.appearance_mode_menu = ctk.CTkOptionMenu(theme_controls_frame, values=self.app.theme_manager.appearance_modes,
                                                       command=self.app.theme_manager.change_appearance_mode_event, corner_radius=self.app.current_corner_radius)
        self.app.appearance_mode_menu.pack(side="left", padx=(0,10))
        self.app.accent_widgets.append(self.app.appearance_mode_menu)

        color_theme_label = ctk.CTkLabel(theme_controls_frame, 
                                        text="Theme:",
                                        image=self.app.theme_manager.get_icon_image('asset'),
                                        compound="left")
        color_theme_label.pack(side="left", padx=(0,5))
        self.app.color_theme_menu = ctk.CTkOptionMenu(theme_controls_frame, values=self.app.theme_manager.color_themes,
                                                 command=self.app.theme_manager.change_color_theme_event, corner_radius=self.app.current_corner_radius)
        self.app.color_theme_menu.pack(side="left")
        self.app.color_theme_menu.set("Default Blue")  # Set initial value
        self.app.accent_widgets.append(self.app.color_theme_menu)

    def _create_main_resizable_layout(self):
        """Create the main layout with resizable panels using PanedWindows."""
        # Main vertical paned window (separates content from bottom panels)
        self.app.main_vertical_pane = ttk.PanedWindow(self.app, orient=tk.VERTICAL)
        self.app.main_vertical_pane.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Top section: horizontal paned window for source tree and preview
        self.app.main_horizontal_pane = ttk.PanedWindow(self.app.main_vertical_pane, orient=tk.HORIZONTAL)
        
        # Create source tree section
        self._create_source_tree_section()
        
        # Create preview section  
        self._create_preview_section()
        
        # Add horizontal pane to main vertical pane
        self.app.main_vertical_pane.add(self.app.main_horizontal_pane, weight=3)
        
        # Set initial horizontal pane position (400px for source tree, rest for preview)
        self.app.after(50, lambda: self._set_initial_pane_positions())
        
        # Create middle section: progress panel (resizable)
        self._create_progress_panel_section()
        
        # Create bottom sections
        self._create_bottom_sections()

    def _set_initial_pane_positions(self):
        """Set initial pane positions to ensure preview panel is visible."""
        try:
            # Set horizontal pane position (source tree width = 400px)
            if hasattr(self.app, 'main_horizontal_pane'):
                self.app.main_horizontal_pane.sashpos(0, 400)
            
            # Set vertical pane positions 
            if hasattr(self.app, 'main_vertical_pane'):
                panes = self.app.main_vertical_pane.panes()
                if len(panes) >= 2:
                    # Main content area gets most of the space (600px)
                    self.app.main_vertical_pane.sashpos(0, 600)
                if len(panes) >= 3:
                    # Bottom log area gets 200px
                    self.app.main_vertical_pane.sashpos(1, 800)
        except Exception as e:
            print(f"Error setting initial pane positions: {e}")

    def _create_source_tree_section(self):
        """Create the source tree section."""
        source_tree_outer_frame = ctk.CTkFrame(self.app.main_horizontal_pane, corner_radius=self.app.current_corner_radius)
        source_tree_outer_frame.grid_rowconfigure(1, weight=1)
        source_tree_outer_frame.grid_columnconfigure(0, weight=1)
        
        # Store reference for theme application
        self.app.source_tree_frame = source_tree_outer_frame
        
        # Header frame for title and Show All button
        source_header_frame = ctk.CTkFrame(source_tree_outer_frame, fg_color="transparent")
        source_header_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        source_header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(source_header_frame, 
                    text="Source Folder Structure", 
                    image=self.app.theme_manager.get_icon_image('folder_closed'),
                    compound="left",
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # Show All button moved to source tree section
        self.app.show_all_btn = ctk.CTkButton(
            source_header_frame,
            text="Show All",
            image=self.app.theme_manager.get_icon_image('info'),
            width=90,
            height=28,
            command=self._show_all_sequences,
            font=ctk.CTkFont(size=12)
        )
        self.app.show_all_btn.grid(row=0, column=2, padx=(5,0), pady=0, sticky="e")
        
        self.app.source_tree = ttk.Treeview(source_tree_outer_frame, columns=("type", "size"), selectmode="browse")
        self.app.source_tree.heading("#0", text=f"{self.app.theme_manager.get_icon_text('folder_open')}  Name", anchor="w")
        self.app.source_tree.heading("type", text="Type", anchor="w")
        self.app.source_tree.heading("size", text="Size", anchor="w")
        self.app.source_tree.column("#0", stretch=tk.YES, minwidth=150)
        self.app.source_tree.column("type", width=80, stretch=tk.NO, anchor="center")
        self.app.source_tree.column("size", width=80, stretch=tk.NO, anchor="e")
        self.app.source_tree.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Bind events for folder expansion and selection
        self.app.source_tree.bind("<<TreeviewOpen>>", self._on_source_tree_open)
        self.app.source_tree.bind("<<TreeviewClose>>", self._on_source_tree_close)
        self.app.source_tree.bind("<<TreeviewSelect>>", self.app.tree_manager.on_source_tree_selection)
        
        # Add to horizontal pane
        self.app.main_horizontal_pane.add(source_tree_outer_frame, weight=1)

    def _create_preview_section(self):
        """Create the preview section with improved layout and enhanced controls."""
        preview_outer_frame = ctk.CTkFrame(self.app.main_horizontal_pane, corner_radius=self.app.current_corner_radius)
        preview_outer_frame.grid_rowconfigure(2, weight=1)  # Treeview gets weight
        preview_outer_frame.grid_rowconfigure(3, weight=0)  # Horizontal scrollbar
        preview_outer_frame.grid_rowconfigure(4, weight=0)  # Action buttons
        preview_outer_frame.grid_rowconfigure(5, weight=0)  # Info display
        preview_outer_frame.grid_columnconfigure(0, weight=1)

        # Store reference for theme application
        self.app.preview_frame = preview_outer_frame

        # Title and controls header
        header_frame = ctk.CTkFrame(preview_outer_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        header_frame.grid_columnconfigure(4, weight=1)  # Middle space for alignment

        ctk.CTkLabel(header_frame, 
                    text="Preview & Actions", 
                    image=self.app.theme_manager.get_icon_image('sequence'),
                    compound="left",
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=(0,15), pady=0, sticky="w")

        # Sort controls - better aligned
        sort_label = ctk.CTkLabel(header_frame, 
                                 text="Sort:",
                                 image=self.app.theme_manager.get_icon_image('refresh'),
                                 compound="left")
        sort_label.grid(row=0, column=1, padx=(0,5), pady=0, sticky="w")
        
        self.app.sort_menu = ctk.CTkOptionMenu(header_frame, values=["Filename", "Task", "Asset", "Destination", "Type"],
                                              command=self._on_sort_change,
                                              width=100,
                                              height=28,
                                              font=ctk.CTkFont(size=12))
        self.app.sort_menu.grid(row=0, column=2, padx=(0,5), pady=0)
        
        # Sort direction button
        self.app.sort_direction_btn = ctk.CTkButton(
            header_frame,
            text="",
            image=self.app.theme_manager.get_icon_image('arrow_up'),
            width=30,
            height=28,
            command=self._toggle_sort_direction,
            font=ctk.CTkFont(size=14)
        )
        self.app.sort_direction_btn.grid(row=0, column=3, padx=(0,15), pady=0)
        
        # Filter controls moved to header row next to sort controls
        filter_label = ctk.CTkLabel(header_frame, 
                                   text="Filter:",
                                   image=self.app.theme_manager.get_icon_image('info'),
                                   compound="left")
        filter_label.grid(row=0, column=4, padx=(15,2), pady=0, sticky="e")

        self.app.filter_combo = ctk.CTkComboBox(
            header_frame,
            values=["All", "Sequences", "Files"],
            command=self._on_filter_change,
            width=100,
            height=28
        )
        self.app.filter_combo.grid(row=0, column=5, padx=(0,15), pady=0, sticky="w")
        self.app.filter_combo.set("All")

        # Selection controls moved to top right - as indicated by red arrows
        select_all_seq_btn = ctk.CTkButton(
            header_frame,
            text=f"{self.app.theme_manager.get_icon_text('sequence')}  Select Sequences",
            command=self._select_all_sequences,
            width=160,
            height=28
        )
        select_all_seq_btn.grid(row=0, column=6, padx=5, pady=0)

        select_all_files_btn = ctk.CTkButton(
            header_frame,
            text=f"{self.app.theme_manager.get_icon_text('file')}  Select Files",
            command=self._select_all_files,
            width=130,
            height=28
        )
        select_all_files_btn.grid(row=0, column=7, padx=5, pady=0)

        clear_selection_btn = ctk.CTkButton(
            header_frame,
            text=f"{self.app.theme_manager.get_icon_text('error')}  Clear",
            command=self._clear_selection,
            width=90,
            height=28
        )
        clear_selection_btn.grid(row=0, column=8, padx=5, pady=0)

        self.app.batch_edit_btn = ctk.CTkButton(
            header_frame,
            text=f"{self.app.theme_manager.get_icon_text('settings')}  Batch Edit",
            command=self._open_batch_edit_dialog,
            width=110,
            height=28
        )
        self.app.batch_edit_btn.grid(row=0, column=9, padx=5, pady=0)

        # Selection stats label in second row (simplified layout)
        stats_frame = ctk.CTkFrame(preview_outer_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")
        stats_frame.grid_columnconfigure(0, weight=1)

        self.app.selection_stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        self.app.selection_stats_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        # Preview tree with enhanced columns and clickable headers
        # Reordered columns: filename, task, asset, new_path, tags (tags moved to end)
        self.app.preview_tree_columns = ("filename", "task", "asset", "new_path", "tags")
        self.app.preview_tree = ttk.Treeview(preview_outer_frame, columns=self.app.preview_tree_columns, show="tree headings", selectmode="extended")
        
        self.app.preview_tree.heading("#0", text="☐")  # For checkbox text via item's text property
        self.app.preview_tree.heading("filename", text="📁 File/Sequence Name", command=lambda: self._on_column_click("filename"))
        self.app.preview_tree.heading("task", text="⚙️ Task", command=lambda: self._on_column_click("task"))  # Editable
        self.app.preview_tree.heading("asset", text="🎨 Asset", command=lambda: self._on_column_click("asset"))  # Editable
        self.app.preview_tree.heading("new_path", text="📂 New Destination Path", command=lambda: self._on_column_click("new_path"))
        self.app.preview_tree.heading("tags", text="ℹ️ Matched Tags", command=lambda: self._on_column_click("type"))  # Moved to last

        # Improved column sizing for better usability
        self.app.preview_tree.column("#0", width=40, stretch=tk.NO, anchor="center", minwidth=30)  # Checkbox column
        self.app.preview_tree.column("filename", width=200, stretch=tk.NO, minwidth=150)
        self.app.preview_tree.column("task", width=80, stretch=tk.NO, minwidth=60) 
        self.app.preview_tree.column("asset", width=80, stretch=tk.NO, minwidth=60)
        self.app.preview_tree.column("new_path", width=350, stretch=tk.YES, minwidth=200)  # This stretches
        self.app.preview_tree.column("tags", width=150, stretch=tk.NO, minwidth=100)  # Tags column

        self.app.preview_tree.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.app.preview_tree.bind("<<TreeviewSelect>>", self._on_tree_selection_change)
        
        # Add right-click context menu
        self.app.preview_tree.bind("<Button-3>", self._show_context_menu)  # Right-click

        # Horizontal Scrollbar for Preview Tree (improved)
        preview_h_scrollbar = ttk.Scrollbar(preview_outer_frame, orient='horizontal', command=self.app.preview_tree.xview)
        self.app.preview_tree.configure(xscrollcommand=preview_h_scrollbar.set)
        preview_h_scrollbar.grid(row=3, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")

        # Vertical Scrollbar for Preview Tree
        preview_v_scrollbar = ttk.Scrollbar(preview_outer_frame, orient='vertical', command=self.app.preview_tree.yview)
        self.app.preview_tree.configure(yscrollcommand=preview_v_scrollbar.set)
        preview_v_scrollbar.grid(row=2, column=1, padx=(0,5), pady=5, sticky="ns")
        
        # Update the grid configuration to accommodate the vertical scrollbar
        preview_outer_frame.grid_columnconfigure(1, weight=0)

        # Action Buttons (within preview_outer_frame)
        action_buttons_bottom_frame = ctk.CTkFrame(preview_outer_frame, fg_color="transparent")
        action_buttons_bottom_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=(5,0), sticky="ew")

        self.app.copy_selected_btn = ctk.CTkButton(
            action_buttons_bottom_frame, 
            text="Copy Selected", 
            image=self.app.theme_manager.get_icon_image('success'),
            command=self.app.file_operations_manager.on_copy_selected_click, 
            state="disabled",
            corner_radius=self.app.current_corner_radius
        )
        self.app.copy_selected_btn.pack(side="left", padx=(0,5))
        self.app.accent_widgets.append(self.app.copy_selected_btn)

        self.app.move_selected_btn = ctk.CTkButton(
            action_buttons_bottom_frame, 
            text="Move Selected", 
            image=self.app.theme_manager.get_icon_image('warning'),
            command=self.app.file_operations_manager.on_move_selected_click, 
            state="disabled",
            corner_radius=self.app.current_corner_radius
        )
        self.app.move_selected_btn.pack(side="left", padx=5)
        self.app.accent_widgets.append(self.app.move_selected_btn)

        # Information Display (within preview_outer_frame)
        info_display_bottom_frame = ctk.CTkFrame(preview_outer_frame, corner_radius=self.app.current_corner_radius, height=60)
        info_display_bottom_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        info_display_bottom_frame.pack_propagate(False)  # Prevent shrinking
        ctk.CTkLabel(info_display_bottom_frame, 
                    text="Details of selected item - Coming Soon!",
                    image=self.app.theme_manager.get_icon_image('info'),
                    compound="left").pack(padx=5, pady=5, anchor="nw")
        
        # Add to horizontal pane
        self.app.main_horizontal_pane.add(preview_outer_frame, weight=3)  # Give more weight to preview area

    def _on_sort_change(self, value):
        """Handle sort column change."""
        column_map = {
            "Filename": "filename",
            "Task": "task", 
            "Asset": "asset",
            "Destination": "destination",
            "Type": "type"
        }
        column = column_map.get(value, "filename")
        self.app.tree_manager.set_sort_order(column, self.app.tree_manager.sort_reverse)

    def _toggle_sort_direction(self):
        """Toggle sort direction."""
        reverse = not self.app.tree_manager.sort_reverse
        self.app.tree_manager.set_sort_order(self.app.tree_manager.current_sort_column, reverse)
        
        # Update button image
        arrow_image = self.app.theme_manager.get_icon_image('arrow_down') if reverse else self.app.theme_manager.get_icon_image('arrow_up')
        self.app.sort_direction_btn.configure(image=arrow_image)

    def _on_filter_change(self, value):
        """Handle filter change with improved debugging."""
        print(f"[WIDGET_FACTORY_DEBUG] Filter change requested: {value}")
        filter_map = {
            "All": "all",
            "Sequences": "sequences", 
            "Files": "files"
        }
        filter_type = filter_map.get(value, "all")
        print(f"[WIDGET_FACTORY_DEBUG] Mapped to filter type: {filter_type}")
        self.app.tree_manager.set_filter(filter_type)

    def _on_column_click(self, column):
        """Handle column header clicks for sorting."""
        print(f"[WIDGET_FACTORY_DEBUG] Column clicked: {column}")
        self.app.tree_manager.sort_by_column(column)

    def _show_all_sequences(self):
        """Show all sequences by clearing folder filter."""
        print(f"[WIDGET_FACTORY_DEBUG] Show All button clicked")
        self.app.tree_manager.clear_source_folder_filter()
        
        # Update UI to reflect "show all" state
        if hasattr(self.app, 'source_tree'):
            self.app.source_tree.selection_remove(self.app.source_tree.selection())

    def _select_all_sequences(self):
        """Select all sequence items."""
        self.app.tree_manager.select_all_sequences()

    def _select_all_files(self):
        """Select all file items."""
        self.app.tree_manager.select_all_files()

    def _clear_selection(self):
        """Clear all selections."""
        self.app.tree_manager.clear_selection()

    def _on_tree_selection_change(self, event=None):
        """Handle tree selection changes."""
        # Update action button states
        self.app.tree_manager.update_action_button_states()
        
        # Update selection stats
        stats = self.app.tree_manager.get_selection_stats()
        stats_text = f"Selected: {stats['total']} items ({stats['sequences']} sequences, {stats['files']} files)"
        self.app.selection_stats_label.configure(text=stats_text)
        
        # Enable/disable batch edit button - check if it exists first
        has_selection = stats['total'] > 0
        if hasattr(self.app, 'batch_edit_btn'):  # Ensure batch_edit_btn exists before configuring
            self.app.batch_edit_btn.configure(state="normal" if has_selection else "disabled")

    def _show_context_menu(self, event):
        """Show right-click context menu with restored options and robustness."""
        # Ensure preview_tree exists before creating a menu for it
        if not hasattr(self.app, 'preview_tree'):
            print("Error: preview_tree not found on app instance for context menu.")
            return
        
        context_menu = tk.Menu(self.app.preview_tree, tearoff=0)  # Correctly parented to preview_tree
        
        has_selection = False
        stats = {'total': 0, 'sequences': 0, 'files': 0}  # Default stats

        if hasattr(self.app, 'tree_manager') and hasattr(self.app.tree_manager, 'get_selection_stats'):
            stats = self.app.tree_manager.get_selection_stats()
            has_selection = stats['total'] > 0
        else:
            print("Warning: tree_manager or get_selection_stats not available for context menu.")

        if has_selection:
            if hasattr(self, '_open_batch_edit_dialog'):
                context_menu.add_command(
                    label=f"Batch Edit ({stats['total']} items)",
                    command=self._open_batch_edit_dialog
                )
            context_menu.add_separator()

            can_copy_move = False
            if hasattr(self.app, 'selected_destination_folder'):
                can_copy_move = bool(self.app.selected_destination_folder.get())

            if hasattr(self.app, 'file_operations_manager'):
                if hasattr(self.app.file_operations_manager, 'on_copy_selected_click'):
                    context_menu.add_command(
                        label="Copy Selected",
                        command=self.app.file_operations_manager.on_copy_selected_click,
                        state="normal" if can_copy_move else "disabled"
                    )
                if hasattr(self.app.file_operations_manager, 'on_move_selected_click'):
                    context_menu.add_command(
                        label="Move Selected", 
                        command=self.app.file_operations_manager.on_move_selected_click,
                        state="normal" if can_copy_move else "disabled"
                    )
            else:
                print("Warning: file_operations_manager not available for context menu copy/move.")
        else:
            context_menu.add_command(label="No items selected", state="disabled")
        
        context_menu.add_separator()
        
        if hasattr(self, '_select_all_sequences'):
            context_menu.add_command(label="Select All Sequences", command=self._select_all_sequences)
        if hasattr(self, '_select_all_files'):
            context_menu.add_command(label="Select All Files", command=self._select_all_files)
        if hasattr(self, '_clear_selection'):
            context_menu.add_command(label="Clear Selection", command=self._clear_selection)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def _open_batch_edit_dialog(self):
        """Open the batch edit dialog for selected items."""
        selected_items = self.app.tree_manager.get_selected_items()
        
        if not selected_items:
            self.app.status_manager.add_log_message("No items selected for batch editing", "WARNING")
            return
        
        # Import and create batch edit dialog
        from .batch_edit_dialog import BatchEditDialog
        
        def on_apply_callback(items, changes):
            """Handle batch edit changes."""
            self._apply_batch_changes(items, changes)
        
        # Create and show dialog
        dialog = BatchEditDialog(self.app, selected_items, on_apply_callback)

    def _open_vlc_player_window(self, media_path: str):
        """Opens the VLC player window for the given media path."""
        if not (hasattr(self.app, 'vlc_module_available') and self.app.vlc_module_available):
            messagebox.showerror("VLC Error", "VLC module is not available (flag check). Cannot open player.")
            return

        # Check if an instance already exists and manage it
        if hasattr(self.app, 'vlc_player_window_instance') and \
           self.app.vlc_player_window_instance and \
           self.app.vlc_player_window_instance.winfo_exists():
            self.app.vlc_player_window_instance.lift() # Bring to front
            if self.app.vlc_player_window_instance.media_path != media_path:
                self.app.vlc_player_window_instance.load_media(media_path) # Load new media
            return

        # Create a new player window instance
        # Assumes self.app.VLCPlayerWindow holds the class, set in app_gui.py's __init__
        if hasattr(self.app, 'VLCPlayerWindow'):
            self.app.vlc_player_window_instance = self.app.VLCPlayerWindow(self.app, media_path)
        else:
            messagebox.showerror("VLC Error", "VLCPlayerWindow class not found on app instance. VLC might not have loaded correctly.")

    def _apply_batch_changes(self, items, changes):
        """Apply batch edit changes to the selected items."""
        # This method will update the item data and regenerate destination paths
        print(f"Applying batch changes to {len(items)} items: {changes}")
        
        # Track which items were changed
        changed_items = []
        
        for item in items:
            item_changed = False
            normalized_parts = item.get('normalized_parts', {}).copy()
            tags = item.get('tags', {}).copy()
            
            # Apply changes to both normalized parts and tags consistently
            for field, value in changes.items():
                if field == 'custom_path':
                    continue  # Handle custom path separately
                    
                if field in ['shot', 'asset', 'task', 'resolution', 'version', 'stage']:
                    old_value = normalized_parts.get(field, '')
                    if value != old_value:
                        normalized_parts[field] = value
                        # Update all possible asset field variations for consistency
                        if field == 'asset':
                            tags['asset'] = value
                            tags['asset_name'] = value  # Also update asset_name
                            tags['asset_type'] = value  # Also update asset_type
                        else:
                            tags[field] = value
                        item_changed = True
                        print(f"[BATCH_EDIT] Updated {field} from '{old_value}' to '{value}' for {item.get('filename', 'unknown')}")

            if item_changed:
                # Update normalized parts and tags
                item['normalized_parts'] = normalized_parts
                item['tags'] = tags
                
                # Regenerate destination path if no custom path override
                if 'custom_path' not in changes:
                    # Use proper path generation logic
                    try:
                        # Get current profile and its rules
                        profile_name = self.app.selected_profile_name.get()
                        if self.app.normalizer and profile_name:
                            # Get profile rules from normalizer
                            profile_data = self.app.normalizer.all_profiles_data.get(profile_name, [])
                            if isinstance(profile_data, list):
                                profile_rules = profile_data
                            elif isinstance(profile_data, dict) and 'rules' in profile_data:
                                profile_rules = profile_data['rules']
                            else:
                                profile_rules = []
                            
                            # Get root output directory
                            root_output_dir = self.app.selected_destination_folder.get()
                            if not root_output_dir:
                                root_output_dir = os.path.join(os.getcwd(), "output")
                            
                            # Check if this is a sequence or a file
                            item_type = item.get('type', 'file').lower()
                            filename = item.get('filename', 'unknown.file')
                            
                            if item_type == 'sequence':
                                # Handle sequence regeneration with updated tags
                                from ..mapping_utils.create_sequence_mapping import create_sequence_mapping
                                
                                # Get patterns from config
                                config = self.app.normalizer.mapping_generator.config
                                if config:
                                    p_shot = self.app.normalizer.mapping_generator.shot_patterns
                                    p_task = self.app.normalizer.mapping_generator.task_patterns
                                    p_version = self.app.normalizer.mapping_generator.version_patterns
                                    p_resolution = self.app.normalizer.mapping_generator.resolution_patterns
                                    p_asset = config.get("assetPatterns", [])
                                    p_stage = config.get("stagePatterns", [])
                                else:
                                    p_shot = p_task = p_version = p_resolution = p_asset = p_stage = None
                                
                                # Create sequence data with updated information
                                sequence_info = item.get('sequence_info', {})
                                
                                sequence_dict = {
                                    "files": sequence_info.get('files', []),
                                    "base_name": sequence_info.get('base_name', filename.replace('.####.', '_').split('.')[0]),
                                    "suffix": sequence_info.get('suffix', ''),
                                    "directory": sequence_info.get('directory', ''),
                                    "frame_range": sequence_info.get('frame_range', ''),
                                    "frame_count": sequence_info.get('frame_count', 0),
                                    "frame_numbers": sequence_info.get('frame_numbers', [])
                                }
                                
                                # Create profile object for sequence mapping
                                profile_object = {
                                    "name": profile_name,
                                    "rules": profile_rules
                                }
                                
                                # Generate new sequence mapping with the updated base name
                                new_sequence_proposal = create_sequence_mapping(
                                    sequence=sequence_dict,
                                    profile=profile_object,
                                    root_output_dir=root_output_dir,
                                    original_base_name=sequence_dict["base_name"],
                                    p_shot=p_shot,
                                    p_task=p_task,
                                    p_version=p_version,
                                    p_resolution=p_resolution,
                                    p_asset=p_asset,
                                    p_stage=p_stage,
                                    override_extracted_values=normalized_parts  # Pass the updated values including shot
                                )
                                
                                if new_sequence_proposal:
                                    new_target_path = new_sequence_proposal.get("targetPath")
                                    if new_target_path:
                                        item['new_destination_path'] = new_target_path
                                        print(f"[BATCH_EDIT] Regenerated sequence path for {filename}: {new_target_path}")
                                    else:
                                        print(f"[BATCH_EDIT] Failed to generate sequence path for {filename}")
                                else:
                                    print(f"[BATCH_EDIT] No sequence proposal generated for {filename}")
                            
                            else:
                                # Handle individual file regeneration with updated tags
                                from ..mapping_utils.generate_simple_target_path import generate_simple_target_path
                                
                                # Extract values from updated normalized parts
                                parsed_shot = normalized_parts.get('shot')
                                parsed_task = normalized_parts.get('task')
                                parsed_asset = normalized_parts.get('asset')
                                parsed_stage = normalized_parts.get('stage')
                                parsed_version = normalized_parts.get('version')
                                parsed_resolution = normalized_parts.get('resolution')
                                
                                # Generate new target path with updated values including shot
                                path_result = generate_simple_target_path(
                                    root_output_dir=root_output_dir,
                                    profile_rules=profile_rules,
                                    filename=filename,
                                    parsed_shot=parsed_shot,
                                    parsed_task=parsed_task,
                                    parsed_asset=parsed_asset,
                                    parsed_stage=parsed_stage,
                                    parsed_version=parsed_version,
                                    parsed_resolution=parsed_resolution
                                )
                                
                                new_target_path = path_result.get("target_path")
                                if new_target_path:
                                    item['new_destination_path'] = new_target_path
                                    print(f"[BATCH_EDIT] Regenerated file path for {filename}: {new_target_path}")
                                else:
                                    # Handle ambiguous or failed path generation
                                    if path_result.get("ambiguous_match"):
                                        print(f"[BATCH_EDIT] Ambiguous path match for {filename}")
                                        # Keep original path for ambiguous matches
                                    else:
                                        print(f"[BATCH_EDIT] Failed to generate path for {filename}")
                        else:
                            print(f"[BATCH_EDIT] No normalizer or profile available for path regeneration")
                    
                    except Exception as e:
                        print(f"[BATCH_EDIT] Error regenerating path for {item.get('filename', 'unknown')}: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # Use custom path override
                    filename = item.get('filename', '')
                    item['new_destination_path'] = os.path.join(changes['custom_path'], filename)
                
                changed_items.append(item)
        
        # Refresh the tree display to show changes
        if changed_items:
            # Update the tree display with modified data
            self.app.tree_manager._refresh_preview_tree()
            
            self.app.status_manager.add_log_message(
                f"Applied batch changes to {len(changed_items)} items", 
                "INFO"
            )
        else:
            self.app.status_manager.add_log_message(
                "No items were changed by batch edit operation", 
                "INFO"
            )

    def _create_progress_panel_section(self):
        """Create the progress panel as a detached popup window."""
        # Create the progress panel as a popup window (not embedded in main UI)
        self.app.progress_panel = ProgressPanel(self.app)
        
        # Note: No container needed since it's now a popup window
        # The panel will be shown/hidden by status_manager when needed

        # Create file operations progress panel (also a popup window system)
        from .file_operations_progress import FileOperationsProgressPanel
        
        # Create file operations progress panel
        self.app.file_operations_progress = FileOperationsProgressPanel(self.app)

    def _create_bottom_sections(self):
        """Create bottom sections (status and log) in a resizable layout."""
        # Create a container for bottom sections
        bottom_container = ctk.CTkFrame(self.app.main_vertical_pane)
        bottom_container.grid_columnconfigure(0, weight=1)
        bottom_container.grid_rowconfigure(0, weight=0)  # Status frame
        bottom_container.grid_rowconfigure(1, weight=1)  # Log frame
        
        # Status frame
        self._create_status_frame(bottom_container)
        
        # Log frame  
        self._create_log_frame(bottom_container)
        
        # Add to main vertical pane (removed minsize parameter)
        self.app.main_vertical_pane.add(bottom_container, weight=1)

    def _create_status_frame(self, parent):
        """Create the status frame."""
        status_frame = ctk.CTkFrame(parent, corner_radius=0)
        status_frame.grid(row=0, column=0, padx=0, pady=(5,0), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)  # Allow horizontal expansion

        # Remove the old progress bar that was causing issues
        # self.app.progress_bar = ctk.CTkProgressBar(status_frame, orientation="horizontal", mode="indeterminate", corner_radius=self.app.current_corner_radius, height=20)
        # Progress bar will be gridded when needed

        self.app.status_label = ctk.CTkLabel(status_frame, text="Welcome to Clean Incomings! Select a profile and folders to begin.", anchor="w")
        self.app.status_label.grid(row=1, column=0, padx=10, pady=(5,10), sticky="ew") 
        
        # Add transfer details label for speed/ETA information
        self.app.transfer_details_label = ctk.CTkLabel(status_frame, text="", anchor="w", font=("Segoe UI", 10))
        self.app.transfer_details_label.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")

    def _create_log_frame(self, parent):
        """Create the collapsible log frame."""
        log_container = ctk.CTkFrame(parent, corner_radius=self.app.current_corner_radius)
        log_container.grid(row=1, column=0, padx=10, pady=(5,10), sticky="nsew")
        log_container.grid_rowconfigure(1, weight=1)  # Log content expands
        log_container.grid_columnconfigure(0, weight=1)

        # Store reference for theme application
        self.app.log_frame = log_container

        # Log header with toggle button
        log_header_frame = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header_frame.grid(row=0, column=0, padx=5, pady=(5,0), sticky="ew")
        log_header_frame.grid_columnconfigure(1, weight=1)

        # Toggle button
        self.app.log_toggle_btn = ctk.CTkButton(
            log_header_frame,
            text="",
            image=self.app.theme_manager.get_icon_image('arrow_down'),
            width=30,
            height=25,
            command=self._toggle_log_panel,
            corner_radius=self.app.current_corner_radius,
            font=ctk.CTkFont(size=12)
        )
        self.app.log_toggle_btn.grid(row=0, column=0, padx=(0,10), pady=0, sticky="w")

        # Log title
        log_title_label = ctk.CTkLabel(
            log_header_frame,
            text="Application Logs",
            image=self.app.theme_manager.get_icon_image('info'),
            compound="left",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        log_title_label.grid(row=0, column=1, pady=0, sticky="ew")

        # Clear log button
        clear_log_btn = ctk.CTkButton(
            log_header_frame,
            text=f"{self.app.theme_manager.get_icon_text('error')}  Clear",
            width=90,
            height=25,
            command=self._clear_log,
            corner_radius=self.app.current_corner_radius,
            font=ctk.CTkFont(size=10)
        )
        clear_log_btn.grid(row=0, column=2, padx=(10,0), pady=0, sticky="e")

        # Log content frame (collapsible)
        self.app.log_content_frame = ctk.CTkFrame(log_container, corner_radius=self.app.current_corner_radius)
        self.app.log_content_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.app.log_content_frame.grid_rowconfigure(0, weight=1)
        self.app.log_content_frame.grid_columnconfigure(0, weight=1)

        # Actual log textbox
        self.app.log_textbox = ctk.CTkTextbox(
            self.app.log_content_frame, 
            wrap='word', 
            state='disabled', 
            corner_radius=self.app.current_corner_radius
        )
        self.app.log_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Initialize collapsed state - default to collapsed
        self.app.log_panel_collapsed = True
        # Start with log panel collapsed
        self.app.log_content_frame.grid_remove()
        self.app.log_toggle_btn.configure(image=self.app.theme_manager.get_icon_image('arrow_up'))

    def _toggle_log_panel(self):
        """Toggle the log panel visibility."""
        if self.app.log_panel_collapsed:
            # Expand log panel
            self.app.log_content_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
            self.app.log_toggle_btn.configure(image=self.app.theme_manager.get_icon_image('arrow_down'))
            self.app.log_panel_collapsed = False
        else:
            # Collapse log panel
            self.app.log_content_frame.grid_remove()
            self.app.log_toggle_btn.configure(image=self.app.theme_manager.get_icon_image('arrow_up'))
            self.app.log_panel_collapsed = True

    def _clear_log(self):
        """Clear the log textbox."""
        try:
            self.app.log_textbox.configure(state='normal')
            self.app.log_textbox.delete('1.0', 'end')
            self.app.log_textbox.configure(state='disabled')
            self.app.status_manager.add_log_message("Log cleared by user", "INFO")
        except Exception as e:
            print(f"Error clearing log: {e}")

    def _select_source_folder(self):
        """Handle source folder selection."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.app.selected_source_folder.set(folder_selected)
            self.app.status_label.configure(text=f"Source folder: {folder_selected}")
            # Trigger validation
            self._validate_folder_entries(None)

    def _select_destination_folder(self):
        """Handle destination folder selection."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.app.selected_destination_folder.set(folder_selected)
            self.app.status_label.configure(text=f"Destination: {folder_selected}")
            self.app.tree_manager.update_action_button_states()  # Update button states when destination changes
            # Trigger validation
            self._validate_folder_entries(None)

    def _open_settings_window(self):
        """Open settings window with actual functionality."""
        print("Opening settings window...")
        
        # Check if settings window already exists
        if hasattr(self.app, 'settings_window') and self.app.settings_window.winfo_exists():
            self.app.settings_window.lift()  # Bring to front
            return
        
        # Create settings window
        self.app.settings_window = ctk.CTkToplevel(self.app)
        self.app.settings_window.title("Settings")
        self.app.settings_window.geometry("600x400")
        self.app.settings_window.resizable(True, True)
        
        # Make it stay on top but not modal
        self.app.settings_window.attributes('-topmost', True)
        self.app.settings_window.after(100, lambda: self.app.settings_window.attributes('-topmost', False))
        
        # Create main container
        main_frame = ctk.CTkFrame(self.app.settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Application Settings", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="w")
        
        # Create tabview for different settings categories
        tabview = ctk.CTkTabview(main_frame)
        tabview.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # General tab
        general_tab = tabview.add("General")
        general_tab.grid_columnconfigure(1, weight=1)
        
        # Appearance mode setting
        appearance_label = ctk.CTkLabel(general_tab, text="Appearance Mode:")
        appearance_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        appearance_var = tk.StringVar(value=self.app.settings.get("ui_state", {}).get("appearance_mode", "System"))
        appearance_combo = ctk.CTkComboBox(
            general_tab,
            values=["System", "Light", "Dark"],
            variable=appearance_var,
            command=self._on_appearance_change
        )
        appearance_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Color theme setting
        theme_label = ctk.CTkLabel(general_tab, text="Color Theme:")
        theme_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        theme_var = tk.StringVar(value=self.app.settings.get("ui_state", {}).get("color_theme", "blue"))
        theme_combo = ctk.CTkComboBox(
            general_tab,
            values=["blue", "green", "dark-blue"],
            variable=theme_var,
            command=self._on_theme_change
        )
        theme_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Advanced tab
        advanced_tab = tabview.add("Advanced")
        advanced_tab.grid_columnconfigure(1, weight=1)
        
        # Log panel default state
        log_label = ctk.CTkLabel(advanced_tab, text="Log Panel Default State:")
        log_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        log_var = tk.StringVar(value="Collapsed" if self.app.settings.get("ui_state", {}).get("log_panel_collapsed", True) else "Expanded")
        log_combo = ctk.CTkComboBox(
            advanced_tab,
            values=["Collapsed", "Expanded"],
            variable=log_var,
            command=lambda val: self._on_log_default_change(val)
        )
        log_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Thread Controls Section
        thread_frame = ctk.CTkFrame(advanced_tab)
        thread_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        thread_frame.grid_columnconfigure(1, weight=1)
        
        thread_title = ctk.CTkLabel(
            thread_frame, 
            text="Performance Settings", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        thread_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # Scan threads
        scan_thread_label = ctk.CTkLabel(thread_frame, text="Scan Threads:")
        scan_thread_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        scan_threads_current = getattr(self.app, 'current_scan_threads', 4)  # Read from app settings
        self.scan_threads_var = tk.IntVar(value=scan_threads_current)
        scan_thread_spinner = ctk.CTkFrame(thread_frame)
        scan_thread_spinner.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        scan_thread_entry = ctk.CTkEntry(
            scan_thread_spinner, 
            textvariable=self.scan_threads_var,
            width=60,
            justify="center"
        )
        scan_thread_entry.pack(side="left", padx=2)
        
        scan_minus_btn = ctk.CTkButton(
            scan_thread_spinner,
            text="-",
            width=30,
            command=lambda: self._adjust_thread_count(self.scan_threads_var, -1)
        )
        scan_minus_btn.pack(side="left", padx=2)
        
        scan_plus_btn = ctk.CTkButton(
            scan_thread_spinner,
            text="+",
            width=30,
            command=lambda: self._adjust_thread_count(self.scan_threads_var, 1)
        )
        scan_plus_btn.pack(side="left", padx=2)
        
        # Copy/Move threads
        copy_thread_label = ctk.CTkLabel(thread_frame, text="Copy/Move Threads:")
        copy_thread_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        copy_threads_current = getattr(self.app, 'current_copy_threads', 2)  # Read from app settings
        self.copy_threads_var = tk.IntVar(value=copy_threads_current)
        copy_thread_spinner = ctk.CTkFrame(thread_frame)
        copy_thread_spinner.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        copy_thread_entry = ctk.CTkEntry(
            copy_thread_spinner, 
            textvariable=self.copy_threads_var,
            width=60,
            justify="center"
        )
        copy_thread_entry.pack(side="left", padx=2)
        
        copy_minus_btn = ctk.CTkButton(
            copy_thread_spinner,
            text="-",
            width=30,
            command=lambda: self._adjust_thread_count(self.copy_threads_var, -1)
        )
        copy_minus_btn.pack(side="left", padx=2)
        
        copy_plus_btn = ctk.CTkButton(
            copy_thread_spinner,
            text="+",
            width=30,
            command=lambda: self._adjust_thread_count(self.copy_threads_var, 1)
        )
        copy_plus_btn.pack(side="left", padx=2)
        
        # Thread info
        thread_info = ctk.CTkLabel(
            thread_frame,
            text="Higher thread counts can improve performance but may use more system resources.\nRecommended: 2-8 scan threads, 1-4 copy threads.",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40"),
            justify="left"
        )
        thread_info.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Bind thread count changes
        self.scan_threads_var.trace('w', self._on_scan_threads_change)
        self.copy_threads_var.trace('w', self._on_copy_threads_change)
        
        # Patterns Editor tab
        patterns_tab = tabview.add("Patterns Editor")
        patterns_tab.grid_columnconfigure(0, weight=1)
        patterns_tab.grid_rowconfigure(1, weight=1)
        
        # Simple button to open patterns editor
        patterns_header = ctk.CTkFrame(patterns_tab)
        patterns_header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        patterns_header.grid_columnconfigure(1, weight=1)
        
        patterns_title = ctk.CTkLabel(
            patterns_header,
            text="🎨 Patterns Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        patterns_title.grid(row=0, column=0, sticky="w")
        
        patterns_info = ctk.CTkFrame(patterns_tab)
        patterns_info.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        patterns_description = ctk.CTkLabel(
            patterns_info,
            text="""Configure pattern recognition rules for:
            
• Shot Patterns - Regex patterns for shot identification (e.g., SC\\d{3}, sh\\d{3})
• Task Patterns - Task categories with their associated keywords/aliases  
• Resolution Patterns - Resolution identifiers (e.g., 4k, 2k, hd, uhd)
• Version Patterns - Version number patterns (e.g., v\\d{3}, ver\\d{3})
• Asset Patterns - Asset type keywords (e.g., hero, vehicle, character, prop)
• Stage Patterns - Production stage keywords (e.g., PREVIZ, ANIM, LAYOUT, COMP)

Click the button below to open the full patterns editor in a separate window.""",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        patterns_description.pack(padx=20, pady=20, anchor="nw")
        
        open_patterns_btn = ctk.CTkButton(
            patterns_info,
            text="🎨 Open Patterns Editor",
            command=self._open_patterns_editor,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        open_patterns_btn.pack(pady=20)
        
        # Profiles Editor tab
        profiles_tab = tabview.add("Profiles Editor")
        profiles_tab.grid_columnconfigure(0, weight=1)
        profiles_tab.grid_rowconfigure(1, weight=1)
        
        # Simple button to open profiles editor
        profiles_header = ctk.CTkFrame(profiles_tab)
        profiles_header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        profiles_header.grid_columnconfigure(1, weight=1)
        
        profiles_title = ctk.CTkLabel(
            profiles_header,
            text="📁 Profiles Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        profiles_title.grid(row=0, column=0, sticky="w")
        
        profiles_info = ctk.CTkFrame(profiles_tab)
        profiles_info.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        profiles_description = ctk.CTkLabel(
            profiles_info,
            text="""Configure project profiles and folder structures:
            
• Create multiple profiles for different project types
• Define folder paths for organized output structure
• Assign pattern types to specific folders
• Customize how files are sorted and organized

Each profile contains folder rules that determine where different types
of files will be placed based on their detected patterns.

Click the button below to open the full profiles editor in a separate window.""",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        profiles_description.pack(padx=20, pady=20, anchor="nw")
        
        open_profiles_btn = ctk.CTkButton(
            profiles_info,
            text="📁 Open Profiles Editor",
            command=self._open_profiles_editor,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        open_profiles_btn.pack(pady=20)
        
        # About tab
        about_tab = tabview.add("About")
        
        about_text = """Clean Incomings - VFX Folder Normalizer

Version: 2.0.0
A modular Python GUI application for organizing VFX project files.

Features:
• Fast directory scanning with progress tracking
• Pattern-based file/sequence recognition
• Batch editing and path generation
• Customizable profiles and patterns
• Real-time preview and validation

Built with:
• Python 3.x
• CustomTkinter for modern UI
• Modular architecture for maintainability"""
        
        about_label = ctk.CTkLabel(
            about_tab, 
            text=about_text,
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        about_label.pack(padx=20, pady=20, anchor="nw")
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Reset to defaults button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_settings_to_defaults,
            width=120
        )
        reset_btn.grid(row=0, column=0, padx=5, pady=0, sticky="w")
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.app.settings_window.destroy,
            width=80
        )
        close_btn.grid(row=0, column=1, padx=5, pady=0, sticky="e")
        
        # Store references for updates
        self.app.settings_window.appearance_var = appearance_var
        self.app.settings_window.theme_var = theme_var
        self.app.settings_window.log_var = log_var
    
    def _on_appearance_change(self, value):
        """Handle appearance mode change."""
        ctk.set_appearance_mode(value)
        # Update settings
        if "ui_state" not in self.app.settings:
            self.app.settings["ui_state"] = {}
        self.app.settings["ui_state"]["appearance_mode"] = value
        self.app.settings_manager.save_current_state()
        self.app.status_manager.add_log_message(f"Appearance mode changed to: {value}", "INFO")
    
    def _on_theme_change(self, value):
        """Handle color theme change."""
        # Update settings
        if "ui_state" not in self.app.settings:
            self.app.settings["ui_state"] = {}
        self.app.settings["ui_state"]["color_theme"] = value
        self.app.settings_manager.save_current_state()
        self.app.status_manager.add_log_message(f"Color theme changed to: {value} (restart required for full effect)", "INFO")
    
    def _on_log_default_change(self, value):
        """Handle log panel default state change."""
        collapsed = value == "Collapsed"
        if "ui_state" not in self.app.settings:
            self.app.settings["ui_state"] = {}
        self.app.settings["ui_state"]["log_panel_collapsed"] = collapsed
        self.app.settings_manager.save_current_state()
        self.app.status_manager.add_log_message(f"Log panel default state changed to: {value}", "INFO")
    
    def _reset_settings_to_defaults(self):
        """Reset all settings to default values."""
        # Reset to default settings
        default_settings = self.app.settings_manager.default_settings.copy()
        self.app.settings = default_settings
        self.app.settings_manager.save_current_state()
        
        # Update the settings window controls
        if hasattr(self.app, 'settings_window') and self.app.settings_window.winfo_exists():
            self.app.settings_window.appearance_var.set(default_settings["ui_state"]["appearance_mode"])
            self.app.settings_window.theme_var.set(default_settings["ui_state"]["color_theme"])
            self.app.settings_window.log_var.set("Collapsed" if default_settings["ui_state"]["log_panel_collapsed"] else "Expanded")
        
        # Apply the defaults
        ctk.set_appearance_mode(default_settings["ui_state"]["appearance_mode"])
        
        self.app.status_manager.add_log_message("Settings reset to defaults", "INFO")

    def _validate_folder_entries(self, event):
        """Validate folder entries and update UI accordingly."""
        # Get current values
        source_path = self.app.selected_source_folder.get().strip()
        dest_path = self.app.selected_destination_folder.get().strip()
        
        # Validate source folder
        source_valid = os.path.isdir(source_path) if source_path else False
        
        # Validate destination folder
        dest_valid = os.path.isdir(dest_path) if dest_path else False
        
        # Update entry field appearance based on validity
        if hasattr(self.app, 'source_folder_entry'):
            if source_path and not source_valid:
                self.app.source_folder_entry.configure(border_color="red")
            else:
                # Reset to default by configuring without border_color parameter
                try:
                    # Get the default border color from theme
                    default_border = ("gray60", "gray30")  # CustomTkinter default
                    self.app.source_folder_entry.configure(border_color=default_border)
                except:
                    # If that fails, don't set border_color at all
                    pass
        
        if hasattr(self.app, 'dest_folder_entry'):
            if dest_path and not dest_valid:
                self.app.dest_folder_entry.configure(border_color="red")
            else:
                # Reset to default by configuring without border_color parameter
                try:
                    # Get the default border color from theme
                    default_border = ("gray60", "gray30")  # CustomTkinter default
                    self.app.dest_folder_entry.configure(border_color=default_border)
                except:
                    # If that fails, don't set border_color at all
                    pass
        
        # Update action button states
        if hasattr(self.app, 'tree_manager'):
            self.app.tree_manager.update_action_button_states()

    def _adjust_thread_count(self, var, delta):
        """Adjust thread count and update UI."""
        current = var.get()
        new_value = max(1, current + delta)
        var.set(new_value)
        self.app.status_manager.add_log_message(f"Thread count adjusted to: {new_value}", "INFO")

    def _on_scan_threads_change(self, *args):
        """Handle scan threads change."""
        new_value = self.scan_threads_var.get()
        self.app.current_scan_threads = new_value
        
        # Update the scanner's thread settings if available
        if hasattr(self.app, 'normalizer') and hasattr(self.app.normalizer, 'scanner'):
            self.app.normalizer.scanner.max_workers_local = new_value
            self.app.normalizer.scanner.max_workers_network = max(2, new_value // 2)  # Use half for network
        
        # Save settings
        current_settings = self.app.settings_manager.load_settings()
        current_settings["ui_state"]["scan_threads"] = new_value
        self.app.settings_manager.save_settings(current_settings)
        
        self.app.status_manager.add_log_message(f"Scan threads changed to: {new_value} (applied to scanner)", "INFO")

    def _on_copy_threads_change(self, *args):
        """Handle copy threads change."""
        new_value = self.copy_threads_var.get()
        self.app.current_copy_threads = new_value
        
        # BALANCED threading for 10GbE - good performance without system overload
        if new_value > 24:
            self.app.status_manager.add_log_message(
                f"⚠️ Warning: {new_value} copy threads may overwhelm the system. For 10GbE, 8-24 threads is optimal.", 
                "WARNING"
            )
        elif new_value > 16:
            self.app.status_manager.add_log_message(
                f"🚀 Excellent: {new_value} copy threads should provide great 10GbE performance.", 
                "INFO"
            )
        elif new_value > 8:
            self.app.status_manager.add_log_message(
                f"🚀 Good: {new_value} copy threads should work well for 10GbE networks.", 
                "INFO"
            )
        elif new_value > 4:
            self.app.status_manager.add_log_message(
                f"ℹ️ Info: {new_value} copy threads may work well for SMB/NAS operations.", 
                "INFO"
            )
        
        # Update the file operations manager's thread settings if available
        if hasattr(self.app, 'file_operations_manager'):
            # For BALANCED 10GbE operations, cap at 24 threads to prevent system overload
            effective_threads = min(new_value, 24)
            self.app.file_operations_manager.max_concurrent_transfers = effective_threads
            # Recreate thread pool with new size
            if hasattr(self.app.file_operations_manager, 'thread_pool'):
                self.app.file_operations_manager.thread_pool.shutdown(wait=False)
                import concurrent.futures
                self.app.file_operations_manager.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=effective_threads)
        
        # Save settings
        current_settings = self.app.settings_manager.load_settings()
        current_settings["ui_state"]["copy_threads"] = new_value
        self.app.settings_manager.save_settings(current_settings)
        
        print(f"Copy threads changed to: {new_value} (effective: {min(new_value, 24)} for BALANCED 10GbE)")

    def _on_patterns_saved(self, filename):
        """Handle patterns configuration saved."""
        self.app.status_manager.add_log_message(f"Patterns configuration saved: {filename}", "INFO")
        
        # Reload patterns in normalizer if available
        if hasattr(self.app, 'normalizer'):
            try:
                # Reload the normalizer's patterns using the correct method
                if hasattr(self.app.normalizer.mapping_generator, 'reload_patterns'):
                    self.app.normalizer.mapping_generator.reload_patterns()
                    
                    # Clear pattern cache to ensure fresh pattern matching
                    try:
                        from python.mapping_utils.pattern_cache import get_global_cache
                        cache = get_global_cache()
                        cache.clear()
                        self.app.status_manager.add_log_message("🧹 Pattern cache cleared", "INFO")
                    except Exception as cache_error:
                        print(f"Warning: Could not clear pattern cache: {cache_error}")
                    
                    self.app.status_manager.add_log_message("🔄 Patterns reloaded in normalizer", "INFO")
                else:
                    self.app.status_manager.add_log_message("Warning: Could not reload patterns - method not found", "WARNING")
            except Exception as e:
                self.app.status_manager.add_log_message(f"Warning: Could not reload patterns: {e}", "WARNING")

    def _on_profiles_saved(self, filename):
        """Handle profiles configuration saved."""
        self.app.status_manager.add_log_message(f"Profiles configuration saved: {filename}", "INFO")
        
        # Reload profile in normalizer if available
        if hasattr(self.app, 'normalizer'):
            try:
                # Reload profiles
                self.app.normalizer.load_profiles()
                self.app.status_manager.add_log_message("🔄 Profiles reloaded in normalizer", "INFO")
                
                # Update profile combobox if available
                if hasattr(self.app, 'profile_combobox'):
                    old_selection = self.app.selected_profile_name.get()
                    profile_names = list(self.app.normalizer.all_profiles_data.keys())
                    self.app.profile_combobox.configure(values=profile_names)
                    
                    # Restore selection if it still exists
                    if old_selection in profile_names:
                        self.app.profile_combobox.set(old_selection)
                    elif profile_names:
                        self.app.profile_combobox.set(profile_names[0])
                        self.app.selected_profile_name.set(profile_names[0])
                    
                    self.app.status_manager.add_log_message("📋 Profile combobox updated", "INFO")
                
            except Exception as e:
                self.app.status_manager.add_log_message(f"Warning: Could not reload profiles: {e}", "WARNING")

    def _on_source_tree_open(self, event):
        """Handle folder expansion in source tree - update icon to open folder."""
        selection = self.app.source_tree.selection()
        if selection:
            item_id = selection[0]
            # Get current text
            current_text = self.app.source_tree.item(item_id, "text")
            # Replace closed folder icon with open folder icon
            closed_icon = self.app.theme_manager.get_icon_text("folder_closed")
            open_icon = self.app.theme_manager.get_icon_text("folder_open")
            if closed_icon in current_text:
                new_text = current_text.replace(closed_icon, open_icon)
                self.app.source_tree.item(item_id, text=new_text)

    def _on_source_tree_close(self, event):
        """Handle folder collapse in source tree - update icon to closed folder."""
        selection = self.app.source_tree.selection()
        if selection:
            item_id = selection[0]
            # Get current text
            current_text = self.app.source_tree.item(item_id, "text")
            # Replace open folder icon with closed folder icon
            closed_icon = self.app.theme_manager.get_icon_text("folder_closed")
            open_icon = self.app.theme_manager.get_icon_text("folder_open")
            if open_icon in current_text:
                new_text = current_text.replace(open_icon, closed_icon)
                self.app.source_tree.item(item_id, text=new_text)

    def apply_theme_to_panels(self):
        """Apply theme colors with panel variations."""
        if hasattr(self.app, 'theme_manager'):
            self.app.theme_manager.apply_panel_colors()

    def _open_patterns_editor(self):
        """Open the patterns editor in a separate window"""
        try:
            # Close settings window first
            if hasattr(self.app, 'settings_window') and self.app.settings_window.winfo_exists():
                self.app.settings_window.destroy()
            
            # Import and create patterns editor window
            from .json_editors import PatternsEditorWindow
            
            # Check if editor is already open
            if hasattr(self.app, 'patterns_editor_window') and self.app.patterns_editor_window:
                try:
                    self.app.patterns_editor_window.show()
                    return
                except:
                    # Window was destroyed, create new one
                    pass
            
            # Create new patterns editor window
            self.app.patterns_editor_window = PatternsEditorWindow(
                config_dir=self.app._config_dir_path,
                on_save_callback=self._on_patterns_saved
            )
            
            self.app.status_manager.add_log_message("🎨 Patterns editor opened", "INFO")
            
        except Exception as e:
            self.app.status_manager.add_log_message(f"Error opening patterns editor: {e}", "ERROR")
            print(f"Error opening patterns editor: {e}")
            import traceback
            traceback.print_exc()

    def _open_profiles_editor(self):
        """Open the profiles editor in a separate window"""
        try:
            # Close settings window first
            if hasattr(self.app, 'settings_window') and self.app.settings_window.winfo_exists():
                self.app.settings_window.destroy()
            
            # Import and create profiles editor window
            from .json_editors import ProfilesEditorWindow
            
            # Check if editor is already open
            if hasattr(self.app, 'profiles_editor_window') and self.app.profiles_editor_window:
                try:
                    self.app.profiles_editor_window.show()
                    return
                except:
                    # Window was destroyed, create new one
                    pass
            
            # Create new profiles editor window
            self.app.profiles_editor_window = ProfilesEditorWindow(
                config_dir=self.app._config_dir_path,
                on_save_callback=self._on_profiles_saved
            )
            
            self.app.status_manager.add_log_message("📁 Profiles editor opened", "INFO")
            
        except Exception as e:
            self.app.status_manager.add_log_message(f"Error opening profiles editor: {e}", "ERROR")
            print(f"Error opening profiles editor: {e}")
            import traceback
            traceback.print_exc()