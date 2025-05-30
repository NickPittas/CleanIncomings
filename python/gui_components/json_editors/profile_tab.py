"""
Profile Tab - For managing individual profile configurations
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, List, Callable, Optional


class ProfileTab:
    """Tab for managing a single profile"""
    
    def __init__(self, parent, profile_name: str, profiles_data: Dict, patterns_data: Dict,
                 on_change_callback: Optional[Callable] = None,
                 on_delete_callback: Optional[Callable] = None,
                 on_rename_callback: Optional[Callable] = None):
        self.parent = parent
        self.profile_name = profile_name
        self.profiles_data = profiles_data
        self.patterns_data = patterns_data
        self.on_change_callback = on_change_callback
        self.on_delete_callback = on_delete_callback
        self.on_rename_callback = on_rename_callback
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(parent)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.create_widgets()
        self.refresh_folders()
    
    def create_widgets(self):
        """Create the tab widgets"""
        # Header with profile name and controls
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        # Profile name entry
        self.profile_var = tk.StringVar(value=self.profile_name)
        profile_entry = ctk.CTkEntry(
            header,
            textvariable=self.profile_var,
            placeholder_text="Profile name...",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200
        )
        profile_entry.grid(row=0, column=0, sticky="w")
        
        # Bind profile name changes
        self.profile_var.trace('w', self.on_profile_name_changed)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(header, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="e")
        
        # Add folder button
        add_folder_btn = ctk.CTkButton(
            buttons_frame,
            text="➕ Add Folder",
            command=self.add_folder,
            width=120
        )
        add_folder_btn.pack(side="left", padx=2)
        
        # Delete profile button
        delete_profile_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete Profile",
            command=self.delete_profile,
            width=140,
            fg_color="red",
            hover_color="darkred"
        )
        delete_profile_btn.pack(side="left", padx=2)
        
        # Folders scrollable frame
        self.folders_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.folders_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.folders_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_folders(self):
        """Refresh the folders display"""
        # Clear existing widgets
        for widget in self.folders_frame.winfo_children():
            widget.destroy()
        
        # Get profile rules
        profile_rules = self.profiles_data.get(self.profile_name, [])
        
        if not profile_rules:
            empty_label = ctk.CTkLabel(
                self.folders_frame,
                text="No folders configured. Click 'Add Folder' to create one.",
                text_color=("gray60", "gray40")
            )
            empty_label.grid(row=0, column=0, pady=20)
            return
        
        # Create folder entries
        for i, rule in enumerate(profile_rules):
            self.create_folder_entry(i, rule)
    
    def create_folder_entry(self, index: int, rule: Dict[str, List[str]]):
        """Create a folder entry with pattern selection"""
        # Each rule is a dict with one key (folder path) and list of patterns
        folder_path = list(rule.keys())[0]
        assigned_patterns = rule[folder_path]
        
        folder_frame = ctk.CTkFrame(self.folders_frame)
        folder_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=5)
        folder_frame.grid_columnconfigure(0, weight=1)
        
        # Folder header
        folder_header = ctk.CTkFrame(folder_frame, fg_color="transparent")
        folder_header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        folder_header.grid_columnconfigure(1, weight=1)
        
        # Folder path entry
        folder_var = tk.StringVar(value=folder_path)
        folder_entry = ctk.CTkEntry(
            folder_header,
            textvariable=folder_var,
            placeholder_text="Folder path (e.g., 3D/Renders)...",
            font=ctk.CTkFont(weight="bold"),
            width=300
        )
        folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Bind folder path changes
        folder_var.trace('w', lambda *args: self.update_folder_path(index, folder_var.get()))
        
        # Delete folder button
        delete_folder_btn = ctk.CTkButton(
            folder_header,
            text="🗑️ Delete Folder",
            command=lambda: self.delete_folder(index),
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        delete_folder_btn.grid(row=0, column=1, sticky="e")
        
        # Pattern assignment info
        patterns_info_frame = ctk.CTkFrame(folder_frame)
        patterns_info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        # Show assigned patterns summary
        if assigned_patterns:
            patterns_text = f"Assigned patterns: {', '.join(assigned_patterns[:5])}"
            if len(assigned_patterns) > 5:
                patterns_text += f" ... and {len(assigned_patterns) - 5} more"
        else:
            patterns_text = "No patterns assigned"
        
        patterns_summary = ctk.CTkLabel(
            patterns_info_frame,
            text=patterns_text,
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        patterns_summary.pack(side="left", padx=10, pady=5)
        
        # Edit patterns button
        edit_patterns_btn = ctk.CTkButton(
            patterns_info_frame,
            text="🎨 Edit Patterns",
            command=lambda idx=index: self.edit_folder_patterns(idx),
            width=120,
            height=25
        )
        edit_patterns_btn.pack(side="right", padx=10, pady=5)
    
    def edit_folder_patterns(self, folder_index: int):
        """Open a dialog to edit patterns for a folder"""
        from .pattern_selection_dialog import PatternSelectionDialog
        
        # Get current folder rule
        profile_rules = self.profiles_data.get(self.profile_name, [])
        if 0 <= folder_index < len(profile_rules):
            rule = profile_rules[folder_index]
            folder_path = list(rule.keys())[0]
            assigned_patterns = rule[folder_path]
            
            # Create dialog
            dialog = PatternSelectionDialog(
                parent=self.main_frame,
                title=f"Edit Patterns for: {folder_path}",
                patterns_data=self.patterns_data,
                assigned_patterns=assigned_patterns.copy(),
                on_save_callback=lambda patterns: self.update_folder_patterns(folder_index, patterns)
            )
    
    def update_folder_patterns(self, folder_index: int, new_patterns: List[str]):
        """Update the patterns for a folder"""
        profile_rules = self.profiles_data.get(self.profile_name, [])
        if 0 <= folder_index < len(profile_rules):
            rule = profile_rules[folder_index]
            folder_path = list(rule.keys())[0]
            profile_rules[folder_index] = {folder_path: new_patterns}
            self.refresh_folders()
            self.notify_change()
    
    def add_folder(self):
        """Add a new folder to the profile"""
        if self.profile_name in self.profiles_data:
            new_folder = {"New Folder": []}
            self.profiles_data[self.profile_name].append(new_folder)
            self.refresh_folders()
            self.notify_change()
    
    def update_folder_path(self, folder_index: int, new_path: str):
        """Update folder path"""
        profile_rules = self.profiles_data.get(self.profile_name, [])
        if 0 <= folder_index < len(profile_rules):
            rule = profile_rules[folder_index]
            old_path = list(rule.keys())[0]
            patterns = rule[old_path]
            
            # Update with new path
            profile_rules[folder_index] = {new_path: patterns}
            self.notify_change()
    
    def delete_folder(self, folder_index: int):
        """Delete a folder from the profile"""
        profile_rules = self.profiles_data.get(self.profile_name, [])
        if 0 <= folder_index < len(profile_rules):
            result = messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this folder configuration?"
            )
            if result:
                del profile_rules[folder_index]
                self.refresh_folders()
                self.notify_change()
    
    def on_profile_name_changed(self, *args):
        """Handle profile name changes"""
        new_name = self.profile_var.get()
        if new_name != self.profile_name and self.on_rename_callback:
            success = self.on_rename_callback(self.profile_name, new_name)
            if success:
                self.profile_name = new_name
            else:
                # Reset to original name if rename failed
                self.profile_var.set(self.profile_name)
    
    def delete_profile(self):
        """Delete this profile"""
        if self.on_delete_callback:
            self.on_delete_callback()
    
    def notify_change(self):
        """Notify parent of changes"""
        if self.on_change_callback:
            self.on_change_callback()
    
    def get_frame(self):
        """Get the main frame"""
        return self.main_frame 