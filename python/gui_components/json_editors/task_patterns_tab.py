"""
Task Patterns Tab - For nested task pattern structure
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, List, Callable, Optional


class TaskPatternsTab:
    """Tab for managing task patterns (nested structure)"""
    
    def __init__(self, parent, patterns_data: Dict, on_change_callback: Optional[Callable] = None):
        self.parent = parent
        self.patterns_data = patterns_data
        self.on_change_callback = on_change_callback
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(parent)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.create_widgets()
        self.refresh_task_patterns()
    
    def create_widgets(self):
        """Create the tab widgets"""
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        info_label = ctk.CTkLabel(
            header,
            text="Task categories with their associated keywords/aliases",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        info_label.grid(row=0, column=0, sticky="w")
        
        add_task_btn = ctk.CTkButton(
            header,
            text="➕ Add Task Category",
            command=self.add_task_category,
            width=150
        )
        add_task_btn.grid(row=0, column=2, sticky="e")
        
        # Scrollable frame for task categories
        self.task_scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.task_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.task_scroll_frame.grid_columnconfigure(0, weight=1)
    
    def refresh_task_patterns(self):
        """Refresh the display of task patterns"""
        # Clear existing widgets
        for widget in self.task_scroll_frame.winfo_children():
            widget.destroy()
        
        # Get task patterns
        task_patterns = self.patterns_data.get("taskPatterns", {})
        
        if not task_patterns:
            empty_label = ctk.CTkLabel(
                self.task_scroll_frame,
                text="No task categories defined. Click 'Add Task Category' to create one.",
                text_color=("gray60", "gray40")
            )
            empty_label.grid(row=0, column=0, pady=20)
            return
        
        # Create task category entries
        for i, (task_name, patterns) in enumerate(task_patterns.items()):
            self.create_task_category_entry(i, task_name, patterns)
    
    def create_task_category_entry(self, index: int, task_name: str, patterns: List[str]):
        """Create a task category entry"""
        category_frame = ctk.CTkFrame(self.task_scroll_frame)
        category_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=5)
        category_frame.grid_columnconfigure(0, weight=1)
        
        # Header with task name and buttons
        header_frame = ctk.CTkFrame(category_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Task name entry
        task_var = tk.StringVar(value=task_name)
        task_entry = ctk.CTkEntry(
            header_frame,
            textvariable=task_var,
            placeholder_text="Task category name...",
            font=ctk.CTkFont(weight="bold"),
            width=200
        )
        task_entry.grid(row=0, column=0, sticky="w")
        
        # Bind task name changes
        task_var.trace('w', lambda *args: self.update_task_name(task_name, task_var.get()))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="e")
        
        # Add pattern button
        add_pattern_btn = ctk.CTkButton(
            buttons_frame,
            text="➕ Add Keyword",
            command=lambda tn=task_name: self.add_task_pattern(tn),
            width=120
        )
        add_pattern_btn.pack(side="left", padx=2)
        
        # Delete category button
        delete_category_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete Category",
            command=lambda tn=task_name: self.delete_task_category(tn),
            width=140,
            fg_color="red",
            hover_color="darkred"
        )
        delete_category_btn.pack(side="left", padx=2)
        
        # Patterns frame
        patterns_frame = ctk.CTkFrame(category_frame)
        patterns_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        patterns_frame.grid_columnconfigure(0, weight=1)
        
        # Create pattern entries
        for i, pattern in enumerate(patterns):
            self.create_task_pattern_entry(patterns_frame, task_name, i, pattern)
    
    def create_task_pattern_entry(self, parent, task_name: str, index: int, pattern: str):
        """Create a single task pattern entry"""
        entry_frame = ctk.CTkFrame(parent)
        entry_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Index label
        index_label = ctk.CTkLabel(
            entry_frame,
            text=f"{index + 1}.",
            width=30,
            font=ctk.CTkFont(size=12)
        )
        index_label.grid(row=0, column=0, padx=5, pady=2)
        
        # Pattern entry
        pattern_var = tk.StringVar(value=pattern)
        entry = ctk.CTkEntry(
            entry_frame,
            textvariable=pattern_var,
            placeholder_text="Enter keyword/alias...",
            width=250
        )
        entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # Bind changes
        pattern_var.trace('w', lambda *args: self.update_task_pattern(task_name, index, pattern_var.get()))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            entry_frame,
            text="🗑️",
            command=lambda: self.delete_task_pattern(task_name, index),
            width=40,
            fg_color="red",
            hover_color="darkred"
        )
        delete_btn.grid(row=0, column=2, padx=5, pady=2)
    
    def add_task_category(self):
        """Add a new task category"""
        if "taskPatterns" not in self.patterns_data:
            self.patterns_data["taskPatterns"] = {}
        
        # Find a unique name
        base_name = "new_task"
        counter = 1
        task_name = base_name
        while task_name in self.patterns_data["taskPatterns"]:
            task_name = f"{base_name}_{counter}"
            counter += 1
        
        self.patterns_data["taskPatterns"][task_name] = []
        self.refresh_task_patterns()
        self.notify_change()
    
    def update_task_name(self, old_name: str, new_name: str):
        """Update task category name"""
        if old_name != new_name and "taskPatterns" in self.patterns_data:
            if old_name in self.patterns_data["taskPatterns"]:
                patterns = self.patterns_data["taskPatterns"][old_name]
                del self.patterns_data["taskPatterns"][old_name]
                self.patterns_data["taskPatterns"][new_name] = patterns
                self.notify_change()
    
    def delete_task_category(self, task_name: str):
        """Delete a task category"""
        if "taskPatterns" in self.patterns_data and task_name in self.patterns_data["taskPatterns"]:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the task category '{task_name}' and all its patterns?"
            )
            if result:
                del self.patterns_data["taskPatterns"][task_name]
                self.refresh_task_patterns()
                self.notify_change()
    
    def add_task_pattern(self, task_name: str):
        """Add a pattern to a task category"""
        if "taskPatterns" in self.patterns_data and task_name in self.patterns_data["taskPatterns"]:
            self.patterns_data["taskPatterns"][task_name].append("")
            self.refresh_task_patterns()
            self.notify_change()
    
    def update_task_pattern(self, task_name: str, index: int, value: str):
        """Update a task pattern"""
        if ("taskPatterns" in self.patterns_data and 
            task_name in self.patterns_data["taskPatterns"] and
            0 <= index < len(self.patterns_data["taskPatterns"][task_name])):
            self.patterns_data["taskPatterns"][task_name][index] = value
            self.notify_change()
    
    def delete_task_pattern(self, task_name: str, index: int):
        """Delete a task pattern"""
        if ("taskPatterns" in self.patterns_data and 
            task_name in self.patterns_data["taskPatterns"] and
            0 <= index < len(self.patterns_data["taskPatterns"][task_name])):
            del self.patterns_data["taskPatterns"][task_name][index]
            self.refresh_task_patterns()
            self.notify_change()
    
    def notify_change(self):
        """Notify parent of changes"""
        if self.on_change_callback:
            self.on_change_callback()
    
    def get_frame(self):
        """Get the main frame"""
        return self.main_frame 