"""
Simple Patterns Tab - For array-based pattern types
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Callable, Optional


class SimplePatternsTab:
    """Tab for managing simple pattern lists (arrays)"""
    
    def __init__(self, parent, pattern_key: str, patterns_data: Dict, 
                 description: str, on_change_callback: Optional[Callable] = None):
        self.parent = parent
        self.pattern_key = pattern_key
        self.patterns_data = patterns_data
        self.description = description
        self.on_change_callback = on_change_callback
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(parent)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.create_widgets()
        self.refresh_patterns()
    
    def create_widgets(self):
        """Create the tab widgets"""
        # Header with info and add button
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        info_label = ctk.CTkLabel(
            header,
            text=self.description,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        info_label.grid(row=0, column=0, sticky="w")
        
        add_btn = ctk.CTkButton(
            header,
            text="➕ Add Pattern",
            command=self.add_pattern,
            width=120
        )
        add_btn.grid(row=0, column=2, sticky="e")
        
        # Scrollable frame for pattern items
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_patterns(self):
        """Refresh the display of patterns"""
        # Clear existing widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Get patterns
        patterns = self.patterns_data.get(self.pattern_key, [])
        
        if not patterns:
            empty_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No patterns defined. Click 'Add Pattern' to create one.",
                text_color=("gray60", "gray40")
            )
            empty_label.grid(row=0, column=0, pady=20)
            return
        
        # Create pattern entries
        for i, pattern in enumerate(patterns):
            self.create_pattern_entry(i, pattern)
    
    def create_pattern_entry(self, index: int, pattern: str):
        """Create a single pattern entry with edit/delete"""
        entry_frame = ctk.CTkFrame(self.scroll_frame)
        entry_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Index label
        index_label = ctk.CTkLabel(
            entry_frame,
            text=f"{index + 1}.",
            width=30,
            font=ctk.CTkFont(size=12)
        )
        index_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Pattern entry
        pattern_var = tk.StringVar(value=pattern)
        entry = ctk.CTkEntry(
            entry_frame,
            textvariable=pattern_var,
            placeholder_text="Enter pattern...",
            width=300
        )
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Bind changes
        pattern_var.trace('w', lambda *args: self.update_pattern(index, pattern_var.get()))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            entry_frame,
            text="🗑️",
            command=lambda: self.delete_pattern(index),
            width=40,
            fg_color="red",
            hover_color="darkred"
        )
        delete_btn.grid(row=0, column=2, padx=5, pady=5)
    
    def add_pattern(self):
        """Add a new pattern"""
        if self.pattern_key not in self.patterns_data:
            self.patterns_data[self.pattern_key] = []
        self.patterns_data[self.pattern_key].append("")
        self.refresh_patterns()
        self.notify_change()
    
    def update_pattern(self, index: int, value: str):
        """Update a pattern"""
        patterns = self.patterns_data.get(self.pattern_key, [])
        if 0 <= index < len(patterns):
            patterns[index] = value
            self.notify_change()
    
    def delete_pattern(self, index: int):
        """Delete a pattern"""
        patterns = self.patterns_data.get(self.pattern_key, [])
        if 0 <= index < len(patterns):
            del patterns[index]
            self.refresh_patterns()
            self.notify_change()
    
    def notify_change(self):
        """Notify parent of changes"""
        if self.on_change_callback:
            self.on_change_callback()
    
    def get_frame(self):
        """Get the main frame"""
        return self.main_frame 