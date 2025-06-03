"""
Batch Edit Dialog

Provides UI for batch editing of sequence and file properties
including Asset, Task, Resolution, Version, Stage, and destination paths.
"""

import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Any, Optional, Callable
import os
from pathlib import Path


class BatchEditDialog(ctk.CTkToplevel):
    """Dialog for batch editing file/sequence properties."""
    
    def __init__(self, parent, items: List[Dict[str, Any]], on_apply_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.parent = parent
        self.items = items
        self.on_apply_callback = on_apply_callback
        self.changes_applied = False
        
        # Window configuration
        self.title(f"Batch Edit - {len(items)} items")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Keep window on top and make it modal
        self.attributes("-topmost", True)
        self.transient(parent)
        self.grab_set()
        
        # Initialize field variables
        self.shot_checkbox_var = tk.BooleanVar()
        self.asset_checkbox_var = tk.BooleanVar()
        self.task_checkbox_var = tk.BooleanVar()
        self.resolution_checkbox_var = tk.BooleanVar()
        self.version_checkbox_var = tk.BooleanVar()
        self.stage_checkbox_var = tk.BooleanVar()
        self.custom_path_checkbox_var = tk.BooleanVar()
        
        self.shot_var = tk.StringVar()
        self.asset_var = tk.StringVar()
        self.task_var = tk.StringVar()
        self.resolution_var = tk.StringVar()
        self.version_var = tk.StringVar()
        self.stage_var = tk.StringVar()
        self.custom_path_var = tk.StringVar()
        
        # Initialize preview variables
        self.preview_var = tk.StringVar()
        
        # Store dropdown widgets for dynamic updates
        self.shot_dropdown = None
        self.asset_dropdown = None
        self.task_dropdown = None
        self.resolution_dropdown = None
        self.version_dropdown = None
        self.stage_dropdown = None
        
        # Create UI
        self.create_ui()
        
        # Load current values (if all items have same value)
        self.load_current_values()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def create_ui(self):
        """Create the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Main content area
        
        # Header
        self.create_header()
        
        # Main content
        self.create_main_content()
        
        # Buttons
        self.create_buttons()

    def create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"Batch Edit Properties",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # Item summary
        sequences = sum(1 for item in self.items if item.get('type', '').lower() == 'sequence')
        files = len(self.items) - sequences
        
        summary_label = ctk.CTkLabel(
            header_frame,
            text=f"Selected: {len(self.items)} items ({sequences} sequences, {files} files)",
            font=ctk.CTkFont(size=12)
        )
        summary_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky="w")

    def create_main_content(self):
        """Create main content area with edit fields."""
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Check the fields you want to update and enter new values. Unchecked fields will remain unchanged.",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        instructions.grid(row=row, column=0, columnspan=3, padx=10, pady=(0,15), sticky="w")
        row += 1
        
        # Shot field
        self.create_field_row(main_frame, row, "Shot:", self.shot_checkbox_var, self.shot_var)
        row += 1
        
        # Asset field
        self.create_field_row(main_frame, row, "Asset:", self.asset_checkbox_var, self.asset_var)
        row += 1
        
        # Task field
        self.create_field_row(main_frame, row, "Task:", self.task_checkbox_var, self.task_var)
        row += 1
        
        # Resolution field
        self.create_field_row(main_frame, row, "Resolution:", self.resolution_checkbox_var, self.resolution_var)
        row += 1
        
        # Version field
        self.create_field_row(main_frame, row, "Version:", self.version_checkbox_var, self.version_var)
        row += 1
        
        # Stage field
        self.create_field_row(main_frame, row, "Stage:", self.stage_checkbox_var, self.stage_var)
        row += 1
        
        # Separator
        separator = ctk.CTkFrame(main_frame, height=2)
        separator.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        row += 1
        
        # Custom destination path
        custom_path_check = ctk.CTkCheckBox(
            main_frame,
            text="Override destination path:",
            variable=self.custom_path_checkbox_var,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        custom_path_check.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        row += 1
        
        self.custom_path_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.custom_path_var,
            placeholder_text="Enter custom destination directory...",
            width=400
        )
        self.custom_path_entry.grid(row=row, column=0, columnspan=2, padx=(30,10), pady=5, sticky="ew")
        
        browse_btn = ctk.CTkButton(
            main_frame,
            text="Browse",
            command=self.browse_custom_path,
            width=80
        )
        browse_btn.grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        # Preview section
        preview_label = ctk.CTkLabel(
            main_frame,
            text="Preview (first 3 items):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        preview_label.grid(row=row, column=0, columnspan=3, padx=10, pady=(15,5), sticky="w")
        row += 1
        
        # Preview text area
        self.preview_text = ctk.CTkTextbox(main_frame, height=120, font=ctk.CTkFont(family="Courier"))
        self.preview_text.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        row += 1
        
        # Update preview when fields change
        for var in [self.shot_var, self.asset_var, self.task_var, self.resolution_var, self.version_var, self.stage_var, self.custom_path_var]:
            var.trace('w', self.update_preview)
        for var in [self.shot_checkbox_var, self.asset_checkbox_var, self.task_checkbox_var, self.resolution_checkbox_var, self.version_checkbox_var, self.stage_checkbox_var, self.custom_path_checkbox_var]:
            var.trace('w', self.update_preview)

    def create_field_row(self, parent, row: int, label_text: str, checkbox_var: tk.BooleanVar, entry_var: tk.StringVar):
        """Create a row with checkbox, label, dropdown combo, and entry field."""
        checkbox = ctk.CTkCheckBox(
            parent,
            text="",
            variable=checkbox_var,
            width=20
        )
        checkbox.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=12),
            width=80
        )
        label.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        
        # Create frame for dropdown and entry
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.grid(row=row, column=2, padx=5, pady=5, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Get dropdown values based on field type
        dropdown_values = self._get_dropdown_values(label_text)
        
        # Dropdown combo box
        dropdown = ctk.CTkComboBox(
            input_frame,
            values=dropdown_values,
            width=150,
            command=lambda value: self._on_dropdown_change(entry_var, value)
        )
        dropdown.grid(row=0, column=0, padx=(0, 5), sticky="w")
        dropdown.set("")  # Start with no selection
        
        # Custom entry field
        entry = ctk.CTkEntry(
            input_frame,
            textvariable=entry_var,
            placeholder_text="Or enter custom value...",
            width=200
        )
        entry.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Store references for later use
        field_name = label_text.replace(":", "").lower()
        setattr(self, f"{field_name}_dropdown", dropdown)
        setattr(self, f"{field_name}_entry", entry)

    def _get_dropdown_values(self, field_label: str) -> List[str]:
        """Get dropdown values for a specific field from JSON files."""
        field_name = field_label.replace(":", "").lower()
        
        try:
            # Load patterns from the normalizer if available
            if hasattr(self.parent, 'normalizer') and self.parent.normalizer:
                config = self.parent.normalizer.mapping_generator.config
                if not config:
                    return ["No patterns loaded"]
                
                if field_name == "task":
                    # Get task patterns from taskPatterns
                    task_patterns = config.get("taskPatterns", {})
                    return list(task_patterns.keys())
                
                elif field_name == "asset":
                    # Get asset patterns from assetPatterns
                    asset_patterns = config.get("assetPatterns", [])
                    # Also include common asset names from profiles
                    profile_assets = self._get_profile_assets()
                    combined_assets = list(set(asset_patterns + profile_assets))
                    return sorted(combined_assets) if combined_assets else ["main_arch", "character", "prop", "env"]
                
                elif field_name == "resolution":
                    # Get resolution patterns and extract common resolutions
                    resolution_patterns = config.get("resolutionPatterns", [])
                    # Extract common resolutions from patterns
                    common_resolutions = []
                    for pattern in resolution_patterns:
                        if "4k" in pattern.lower():
                            common_resolutions.append("4K")
                        if "8k" in pattern.lower():
                            common_resolutions.append("8K")
                        if "2k" in pattern.lower():
                            common_resolutions.append("2K")
                        if "1080" in pattern:
                            common_resolutions.append("1080p")
                        if "720" in pattern:
                            common_resolutions.append("720p")
                    
                    # Add standard resolutions if not found
                    if not common_resolutions:
                        common_resolutions = ["2K", "4K", "8K", "1080p", "720p", "480p"]
                    
                    return sorted(list(set(common_resolutions)))
                
                elif field_name == "version":
                    # Generate common version formats
                    return ["v001", "v002", "v003", "v004", "v005", "v010", "v020", "v030"]
                
                elif field_name == "stage":
                    # Get stage patterns from stagePatterns
                    stage_patterns = config.get("stagePatterns", [])
                    # Also include common stages from profiles
                    profile_stages = self._get_profile_stages()
                    combined_stages = list(set(stage_patterns + profile_stages))
                    return sorted(combined_stages) if combined_stages else ["PREVIZ", "LAYOUT", "ANIM", "LIGHT", "RENDER", "FINAL"]
            
            # Fallback values if normalizer is not available
            fallback_values = {
                "task": ["beauty", "depth", "normal", "diffuse", "specular", "roughness", "emission", "rgb"],
                "asset": ["main_arch", "character", "prop", "env", "vehicle", "hero", "background"],
                "resolution": ["2K", "4K", "8K", "1080p", "720p"],
                "version": ["v001", "v002", "v003", "v004", "v005"],
                "stage": ["PREVIZ", "LAYOUT", "ANIM", "LIGHT", "RENDER", "FINAL"]
            }
            
            return fallback_values.get(field_name, [])
            
        except Exception as e:
            print(f"[BATCH_EDIT] Error loading dropdown values for {field_name}: {e}")
            return [f"Error loading {field_name} values"]

    def _get_profile_assets(self) -> List[str]:
        """Extract asset names from current profile."""
        try:
            if hasattr(self.parent, 'normalizer') and self.parent.normalizer:
                profile_name = self.parent.selected_profile_name.get()
                profile_data = self.parent.normalizer.all_profiles_data.get(profile_name, [])
                
                assets = []
                if isinstance(profile_data, list):
                    for rule in profile_data:
                        if isinstance(rule, dict):
                            for path, keywords in rule.items():
                                if isinstance(keywords, list):
                                    # Filter for asset-like keywords (lowercase, no special chars)
                                    for keyword in keywords:
                                        if isinstance(keyword, str) and keyword.islower() and "_" in keyword:
                                            assets.append(keyword)
                
                return list(set(assets))
        except Exception as e:
            print(f"[BATCH_EDIT] Error extracting profile assets: {e}")
        return []

    def _get_profile_stages(self) -> List[str]:
        """Extract stage names from current profile."""
        try:
            if hasattr(self.parent, 'normalizer') and self.parent.normalizer:
                profile_name = self.parent.selected_profile_name.get()
                profile_data = self.parent.normalizer.all_profiles_data.get(profile_name, [])
                
                stages = []
                if isinstance(profile_data, list):
                    for rule in profile_data:
                        if isinstance(rule, dict):
                            for path, keywords in rule.items():
                                if isinstance(keywords, list):
                                    # Filter for stage-like keywords (uppercase)
                                    for keyword in keywords:
                                        if isinstance(keyword, str) and keyword.isupper():
                                            stages.append(keyword)
                
                return list(set(stages))
        except Exception as e:
            print(f"[BATCH_EDIT] Error extracting profile stages: {e}")
        return []

    def _on_dropdown_change(self, entry_var: tk.StringVar, value: str):
        """Handle dropdown selection change."""
        if value and value != "":
            entry_var.set(value)  # Update the entry field with dropdown selection

    def create_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5,10))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=100
        )
        cancel_btn.pack(side="right", padx=10, pady=10)
        
        # Apply button
        apply_btn = ctk.CTkButton(
            button_frame,
            text="Apply Changes",
            command=self.on_apply,
            width=120
        )
        apply_btn.pack(side="right", padx=5, pady=10)
        
        # Reset button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset",
            command=self.reset_fields,
            width=80
        )
        reset_btn.pack(side="left", padx=10, pady=10)

    def load_current_values(self):
        """Load current values if all selected items have the same value."""
        if not self.items:
            return
        
        # Check if all items have the same values for each field
        def get_common_value(field_path):
            values = set()
            for item in self.items:
                if isinstance(field_path, list):
                    # Nested field like ['normalized_parts', 'task']
                    value = item
                    for key in field_path:
                        value = value.get(key, {}) if isinstance(value, dict) else {}
                    values.add(str(value) if value else "")
                else:
                    # Simple field
                    values.add(str(item.get(field_path, "")))
            return list(values)[0] if len(values) == 1 else ""
        
        # Load common values
        self.shot_var.set(get_common_value('shot'))
        self.asset_var.set(get_common_value('asset'))
        self.task_var.set(get_common_value('task'))
        self.resolution_var.set(get_common_value('resolution'))
        self.version_var.set(get_common_value('version'))
        self.stage_var.set(get_common_value('stage'))
        
        # Also update dropdowns to show current values
        self._update_dropdown_selections()
        
        # Update preview
        self.update_preview()

    def _update_dropdown_selections(self):
        """Update dropdown selections to match current entry values."""
        try:
            if hasattr(self, 'shot_dropdown'):
                self.shot_dropdown.set(self.shot_var.get())
            if hasattr(self, 'asset_dropdown'):
                self.asset_dropdown.set(self.asset_var.get())
            if hasattr(self, 'task_dropdown'):
                self.task_dropdown.set(self.task_var.get())
            if hasattr(self, 'resolution_dropdown'):
                self.resolution_dropdown.set(self.resolution_var.get())
            if hasattr(self, 'version_dropdown'):
                self.version_dropdown.set(self.version_var.get())
            if hasattr(self, 'stage_dropdown'):
                self.stage_dropdown.set(self.stage_var.get())
        except Exception as e:
            print(f"[BATCH_EDIT] Error updating dropdown selections: {e}")

    def reset_fields(self):
        """Reset all fields to their initial values."""
        # Clear all checkboxes
        self.shot_checkbox_var.set(False)
        self.asset_checkbox_var.set(False)
        self.task_checkbox_var.set(False)
        self.resolution_checkbox_var.set(False)
        self.version_checkbox_var.set(False)
        self.stage_checkbox_var.set(False)
        self.custom_path_checkbox_var.set(False)
        
        # Clear all entry fields
        self.shot_var.set("")
        self.asset_var.set("")
        self.task_var.set("")
        self.resolution_var.set("")
        self.version_var.set("")
        self.stage_var.set("")
        self.custom_path_var.set("")
        
        # Clear dropdown selections
        if hasattr(self, 'shot_dropdown'):
            self.shot_dropdown.set("")
        if hasattr(self, 'asset_dropdown'):
            self.asset_dropdown.set("")
        if hasattr(self, 'task_dropdown'):
            self.task_dropdown.set("")
        if hasattr(self, 'resolution_dropdown'):
            self.resolution_dropdown.set("")
        if hasattr(self, 'version_dropdown'):
            self.version_dropdown.set("")
        if hasattr(self, 'stage_dropdown'):
            self.stage_dropdown.set("")
        
        # Update preview
        self.update_preview()

    def on_apply(self):
        """Apply the batch changes."""
        # Collect changes
        changes = {}
        
        if self.shot_checkbox_var.get() and self.shot_var.get():
            changes['shot'] = self.shot_var.get()
        if self.asset_checkbox_var.get() and self.asset_var.get():
            changes['asset'] = self.asset_var.get()
        if self.task_checkbox_var.get() and self.task_var.get():
            changes['task'] = self.task_var.get()
        if self.resolution_checkbox_var.get() and self.resolution_var.get():
            changes['resolution'] = self.resolution_var.get()
        if self.version_checkbox_var.get() and self.version_var.get():
            changes['version'] = self.version_var.get()
        if self.stage_checkbox_var.get() and self.stage_var.get():
            changes['stage'] = self.stage_var.get()
        if self.custom_path_checkbox_var.get() and self.custom_path_var.get():
            changes['custom_path'] = self.custom_path_var.get()
        
        if not changes:
            self.parent.status_manager.add_log_message("No changes to apply", "WARNING")
            return
        
        # Apply changes via callback
        if self.on_apply_callback:
            self.on_apply_callback(self.items, changes)
        
        self.changes_applied = True
        self.destroy()

    def on_cancel(self):
        """Cancel the dialog without applying changes."""
        if not self.changes_applied:
            self.parent.status_manager.add_log_message("Batch edit cancelled", "INFO")
        self.destroy()

    def browse_custom_path(self):
        """Browse for custom destination path."""
        from tkinter import filedialog
        
        initial_dir = self.custom_path_var.get() or os.path.expanduser("~")
        
        directory = filedialog.askdirectory(
            title="Select Custom Destination Directory",
            initialdir=initial_dir
        )
        
        if directory:
            self.custom_path_var.set(directory)

    def update_preview(self, *args):
        """Update the preview text with sample destination paths."""
        preview_items = self.items[:3]  # Show first 3 items
        preview_text = ""
        
        for i, item in enumerate(preview_items):
            original_filename = item.get('filename', 'unknown')
            original_path = item.get('new_destination_path', '')
            
            # Create a copy of the item with updated values
            updated_item = item.copy()
            updated_parts = updated_item.get('normalized_parts', {}).copy()
            
            # Apply updates based on checkboxes
            if self.shot_checkbox_var.get():
                updated_parts['shot'] = self.shot_var.get()
            if self.asset_checkbox_var.get():
                updated_parts['asset'] = self.asset_var.get()
            if self.task_checkbox_var.get():
                updated_parts['task'] = self.task_var.get()
            if self.resolution_checkbox_var.get():
                updated_parts['resolution'] = self.resolution_var.get()
            if self.version_checkbox_var.get():
                updated_parts['version'] = self.version_var.get()
            if self.stage_checkbox_var.get():
                updated_parts['stage'] = self.stage_var.get()
            
            updated_item['normalized_parts'] = updated_parts
            
            # Generate new path using proper path generation logic
            if self.custom_path_checkbox_var.get() and self.custom_path_var.get():
                new_path = os.path.join(self.custom_path_var.get(), original_filename)
            else:
                # Use proper path generation logic for preview
                new_path = self._generate_preview_path(updated_parts, original_filename)
            
            preview_text += f"{i+1}. {original_filename}\n"
            preview_text += f"   Current: {original_path or 'Not set'}\n"
            preview_text += f"   New:     {new_path}\n"
            preview_text += f"   Changes: "
            
            changes = []
            if self.shot_checkbox_var.get():
                changes.append(f"Shot={self.shot_var.get()}")
            if self.asset_checkbox_var.get():
                changes.append(f"Asset={self.asset_var.get()}")
            if self.task_checkbox_var.get():
                changes.append(f"Task={self.task_var.get()}")
            if self.resolution_checkbox_var.get():
                changes.append(f"Resolution={self.resolution_var.get()}")
            if self.version_checkbox_var.get():
                changes.append(f"Version={self.version_var.get()}")
            if self.stage_checkbox_var.get():
                changes.append(f"Stage={self.stage_var.get()}")
            if self.custom_path_checkbox_var.get():
                changes.append(f"CustomPath={self.custom_path_var.get()}")
            
            preview_text += ", ".join(changes) if changes else "None"
            preview_text += "\n\n"
        
        # Update preview textbox
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview_text)

    def _generate_preview_path(self, normalized_parts: Dict[str, Any], filename: str) -> str:
        """Generate a preview path using the proper path generation logic."""
        try:
            # Get the original item to determine if it's a sequence or file
            original_item = None
            for item in self.items:
                if item.get('filename') == filename:
                    original_item = item
                    break
            
            if not original_item:
                return f"[ITEM_NOT_FOUND] {filename}"
            
            item_type = original_item.get('type', 'file').lower()
            
            # Get current profile and its rules
            profile_name = self.parent.selected_profile_name.get()
            if self.parent.normalizer and profile_name:
                # Get profile rules from normalizer
                profile_data = self.parent.normalizer.all_profiles_data.get(profile_name, [])
                if isinstance(profile_data, list):
                    profile_rules = profile_data
                elif isinstance(profile_data, dict) and 'rules' in profile_data:
                    profile_rules = profile_data['rules']
                else:
                    profile_rules = []
                
                # Get root output directory
                root_output_dir = self.parent.selected_destination_folder.get()
                if not root_output_dir:
                    root_output_dir = os.path.join(os.getcwd(), "output")
                
                if item_type == 'sequence':
                    # Handle sequence preview generation
                    from ..mapping_utils.create_sequence_mapping import create_sequence_mapping
                    
                    # Get patterns from config, not from non-existent attributes  
                    config = self.parent.normalizer.mapping_generator.config
                    if config:
                        p_shot = self.parent.normalizer.mapping_generator.shot_patterns
                        p_task = self.parent.normalizer.mapping_generator.task_patterns
                        p_version = self.parent.normalizer.mapping_generator.version_patterns
                        p_resolution = self.parent.normalizer.mapping_generator.resolution_patterns
                        p_asset = config.get("assetPatterns", [])  # Get from config
                        p_stage = config.get("stagePatterns", [])   # Get from config
                    else:
                        p_shot = p_task = p_version = p_resolution = p_asset = p_stage = None
                    
                    # Reconstruct sequence data for mapping
                    sequence_info = original_item.get('sequence_info', {})
                    base_name = sequence_info.get('base_name', filename.replace('.####.', '_').split('.')[0])
                    
                    sequence_dict = {
                        "files": sequence_info.get('files', []),
                        "base_name": base_name,
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
                    
                    # Generate new sequence mapping
                    new_sequence_proposal = create_sequence_mapping(
                        sequence=sequence_dict,
                        profile=profile_object,
                        root_output_dir=root_output_dir,
                        original_base_name=base_name,
                        p_shot=p_shot,
                        p_task=p_task,
                        p_version=p_version,
                        p_resolution=p_resolution,
                        p_asset=p_asset,
                        p_stage=p_stage
                    )
                    
                    if new_sequence_proposal:
                        new_target_path = new_sequence_proposal.get("targetPath")
                        if new_target_path:
                            return new_target_path
                        else:
                            return f"[SEQUENCE_PATH_GENERATION_FAILED] {filename}"
                    else:
                        return f"[NO_SEQUENCE_PROPOSAL] {filename}"
                
                else:
                    # Handle individual file preview generation
                    from ..mapping_utils.generate_simple_target_path import generate_simple_target_path
                    
                    # Extract values from normalized parts
                    parsed_shot = normalized_parts.get('shot')
                    parsed_task = normalized_parts.get('task')
                    parsed_asset = normalized_parts.get('asset')
                    parsed_stage = normalized_parts.get('stage')
                    parsed_version = normalized_parts.get('version')
                    parsed_resolution = normalized_parts.get('resolution')
                    
                    # Generate new target path
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
                        return new_target_path
                    else:
                        # Handle ambiguous or failed path generation
                        if path_result.get("ambiguous_match"):
                            return f"[AMBIGUOUS_MATCH] {filename}"
                        else:
                            return f"[PATH_GENERATION_FAILED] {filename}"
            else:
                return f"[NO_PROFILE_AVAILABLE] {filename}"
        
        except Exception as e:
            return f"[ERROR_GENERATING_PATH] {filename} ({str(e)})" 