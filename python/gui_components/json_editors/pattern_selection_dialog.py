"""
Pattern Selection Dialog - Popup for selecting patterns for folders
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Callable, Optional


class PatternSelectionDialog:
    """Dialog for selecting patterns for a folder"""
    
    def __init__(self, parent, title: str, patterns_data: Dict, 
                 assigned_patterns: List[str], on_save_callback: Optional[Callable] = None):
        self.parent = parent
        self.title = title
        self.patterns_data = patterns_data
        self.assigned_patterns = assigned_patterns.copy()
        self.on_save_callback = on_save_callback
        self.pattern_vars = {}
        
        self.create_dialog()
        self.create_widgets()
    
    def create_dialog(self):
        """Create the dialog window"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Center on parent
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(1, weight=1)
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎨 Select Patterns",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Pattern selection area
        self.scroll_frame = ctk.CTkScrollableFrame(self.dialog)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Create pattern checkboxes organized by category
        self.create_pattern_checkboxes()
        
        # Buttons
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Select/Deselect all buttons
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="✅ Select All",
            command=self.select_all,
            width=100
        )
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="❌ Deselect All",
            command=self.deselect_all,
            width=100
        )
        deselect_all_btn.pack(side="left", padx=5)
        
        # Save/Cancel buttons
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=80
        )
        cancel_btn.pack(side="right", padx=5)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_selection,
            width=80
        )
        save_btn.pack(side="right", padx=5)
    
    def create_pattern_checkboxes(self):
        """Create organized pattern checkboxes with performance optimizations"""
        row = 0
        
        # Limit patterns to prevent UI overload
        max_patterns_per_category = 25
        
        # Get all available patterns
        all_patterns = self.get_all_pattern_options()
        
        if not all_patterns:
            no_patterns_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No patterns available. Please configure patterns.json first.",
                text_color=("gray60", "gray40")
            )
            no_patterns_label.grid(row=0, column=0, pady=20)
            return
        
        # Create sections for each pattern category
        for category, patterns in all_patterns.items():
            if not patterns:
                continue
            
            # Limit patterns to prevent too many widgets
            display_patterns = patterns[:max_patterns_per_category]
            
            # Category header
            category_label = ctk.CTkLabel(
                self.scroll_frame,
                text=f"📋 {category.replace('Patterns', '').title()} Patterns:",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            category_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=5, pady=(10, 5))
            row += 1
            
            # Create checkboxes in grid layout (4 columns max)
            col = 0
            for pattern in display_patterns:
                # Create checkbox variable
                var = tk.BooleanVar(value=pattern in self.assigned_patterns)
                self.pattern_vars[pattern] = var
                
                checkbox = ctk.CTkCheckBox(
                    self.scroll_frame,
                    text=pattern,
                    variable=var
                )
                checkbox.grid(row=row, column=col, sticky="w", padx=5, pady=2)
                
                col += 1
                if col >= 4:  # 4 columns max
                    col = 0
                    row += 1
            
            # Show "more patterns available" message if truncated
            if len(patterns) > max_patterns_per_category:
                more_label = ctk.CTkLabel(
                    self.scroll_frame,
                    text=f"... and {len(patterns) - max_patterns_per_category} more patterns available",
                    font=ctk.CTkFont(size=10),
                    text_color=("gray60", "gray40")
                )
                more_label.grid(row=row, column=0, columnspan=4, sticky="w", padx=5, pady=2)
                row += 1
            
            if col > 0:  # Move to next row if we didn't fill the last row
                row += 1
    
    def get_all_pattern_options(self) -> Dict[str, List[str]]:
        """Get all available patterns organized by category"""
        options = {}
        
        # Simple pattern lists
        for key in ["shotPatterns", "resolutionPatterns", "versionPatterns", "assetPatterns", "stagePatterns"]:
            patterns = self.patterns_data.get(key, [])
            if patterns:
                options[key] = patterns
        
        # Task patterns (nested structure)
        task_patterns = self.patterns_data.get("taskPatterns", {})
        if task_patterns:
            # Flatten task patterns - include both category names and individual patterns
            all_task_patterns = []
            for category, patterns in task_patterns.items():
                all_task_patterns.append(category)  # Include category name
                all_task_patterns.extend(patterns)  # Include all patterns in category
            
            if all_task_patterns:
                options["taskPatterns"] = sorted(set(all_task_patterns))  # Remove duplicates and sort
        
        return options
    
    def select_all(self):
        """Select all available patterns"""
        for var in self.pattern_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deselect all patterns"""
        for var in self.pattern_vars.values():
            var.set(False)
    
    def save_selection(self):
        """Save the selected patterns"""
        selected_patterns = []
        for pattern, var in self.pattern_vars.items():
            if var.get():
                selected_patterns.append(pattern)
        
        if self.on_save_callback:
            self.on_save_callback(selected_patterns)
        
        self.dialog.destroy() 