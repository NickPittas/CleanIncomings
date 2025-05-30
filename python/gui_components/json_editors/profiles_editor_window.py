"""
Profiles Editor Window - Standalone editor for profiles.json
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
from typing import Dict, List, Any, Callable, Optional

from .shared_utils import load_json_file, save_json_file, clean_profiles_data
from .profile_tab import ProfileTab


class ProfilesEditorWindow:
    """Standalone window for editing profiles.json"""
    
    def __init__(self, config_dir: str, on_save_callback: Optional[Callable] = None):
        self.config_dir = config_dir
        self.on_save_callback = on_save_callback
        self.profiles_data = {}
        self.patterns_data = {}
        self.window = None
        self.profile_tabs = {}
        
        self.create_window()
        self.load_data()
        self.create_widgets()
    
    def create_window(self):
        """Create the main window"""
        self.window = ctk.CTkToplevel()
        self.window.title("Profiles Configuration Editor")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
    
    def load_data(self):
        """Load profiles and patterns data"""
        # Load profiles
        profiles_file = os.path.join(self.config_dir, "profiles.json")
        self.profiles_data = load_json_file(profiles_file, {})
        
        # Load patterns for reference
        patterns_file = os.path.join(self.config_dir, "patterns.json")
        self.patterns_data = load_json_file(patterns_file, {})
    
    def create_widgets(self):
        """Create the interface widgets"""
        # Header
        header_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="📁 Profiles Configuration Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=2, sticky="e")
        
        add_profile_btn = ctk.CTkButton(
            buttons_frame,
            text="➕ Add Profile",
            command=self.add_profile,
            width=120
        )
        add_profile_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Changes",
            command=self.save_profiles,
            width=120
        )
        save_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Close",
            command=self.window.destroy,
            width=80
        )
        close_btn.pack(side="left", padx=5)
        
        # Main content with notebook
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Create profile tabs
        self.refresh_profiles()
    
    def refresh_profiles(self):
        """Refresh the profiles display"""
        # Clear existing tabs - CTkTabview doesn't have tabs() method, need to track manually
        # For CTkTabview, we need to recreate the entire tabview
        self.notebook.destroy()
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        self.profile_tabs.clear()
        
        if not self.profiles_data:
            # Show empty state
            empty_tab_frame = self.notebook.add("No Profiles")
            
            empty_label = ctk.CTkLabel(
                empty_tab_frame,
                text="No profiles defined.\nClick 'Add Profile' to create your first profile.",
                font=ctk.CTkFont(size=16),
                text_color=("gray60", "gray40")
            )
            empty_label.pack(expand=True)
            return
        
        # Create tab for each profile
        for profile_name in self.profiles_data.keys():
            self.create_profile_tab(profile_name)
    
    def create_profile_tab(self, profile_name: str):
        """Create a tab for a profile"""
        # Add tab to CTkTabview
        tab_frame = self.notebook.add(profile_name)
        
        tab = ProfileTab(
            parent=tab_frame,
            profile_name=profile_name,
            profiles_data=self.profiles_data,
            patterns_data=self.patterns_data,
            on_change_callback=self.on_profiles_changed,
            on_delete_callback=lambda pn=profile_name: self.delete_profile(pn),
            on_rename_callback=self.rename_profile
        )
        
        self.profile_tabs[profile_name] = tab
        # Pack the tab content into the tab frame
        tab.get_frame().pack(fill="both", expand=True)
    
    def add_profile(self):
        """Add a new profile"""
        # Find unique name
        base_name = "New Project"
        counter = 1
        profile_name = base_name
        while profile_name in self.profiles_data:
            profile_name = f"{base_name} {counter}"
            counter += 1
        
        self.profiles_data[profile_name] = []
        self.refresh_profiles()
        self.on_profiles_changed()
    
    def delete_profile(self, profile_name: str):
        """Delete a profile"""
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the profile '{profile_name}' and all its folder configurations?"
        )
        if result:
            del self.profiles_data[profile_name]
            self.refresh_profiles()
            self.on_profiles_changed()
    
    def rename_profile(self, old_name: str, new_name: str):
        """Rename a profile"""
        if old_name != new_name and old_name in self.profiles_data:
            # Check if new name already exists
            if new_name in self.profiles_data:
                messagebox.showwarning("Warning", f"Profile '{new_name}' already exists!")
                return False
            
            # Update the profile name
            profile_data = self.profiles_data[old_name]
            del self.profiles_data[old_name]
            self.profiles_data[new_name] = profile_data
            
            # Refresh to update tab names
            self.refresh_profiles()
            self.on_profiles_changed()
            return True
        return False
    
    def on_profiles_changed(self):
        """Called when profiles data is modified"""
        # This allows tabs to notify the window that data has changed
        pass
    
    def save_profiles(self):
        """Save profiles to file"""
        profiles_file = os.path.join(self.config_dir, "profiles.json")
        clean_data = clean_profiles_data(self.profiles_data)
        
        if save_json_file(profiles_file, clean_data):
            messagebox.showinfo("Success", "Profiles saved successfully!")
            if self.on_save_callback:
                self.on_save_callback("profiles.json")
    
    def show(self):
        """Show the window"""
        if self.window:
            self.window.lift()
            self.window.focus()
    
    def destroy(self):
        """Destroy the window"""
        if self.window:
            self.window.destroy()
            self.window = None 