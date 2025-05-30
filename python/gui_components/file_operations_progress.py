"""
File Operations Progress Panel

Displays detailed progress information for file copy/move operations.
Shows individual file progress, overall batch progress, speeds, and ETAs.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional
import threading
import time


class FileOperationProgress:
    """Represents the progress state of a single file operation."""
    
    def __init__(self, transfer_id: str, file_name: str, operation: str, total_size: int = 0):
        self.transfer_id = transfer_id
        self.file_name = file_name
        self.operation = operation  # 'copy' or 'move'
        self.total_size = total_size
        self.transferred_bytes = 0
        self.status = 'pending'  # pending, active, completed, failed, cancelled
        self.speed_mbps = 0.0
        self.eta_str = 'Calculating...'
        self.start_time = time.time()
        self.completion_time = None
        self.error_message = None


class FileOperationsProgressWindow(ctk.CTkToplevel):
    """Moveable progress window for file operations."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Window configuration - made larger and will be centered
        self.title("File Operations Progress")
        self.geometry("800x600")  # Increased from 600x400
        self.resizable(True, True)
        
        # Keep window on top but not modal
        self.attributes("-topmost", True)
        
        # Center the window on the parent app
        self._center_on_parent()
        
        # Data storage
        self.active_transfers = {}  # Only store active transfers
        self.transfer_widgets = {}  # Store widget references
        self.completed_count = 0
        self.failed_count = 0
        self.total_files = 0
        self.operation_type = "Copy"
        self.batch_start_time = time.time()
        
        # UI components
        self.create_ui()
        
        # Hide initially
        self.withdraw()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def _center_on_parent(self):
        """Center the window on the parent application."""
        if self.parent:
            # Get parent window geometry
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Calculate center position
            window_width = 800
            window_height = 600
            x = parent_x + (parent_width // 2) - (window_width // 2)
            y = parent_y + (parent_height // 2) - (window_height // 2)
            
            # Set position
            self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_ui(self):
        """Create the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Transfer list area
        
        # Header
        self.create_header()
        
        # Overall progress
        self.create_overall_progress()
        
        # Active transfers list (scrollable)
        self.create_transfer_list()
        
        # Controls
        self.create_controls()

    def create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="File Operations",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Ready",
            font=ctk.CTkFont(size=18)
        )
        self.status_label.grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

    def create_overall_progress(self):
        """Create overall progress section."""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        progress_frame.grid_columnconfigure(1, weight=1)
        
        # Overall progress bar (shows batch progress)
        ctk.CTkLabel(progress_frame, text="Overall:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.overall_progress_bar = ctk.CTkProgressBar(progress_frame)
        self.overall_progress_bar.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.overall_progress_bar.set(0)
        
        self.overall_progress_label = ctk.CTkLabel(progress_frame, text="0.0%")
        self.overall_progress_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        # File count and statistics
        self.stats_label = ctk.CTkLabel(
            progress_frame,
            text="Files: 0/0 • Speed: 0 MB/s • ETA: --",
            font=ctk.CTkFont(size=15)
        )
        self.stats_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0,5), sticky="w")

    def create_transfer_list(self):
        """Create scrollable list for active transfers only."""
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            list_frame,
            text="Active Transfers (max 10 shown)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")
        
        # Scrollable frame for transfers
        self.transfers_scroll = ctk.CTkScrollableFrame(list_frame, height=200)
        self.transfers_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.transfers_scroll.grid_columnconfigure(0, weight=1)

    def create_controls(self):
        """Create control buttons."""
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5,10))
        
        self.pause_all_btn = ctk.CTkButton(
            controls_frame,
            text="Pause All",
            command=self.pause_all_transfers,
            width=100
        )
        self.pause_all_btn.pack(side="left", padx=10, pady=10)
        
        self.cancel_all_btn = ctk.CTkButton(
            controls_frame,
            text="Cancel All",
            command=self.cancel_all_transfers,
            width=100
        )
        self.cancel_all_btn.pack(side="left", padx=5, pady=10)
        
        self.hide_btn = ctk.CTkButton(
            controls_frame,
            text="Hide",
            command=self.hide_window,
            width=80
        )
        self.hide_btn.pack(side="right", padx=10, pady=10)

    def show_window(self):
        """Show the progress window."""
        self.deiconify()
        self.lift()
        self.focus()
        # Re-center when showing
        self._center_on_parent()

    def hide_window(self):
        """Hide the progress window."""
        self.withdraw()

    def start_operation_batch(self, operation_type: str, total_files: int):
        """Start a new batch operation."""
        # Initialize overall batch tracking on first call or operation type change
        if not hasattr(self, 'overall_total_files') or self.operation_type != operation_type:
            # New operation - reset everything
            self.operation_type = operation_type
            self.overall_total_files = total_files
            self.overall_completed_count = 0
            self.overall_failed_count = 0
            self.batch_start_time = time.time()
            self.active_transfers.clear()
            self.clear_transfer_widgets()
            
            # Reset sequence tracking
            self.total_files = total_files
            self.completed_count = 0
            self.failed_count = 0
        else:
            # Same operation continuing - accumulate totals but don't clear active transfers
            self.overall_total_files += total_files
            # Reset current sequence counters but keep overall counters
            self.total_files = total_files
            self.completed_count = 0
            self.failed_count = 0
        
        # Update UI
        self.title_label.configure(text=f"{operation_type} Operations")
        self.status_label.configure(text=f"Starting {operation_type.lower()} of {self.overall_total_files} files...")
        self.update_overall_progress()
        
        # Show window
        self.show_window()

    def add_transfer(self, transfer_id: str, file_name: str, operation: str, total_size: int = 0):
        """Add a new transfer (store all for progress tracking, display max 10)."""
        # Always store the transfer for progress tracking
        transfer = FileOperationProgress(transfer_id, file_name, operation, total_size)
        transfer.status = 'active'
        self.active_transfers[transfer_id] = transfer
        
        # Only create widget if we have room for display (limit visual displays to 10)
        if len(self.transfer_widgets) < 10:
            self.create_transfer_widget(transfer_id, transfer)
        
        # Always update overall progress
        self.update_overall_progress()

    def update_transfer_progress(self, transfer_id: str, transferred_bytes: int, speed_mbps: float, eta_str: str, status: str, percent: float = None):
        """Update transfer progress."""
        if transfer_id in self.active_transfers:
            transfer = self.active_transfers[transfer_id]
            transfer.transferred_bytes = transferred_bytes
            transfer.speed_mbps = speed_mbps
            transfer.eta_str = eta_str
            transfer.status = status
            
            # Store the actual percentage if provided (for sequence operations)
            if percent is not None:
                transfer.actual_percent = percent
            
            # Mark completion time if transfer is done
            if transferred_bytes >= transfer.total_size and transfer.total_size > 0:
                transfer.completion_time = time.time()
            elif percent is not None and percent >= 100:
                transfer.completion_time = time.time()
            
            self.update_transfer_widget(transfer_id)
            
            # Update overall progress every time individual progress is updated
            self.update_overall_progress()
        else:
            print(f"DEBUG: Transfer ID {transfer_id} not found in active_transfers (may be completed or not yet added)")

    def complete_transfer(self, transfer_id: str, success: bool, message: str = ""):
        """Mark transfer as complete and remove from active display after a delay."""
        # Update counters - both current sequence and overall
        if success:
            self.completed_count += 1
            if hasattr(self, 'overall_completed_count'):
                self.overall_completed_count += 1
        else:
            self.failed_count += 1
            if hasattr(self, 'overall_failed_count'):
                self.overall_failed_count += 1
        
        # Keep the transfer visible for a few seconds with final status
        if transfer_id in self.active_transfers:
            transfer = self.active_transfers[transfer_id]
            transfer.status = 'completed' if success else 'failed'
            transfer.completion_time = time.time()
            
            # Update the widget one final time with completion status
            self.update_transfer_widget(transfer_id)
            
            # Schedule removal after 2 seconds to let user see final speed
            self.after(2000, lambda: self._delayed_transfer_removal(transfer_id))
        
        # Update overall progress
        self.update_overall_progress()
        
        # Check if current sequence is complete (but not the entire overall batch)
        if self.completed_count + self.failed_count >= self.total_files:
            # Current sequence is complete, but check if overall batch is complete
            overall_completed = getattr(self, 'overall_completed_count', 0) + getattr(self, 'overall_failed_count', 0)
            overall_total = getattr(self, 'overall_total_files', self.total_files)
            
            if overall_completed >= overall_total:
                # Entire operation is complete
                self.on_batch_complete()
            # If just this sequence is complete but overall operation continues, don't call on_batch_complete

    def _delayed_transfer_removal(self, transfer_id: str):
        """Remove transfer from display after showing final status and show next pending transfer."""
        if transfer_id in self.active_transfers:
            # Remove from active tracking only if completed/failed
            transfer = self.active_transfers[transfer_id]
            if transfer.status in ['completed', 'failed']:
                del self.active_transfers[transfer_id]
            
            # Remove from display
            self.remove_transfer_widget(transfer_id)
            
            # Try to show a pending transfer that isn't currently displayed
            if len(self.transfer_widgets) < 10:
                for pending_id, pending_transfer in self.active_transfers.items():
                    if pending_id not in self.transfer_widgets and pending_transfer.status == 'active':
                        self.create_transfer_widget(pending_id, pending_transfer)
                        break

    def create_transfer_widget(self, transfer_id: str, transfer: FileOperationProgress):
        """Create widget for a transfer."""
        # Create frame for this transfer
        transfer_frame = ctk.CTkFrame(self.transfers_scroll)
        transfer_frame.grid(sticky="ew", padx=5, pady=2)
        transfer_frame.grid_columnconfigure(1, weight=1)
        
        # File name
        name_label = ctk.CTkLabel(
            transfer_frame,
            text=transfer.file_name[:40] + "..." if len(transfer.file_name) > 40 else transfer.file_name,
            font=ctk.CTkFont(size=15)
        )
        name_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5,0), sticky="w")
        
        # Progress bar
        progress_bar = ctk.CTkProgressBar(transfer_frame, width=200)
        progress_bar.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        progress_bar.set(0)
        
        # Progress info
        info_label = ctk.CTkLabel(
            transfer_frame,
            text="Starting...",
            font=ctk.CTkFont(size=14)
        )
        info_label.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        # Store references
        transfer_frame._progress_bar = progress_bar
        transfer_frame._info_label = info_label
        transfer_frame._transfer_id = transfer_id
        
        # Store widget reference
        self.transfer_widgets[transfer_id] = transfer_frame

    def update_transfer_widget(self, transfer_id: str):
        """Update transfer widget display."""
        if transfer_id not in self.transfer_widgets:
            return
            
        transfer = self.active_transfers.get(transfer_id)
        if not transfer:
            return
            
        widget = self.transfer_widgets[transfer_id]
        
        # Update progress bar - use actual percentage if available (for sequence operations)
        if transfer.status == 'completed':
            widget._progress_bar.set(1.0)  # 100% when completed
        elif transfer.status == 'failed':
            widget._progress_bar.set(0)    # 0% when failed
        elif hasattr(transfer, 'actual_percent') and transfer.actual_percent is not None:
            # Use the actual percentage from sequence operation callback
            progress = min(transfer.actual_percent / 100.0, 1.0)
            widget._progress_bar.set(progress)
        elif transfer.total_size > 0:
            # For transfers with known size, use byte progress
            progress = min(transfer.transferred_bytes / transfer.total_size, 1.0)
            widget._progress_bar.set(progress)
        else:
            # For sequence batches with no percentage info, show indeterminate progress (50%)
            widget._progress_bar.set(0.5)
        
        # Update info label with better formatting based on status
        if transfer.status == 'completed':
            info_text = f"✓ Completed • {transfer.speed_mbps:.1f} MB/s"
        elif transfer.status == 'failed':
            info_text = f"✗ Failed"
        elif transfer.speed_mbps > 0:
            info_text = f"{transfer.speed_mbps:.1f} MB/s • {transfer.eta_str}"
        else:
            info_text = f"Starting... • {transfer.eta_str}"
        
        widget._info_label.configure(text=info_text)

    def remove_transfer_widget(self, transfer_id: str):
        """Remove transfer widget from display."""
        if transfer_id in self.transfer_widgets:
            widget = self.transfer_widgets[transfer_id]
            widget.destroy()
            del self.transfer_widgets[transfer_id]

    def clear_transfer_widgets(self):
        """Clear all transfer widgets."""
        for widget in self.transfer_widgets.values():
            widget.destroy()
        self.transfer_widgets.clear()

    def update_overall_progress(self):
        """Update overall progress by averaging percentages from all active transfers."""
        current_aggregate_speed = 0.0
        active_transfer_count = 0
        current_time = time.time()
        
        # Calculate real-time overall progress by averaging individual transfer percentages
        total_progress = 0.0
        transfer_count = 0
        completed_transfers = 0
        
        for transfer in self.active_transfers.values():
            transfer_count += 1
            
            # Get progress percentage for this transfer
            if transfer.status == 'completed':
                total_progress += 100.0  # Completed transfers contribute 100%
                completed_transfers += 1
            elif transfer.status == 'failed':
                total_progress += 0.0   # Failed transfers contribute 0%
            elif hasattr(transfer, 'actual_percent') and transfer.actual_percent is not None:
                # Use actual percentage from sequence operations
                total_progress += transfer.actual_percent
            elif transfer.total_size > 0:
                # Calculate percentage from bytes for individual file transfers
                file_progress = min(transfer.transferred_bytes / transfer.total_size * 100.0, 100.0)
                total_progress += file_progress
            else:
                # Default to 0% for transfers without progress info
                total_progress += 0.0
            
            # Sum up speeds from active transfers for display
            if transfer.status == 'active' and transfer.speed_mbps > 0:
                current_aggregate_speed += transfer.speed_mbps
                active_transfer_count += 1
            # For recently completed transfers, include their final speed
            elif transfer.status in ['completed', 'failed'] and transfer.completion_time:
                if current_time - transfer.completion_time <= 3.0 and transfer.speed_mbps > 0:
                    current_aggregate_speed += transfer.speed_mbps
        
        # Calculate overall progress percentage by averaging all transfers
        if transfer_count > 0:
            overall_progress = total_progress / transfer_count / 100.0  # Convert to 0-1 range
            self.overall_progress_bar.set(overall_progress)
            self.overall_progress_label.configure(text=f"{overall_progress * 100:.1f}%")
        else:
            self.overall_progress_bar.set(0)
            self.overall_progress_label.configure(text="0.0%")
        
        # Calculate ETA based on transfer completion rate
        eta_str = "--"
        if completed_transfers > 0 and transfer_count > completed_transfers:
            elapsed = time.time() - getattr(self, 'batch_start_time', time.time())
            completion_rate = completed_transfers / elapsed if elapsed > 0 else 0
            
            if completion_rate > 0:
                remaining_transfers = transfer_count - completed_transfers
                eta_seconds = remaining_transfers / completion_rate
                
                if eta_seconds < 60:
                    eta_str = f"{int(eta_seconds)}s"
                elif eta_seconds < 3600:
                    eta_str = f"{int(eta_seconds//60)}m {int(eta_seconds%60)}s"
                else:
                    eta_str = f"{int(eta_seconds//3600)}h {int((eta_seconds%3600)//60)}m"
        elif completed_transfers >= transfer_count and transfer_count > 0:
            eta_str = "Complete"
        
        # Update stats with transfer count and aggregate information
        stats_text = f"Transfers: {completed_transfers}/{transfer_count} • Speed: {current_aggregate_speed:.1f} MB/s • ETA: {eta_str}"
        self.stats_label.configure(text=stats_text)

    def on_batch_complete(self):
        """Handle batch completion."""
        elapsed = time.time() - self.batch_start_time
        overall_completed = getattr(self, 'overall_completed_count', self.completed_count)
        overall_failed = getattr(self, 'overall_failed_count', self.failed_count)
        overall_total = getattr(self, 'overall_total_files', self.total_files)
        success_rate = (overall_completed / overall_total * 100) if overall_total > 0 else 0
        
        self.status_label.configure(
            text=f"Complete! {overall_completed} succeeded, {overall_failed} failed ({success_rate:.1f}%) in {elapsed:.1f}s"
        )
        
        # Clear active transfers after a delay
        self.after(3000, self.clear_transfer_widgets)

    def pause_all_transfers(self):
        """Pause all active transfers."""
        # Implement pause logic here
        pass

    def cancel_all_transfers(self):
        """Cancel all active transfers."""
        # Implement cancel logic here
        pass


class FileOperationsProgressPanel(ctk.CTkFrame):
    """Legacy panel - now just shows/hides the popup window."""
    
    def __init__(self, parent):
        super().__init__(parent, height=50)  # Minimal height
        self.parent = parent
        
        # Create the popup window
        self.progress_window = FileOperationsProgressWindow(parent)
        
        # Minimal UI - just a toggle button
        self.grid_columnconfigure(0, weight=1)
        
        toggle_btn = ctk.CTkButton(
            self,
            text="📊 Show File Operations Progress",
            command=self.toggle_window,
            height=30
        )
        toggle_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Hide this panel initially
        self.grid_remove()

    def toggle_window(self):
        """Toggle the progress window visibility."""
        if self.progress_window.winfo_viewable():
            self.progress_window.hide_window()
        else:
            self.progress_window.show_window()

    # Delegate all operations to the popup window
    def start_operation_batch(self, operation_type: str, file_count: int):
        self.grid(row=2, column=0, sticky="ew", padx=10, pady=5)  # Show toggle button
        return self.progress_window.start_operation_batch(operation_type, file_count)

    def add_transfer(self, transfer_id: str, file_name: str, operation: str, total_size: int = 0):
        return self.progress_window.add_transfer(transfer_id, file_name, operation, total_size)

    def update_transfer_progress(self, transfer_id: str, transferred_bytes: int, speed_mbps: float, eta_str: str, status: str, percent: float = None):
        return self.progress_window.update_transfer_progress(transfer_id, transferred_bytes, speed_mbps, eta_str, status, percent)

    def complete_transfer(self, transfer_id: str, success: bool, message: str = ""):
        return self.progress_window.complete_transfer(transfer_id, success, message) 