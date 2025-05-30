#!/usr/bin/env python3
"""
Test script for the new multi-stage progress panel.

This script demonstrates the beautiful progress panel in action
without needing to run the full application.
"""

import tkinter as tk
import customtkinter as ctk
import time
import threading
from python.gui_components.progress_panel import ProgressPanel

# Set appearance mode and theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ProgressTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Progress Panel Test")
        self.geometry("800x600")
        
        # Create main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create test frame
        self.test_frame = ctk.CTkFrame(self)
        self.test_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.test_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.test_frame,
            text="Multi-Stage Progress Panel Demo",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Create progress panel
        self.progress_panel = ProgressPanel(self.test_frame)
        
        # Control buttons
        button_frame = ctk.CTkFrame(self.test_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=20)
        
        start_btn = ctk.CTkButton(
            button_frame,
            text="Start Demo Scan",
            command=self.start_demo_scan
        )
        start_btn.pack(side="left", padx=10)
        
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset",
            command=self.reset_progress
        )
        reset_btn.pack(side="left", padx=10)
        
        error_btn = ctk.CTkButton(
            button_frame,
            text="Demo Error",
            command=self.demo_error,
            fg_color="red",
            hover_color="darkred"
        )
        error_btn.pack(side="left", padx=10)
        
        # Initially hide progress panel
        self.progress_panel.hide()

    def start_demo_scan(self):
        """Start a demonstration of the scan progress."""
        # Show and reset progress panel
        self.progress_panel.reset()
        self.progress_panel.show()
        
        # Run demo in background thread
        demo_thread = threading.Thread(target=self._demo_scan_worker, daemon=True)
        demo_thread.start()

    def reset_progress(self):
        """Reset the progress panel."""
        self.progress_panel.reset()
        self.progress_panel.hide()

    def demo_error(self):
        """Demonstrate error handling."""
        self.progress_panel.reset()
        self.progress_panel.show()
        
        # Show validation error
        self.progress_panel.start_stage('validation', 'Checking inputs...')
        self.after(1000, lambda: self.progress_panel.error_stage('validation', 'Invalid source folder'))

    def _demo_scan_worker(self):
        """Worker thread that simulates a complete scan operation."""
        try:
            # Stage 1: Validation (quick, no progress bar)
            self.after(0, lambda: self.progress_panel.start_stage('validation', 'Validating inputs...'))
            time.sleep(0.8)  # Quick validation
            self.after(0, lambda: self.progress_panel.complete_stage('validation', 'All inputs valid'))
            
            # Stage 2: Scanning (has progress bar)
            self.after(0, lambda: self.progress_panel.start_stage('scanning', 'Starting file scan...'))
            time.sleep(0.3)
            
            # Simulate file scanning with progress updates
            total_files = 50  # Reduced for faster demo
            for i in range(total_files + 1):
                progress = i / total_files
                files_count = i
                folders_count = i // 8
                
                detail_msg = f"{files_count} files, {folders_count} folders"
                if i < total_files:
                    detail_msg += f" • file_{i:03d}.exr"
                else:
                    detail_msg = f"Scan complete: {files_count} files"
                
                self.after(0, lambda p=progress, d=detail_msg: self.progress_panel.update_stage_progress('scanning', p, d))
                time.sleep(0.04)  # Faster updates for demo
            
            self.after(0, lambda: self.progress_panel.complete_stage('scanning', f'Found {total_files} files'))
            
            # Stage 3: Mapping (has progress bar)
            self.after(0, lambda: self.progress_panel.start_stage('mapping', 'Generating mappings...'))
            time.sleep(0.3)
            
            # Simulate mapping generation with file processing
            total_mapping_files = 30
            for i in range(total_mapping_files + 1):
                progress = i / total_mapping_files
                detail_msg = f"Processing file {i}/{total_mapping_files}"
                if i < total_mapping_files:
                    detail_msg += f" • mapping_{i:03d}.exr"
                else:
                    detail_msg = "Mapping complete"
                
                self.after(0, lambda p=progress, d=detail_msg: self.progress_panel.update_stage_progress('mapping', p, d))
                time.sleep(0.06)  # Slightly slower to show progress
            
            self.after(0, lambda: self.progress_panel.complete_stage('mapping', 'Generated 87 mapping proposals'))
            
            # Stage 4: Processing (quick, no progress bar)
            self.after(0, lambda: self.progress_panel.start_stage('processing', 'Processing results...'))
            time.sleep(0.8)  # Quick processing
            self.after(0, lambda: self.progress_panel.complete_stage('processing', 'Results processed for GUI'))
            
            # Stage 5: Complete (final state, no progress bar)
            self.after(0, lambda: self.progress_panel.complete_stage('complete', 'Operation successful!'))
            
            # Auto-hide after 4 seconds
            self.after(4000, self.progress_panel.hide)
            
        except Exception as e:
            self.after(0, lambda: self.progress_panel.error_stage('scanning', f'Demo error: {e}'))

if __name__ == "__main__":
    app = ProgressTestApp()
    app.mainloop() 