"""
Progress Panel Module

Provides a beautiful multi-stage progress display with check indicators
for the scanning and mapping process as a detached popup window.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class StageStatus(Enum):
    """Status of each progress stage."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class ProgressPanel(ctk.CTkToplevel):
    """
    Multi-stage progress panel as a detached popup window with improved error handling and rate limiting.
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Window configuration
        self.title("Scanning Progress")
        self.geometry("500x350")
        self.resizable(True, False)
        
        # Keep window on top but not modal
        self.attributes("-topmost", True)
        
        # Rate limiting for progress updates
        self.last_update_time = 0
        self.min_update_interval = 0.1  # Minimum 100ms between updates
        self.pending_update = False
        
        # Error handling
        self.update_errors = 0
        self.max_update_errors = 10
        
        # Define the stages for scanning with consistent theming
        self.stages = [
            {
                'id': 'initialization',
                'title': '1. Initialization',
                'icon_pending': '⏳',
                'icon_progress': '🔄',
                'icon_completed': '✅',
                'icon_error': '❌',
                'has_progress': False  # Simple status only
            },
            {
                'id': 'collection',
                'title': '2. File Collection',
                'icon_pending': '⏳',
                'icon_progress': '📁',
                'icon_completed': '✅',
                'icon_error': '❌',
                'has_progress': False  # Removed progress bar, text only
            },
            {
                'id': 'sequencing',
                'title': '3. Sequence Detection',
                'icon_pending': '⏳',
                'icon_progress': '🔍',
                'icon_completed': '✅',
                'icon_error': '❌',
                'has_progress': True  # Progress bar
            },
            {
                'id': 'mapping',
                'title': '4. Path Mapping',
                'icon_pending': '⏳',
                'icon_progress': '🗺️',
                'icon_completed': '✅',
                'icon_error': '❌',
                'has_progress': True  # Progress bar
            },
            {
                'id': 'processing',
                'title': '5. Final Processing',
                'icon_pending': '⏳',
                'icon_progress': '⚙️',
                'icon_completed': '✅',
                'icon_error': '❌',
                'has_progress': False  # Simple status only
            }
        ]
        
        # Track stage status
        self.stage_status = {stage['id']: StageStatus.PENDING for stage in self.stages}
        self.stage_progress = {stage['id']: 0.0 for stage in self.stages}
        self.stage_details = {stage['id']: '' for stage in self.stages}
        self.stage_widgets = {}
        self.current_stage = None
        
        # Create the UI
        self.create_ui()
        
        # Hide initially
        self.withdraw()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def hide_window(self):
        """Hide the progress window."""
        self.withdraw()

    def show_window(self):
        """Show the progress window."""
        self.deiconify()
        self.lift()
        self.focus()

    def _can_update(self) -> bool:
        """Check if we can update based on rate limiting and error count."""
        current_time = time.time()
        
        # Rate limiting check
        if current_time - self.last_update_time < self.min_update_interval:
            if not self.pending_update:
                # Schedule a delayed update
                self.pending_update = True
                self.after(int(self.min_update_interval * 1000), self._delayed_update)
            return False
        
        # Error count check
        if self.update_errors >= self.max_update_errors:
            return False
        
        return True

    def _delayed_update(self):
        """Handle delayed updates for rate limiting."""
        self.pending_update = False
        if self._can_update():
            self._safe_update_display()

    def _safe_update_display(self):
        """Safely update display with error handling."""
        try:
            self.last_update_time = time.time()
            self._update_display_core()
            # Reset error count on successful update
            if self.update_errors > 0:
                self.update_errors = max(0, self.update_errors - 1)
        except RecursionError as e:
            self.update_errors += 1
            print(f"[PROGRESS_PANEL_ERROR] RecursionError in display update (count: {self.update_errors}): {e}")
            if self.update_errors >= self.max_update_errors:
                print(f"[PROGRESS_PANEL_ERROR] Too many update errors, disabling updates")
        except Exception as e:
            self.update_errors += 1
            print(f"[PROGRESS_PANEL_ERROR] Error in display update (count: {self.update_errors}): {e}")

    def create_ui(self):
        """Create the progress panel UI."""
        # Configure main window grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with close button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Scanning Progress",
            font=ctk.CTkFont(size=28, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Hide button
        hide_btn = ctk.CTkButton(
            header_frame,
            text="Hide",
            command=self.hide_window,
            width=60,
            height=25
        )
        hide_btn.grid(row=0, column=2, sticky="e")
        
        # Main progress container
        self.progress_frame = ctk.CTkFrame(self, corner_radius=8)
        self.progress_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        # Overall progress bar
        self.overall_progress = ctk.CTkProgressBar(
            self.progress_frame,
            orientation="horizontal",
            mode="determinate",
            height=8
        )
        self.overall_progress.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.overall_progress.set(0.0)
        
        # Create individual stage widgets
        for i, stage in enumerate(self.stages):
            self._create_stage_widget(stage, i + 1)  # Start from row 1

    def _create_stage_widget(self, stage: Dict[str, Any], row: int):
        """Create widgets for a single stage with improved error handling."""
        # Stage container
        stage_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        stage_frame.grid(row=row, column=0, padx=15, pady=2, sticky="ew")
        stage_frame.grid_columnconfigure(1, weight=1)  # Title column expands
        
        # Status icon
        icon_label = ctk.CTkLabel(
            stage_frame,
            text=stage['icon_pending'],
            font=ctk.CTkFont(size=28),
            width=50,
            text_color=("gray60", "gray40")
        )
        icon_label.grid(row=0, column=0, padx=(5, 8), pady=3, sticky="w")
        
        # Stage title
        title_label = ctk.CTkLabel(
            stage_frame,
            text=stage['title'],
            font=ctk.CTkFont(size=22, weight="normal"),
            anchor="w",
            text_color=("gray70", "gray30")
        )
        title_label.grid(row=0, column=1, padx=0, pady=3, sticky="ew")
        
        if stage.get('has_progress', False):
            # Progress bar for this stage
            progress_bar = ctk.CTkProgressBar(
                stage_frame,
                orientation="horizontal",
                mode="determinate",
                height=6,
                width=120
            )
            progress_bar.grid(row=0, column=2, padx=(5, 0), pady=3, sticky="e")
            
            # Set initial value safely
            try:
                progress_bar.set(0.0)
            except Exception as e:
                print(f"[PROGRESS_PANEL_ERROR] Failed to initialize progress bar for stage {stage['id']}: {e}")
            
            # Details label for progress stages
            details_label = ctk.CTkLabel(
                stage_frame,
                text="",
                font=ctk.CTkFont(size=18),
                anchor="e",
                text_color=("gray50", "gray60")
            )
            details_label.grid(row=1, column=1, columnspan=2, padx=(0, 8), pady=(0, 3), sticky="e")
            
            # Store widgets for this stage
            self.stage_widgets[stage['id']] = {
                'icon': icon_label,
                'title': title_label,
                'progress': progress_bar,
                'details': details_label
            }
        else:
            # No progress bar for simple status stages, but add details label for text updates
            details_label = ctk.CTkLabel(
                stage_frame,
                text="",
                font=ctk.CTkFont(size=18),
                anchor="e",
                text_color=("gray50", "gray60")
            )
            details_label.grid(row=1, column=1, columnspan=1, padx=(0, 8), pady=(0, 3), sticky="e")
            
            self.stage_widgets[stage['id']] = {
                'icon': icon_label,
                'title': title_label,
                'details': details_label  # Add details label even without progress bar
            }

    def _update_display_core(self):
        """Core display update logic without excessive UI calls."""
        if self.update_errors >= self.max_update_errors:
            return  # Skip updates if too many errors
        
        completed_stages = 0
        total_stages = len(self.stages)
        
        for stage in self.stages:
            stage_id = stage['id']
            widgets = self.stage_widgets.get(stage_id)
            if not widgets:
                continue
                
            status = self.stage_status[stage_id]
            progress = self.stage_progress[stage_id]
            details = self.stage_details[stage_id]
            
            # Update icon
            if status == StageStatus.PENDING:
                icon = stage['icon_pending']
                icon_color = ("gray60", "gray40")
            elif status == StageStatus.IN_PROGRESS:
                icon = stage['icon_progress']
                icon_color = ("blue", "lightblue")
            elif status == StageStatus.COMPLETED:
                icon = stage['icon_completed']
                icon_color = ("green", "lightgreen")
                completed_stages += 1
            elif status == StageStatus.ERROR:
                icon = stage['icon_error']
                icon_color = ("red", "lightcoral")
            else:
                icon = stage['icon_pending']
                icon_color = ("gray60", "gray40")
            
            try:
                widgets['icon'].configure(text=icon, text_color=icon_color)
            except Exception as e:
                print(f"[PROGRESS_PANEL_ERROR] Error updating icon for {stage_id}: {e}")
                continue
            
            # Update title color based on status
            if status == StageStatus.COMPLETED:
                text_color = ("green", "lightgreen")
            elif status == StageStatus.ERROR:
                text_color = ("red", "lightcoral")
            elif status == StageStatus.IN_PROGRESS:
                text_color = ("blue", "lightblue")
            else:
                text_color = ("gray70", "gray30")
            
            try:
                widgets['title'].configure(text_color=text_color)
            except Exception as e:
                print(f"[PROGRESS_PANEL_ERROR] Error updating title for {stage_id}: {e}")
                continue
            
            # Update progress bar and details only for stages that have them
            if 'progress' in widgets:
                try:
                    # Safely update progress bar without aggressive refresh
                    widgets['progress'].set(progress)
                except Exception as e:
                    print(f"[PROGRESS_PANEL_ERROR] Error updating progress bar for {stage_id}: {e}")
                    continue
            
            # Update details text for any stage that has a details widget
            if 'details' in widgets and details:
                try:
                    # Truncate details if too long
                    display_details = details[:40] + "..." if len(details) > 40 else details
                    widgets['details'].configure(text=display_details)
                except Exception as e:
                    print(f"[PROGRESS_PANEL_ERROR] Error updating details for {stage_id}: {e}")
        
        # Update overall progress safely
        try:
            overall_progress = completed_stages / total_stages if total_stages > 0 else 0
            self.overall_progress.set(overall_progress)
        except Exception as e:
            print(f"[PROGRESS_PANEL_ERROR] Error updating overall progress: {e}")

    def show(self):
        """Show the progress panel."""
        self.show_window()

    def hide(self):
        """Hide the progress panel."""
        self.hide_window()

    def reset(self):
        """Reset all stages to pending state."""
        self.current_stage = None
        self.update_errors = 0  # Reset error count
        for stage_id in self.stage_status:
            self.stage_status[stage_id] = StageStatus.PENDING
            self.stage_progress[stage_id] = 0.0
            self.stage_details[stage_id] = ''
        
        try:
            self.overall_progress.set(0.0)
        except Exception as e:
            print(f"[PROGRESS_PANEL_ERROR] Error resetting overall progress: {e}")
        
        self._safe_update_display()

    def start_stage(self, stage_id: str, details: str = ""):
        """Start a specific stage."""
        if stage_id in self.stage_status:
            self.current_stage = stage_id
            self.stage_status[stage_id] = StageStatus.IN_PROGRESS
            self.stage_details[stage_id] = details
            self._safe_update_display()

    def update_stage_progress(self, stage_id: str, progress: float, details: str = ""):
        """Update progress for a specific stage with rate limiting."""
        if stage_id in self.stage_progress:
            # Validate progress value
            progress = max(0.0, min(1.0, float(progress))) if isinstance(progress, (int, float)) else 0.0
            
            old_progress = self.stage_progress[stage_id]
            self.stage_progress[stage_id] = progress
            if details:
                self.stage_details[stage_id] = details
            
            # Only update display if we can (rate limiting)
            if self._can_update():
                self._safe_update_display()

    def complete_stage(self, stage_id: str, details: str = ""):
        """Mark a stage as completed."""
        if stage_id in self.stage_status:
            self.stage_status[stage_id] = StageStatus.COMPLETED
            self.stage_progress[stage_id] = 1.0
            if details:
                self.stage_details[stage_id] = details
            self._safe_update_display()

    def error_stage(self, stage_id: str, error_message: str = ""):
        """Mark a stage as having an error."""
        if stage_id in self.stage_status:
            self.stage_status[stage_id] = StageStatus.ERROR
            self.stage_details[stage_id] = error_message
            self._safe_update_display()

    def get_current_stage(self):
        """Get the current active stage."""
        return self.current_stage

    def is_complete(self):
        """Check if all stages are completed."""
        return all(status == StageStatus.COMPLETED for status in self.stage_status.values())

    def has_errors(self) -> bool:
        """Check if any stage has errors."""
        return any(status == StageStatus.ERROR for status in self.stage_status.values()) 