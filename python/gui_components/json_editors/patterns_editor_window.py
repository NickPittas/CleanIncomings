"""
Patterns Editor Window - Standalone editor for patterns.json
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
from typing import Dict, List, Any, Callable, Optional

from .shared_utils import load_json_file, save_json_file, clean_patterns_data
from .simple_patterns_tab import SimplePatternsTab
from .task_patterns_tab import TaskPatternsTab


class PatternsEditorWindow:
    """Standalone window for editing patterns.json"""
    
    def __init__(self, config_dir: str, on_save_callback: Optional[Callable] = None):
        self.config_dir = config_dir
        self.on_save_callback = on_save_callback
        self.patterns_data = {}
        self.window = None
        
        self.create_window()
        self.load_patterns()
        self.create_widgets()
    
    def create_window(self):
        """Create the main window"""
        self.window = ctk.CTkToplevel()
        self.window.title("Patterns Configuration Editor")
        self.window.geometry("800x600")
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
    
    def load_patterns(self):
        """Load patterns from patterns.json"""
        patterns_file = os.path.join(self.config_dir, "patterns.json")
        default_patterns = {
            "shotPatterns": [],
            "taskPatterns": {},
            "resolutionPatterns": [],
            "versionPatterns": [],
            "assetPatterns": [],
            "stagePatterns": []
        }
        self.patterns_data = load_json_file(patterns_file, default_patterns)
    
    def create_widgets(self):
        """Create the interface widgets"""
        # Header
        header_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="🎨 Patterns Configuration Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=2, sticky="e")
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Changes",
            command=self.save_patterns,
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
        
        # Create tabs
        self.create_pattern_tabs()
    
    def create_pattern_tabs(self):
        """Create tabs for different pattern types"""
        # Simple pattern tabs
        simple_patterns = [
            ("Shot Patterns", "shotPatterns", "Regex patterns for shot identification (e.g., SC\\d{3}, sh\\d{3})"),
            ("Resolution Patterns", "resolutionPatterns", "Resolution identifiers (e.g., 4k, 2k, hd, uhd)"),
            ("Version Patterns", "versionPatterns", "Version number patterns (e.g., v\\d{3}, ver\\d{3})"),
            ("Asset Patterns", "assetPatterns", "Asset type keywords (e.g., hero, vehicle, character, prop)"),
            ("Stage Patterns", "stagePatterns", "Production stage keywords (e.g., PREVIZ, ANIM, LAYOUT, COMP)")
        ]
        
        for tab_name, pattern_key, description in simple_patterns:
            # Add tab to CTkTabview
            tab_frame = self.notebook.add(tab_name)
            
            # Create tab content
            tab = SimplePatternsTab(
                parent=tab_frame,
                pattern_key=pattern_key,
                patterns_data=self.patterns_data,
                description=description,
                on_change_callback=self.on_patterns_changed
            )
            
            # Pack the tab content into the tab frame
            tab.get_frame().pack(fill="both", expand=True)
        
        # Task patterns tab (more complex)
        task_tab_frame = self.notebook.add("Task Patterns")
        task_tab = TaskPatternsTab(
            parent=task_tab_frame,
            patterns_data=self.patterns_data,
            on_change_callback=self.on_patterns_changed
        )
        task_tab.get_frame().pack(fill="both", expand=True)
    
    def on_patterns_changed(self):
        """Called when patterns data is modified"""
        # This allows tabs to notify the window that data has changed
        pass
    
    def save_patterns(self):
        """Save patterns to file"""
        patterns_file = os.path.join(self.config_dir, "patterns.json")
        clean_data = clean_patterns_data(self.patterns_data)
        
        if save_json_file(patterns_file, clean_data):
            messagebox.showinfo("Success", "Patterns saved successfully!")
            if self.on_save_callback:
                self.on_save_callback("patterns.json")
    
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