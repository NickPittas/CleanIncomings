"""
Status Manager Module - PyQt5 Compatible

Handles status updates, progress reporting, and logging functionality
for the Clean Incomings GUI application.
"""

import datetime
import threading
from typing import Dict, Any, Optional
from PyQt5.QtCore import QTimer


class StatusManager:
    """Manages status updates, progress reporting, and logging for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the StatusManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.current_transfer_info = {
            'file_name': '',
            'speed_mbps': 0.0,
            'eta_str': 'Calculating...',
            'percent': 0.0,
            'status': 'idle'
        }
        self.scan_in_progress = False
        
        # Rate limiting for UI updates
        self.last_ui_update = 0
        self.min_ui_update_interval = 0.1  # Minimum 100ms between UI updates
        self.pending_ui_update = False

    def start_scan_progress(self):
        """Start the scan progress indication."""
        self.scan_in_progress = True
        if hasattr(self.app, 'status_label'):
            self.app.status_label.setText("Starting scan...")
        print("Scan progress started")

    def complete_validation_stage(self):
        """Complete the validation stage."""
        if hasattr(self.app, 'status_label'):
            self.app.status_label.setText("Validation completed...")
        print("Validation stage completed")

    def finish_scan_progress(self, success: bool, message: str = ""):
        """Finish the scan progress indication."""
        self.scan_in_progress = False
        if hasattr(self.app, 'status_label'):
            if success:
                self.app.status_label.setText("Scan completed successfully")
            else:
                self.app.status_label.setText(f"Scan failed: {message}")
        print(f"Scan progress finished: success={success}, message={message}")

    def set_status(self, message: str):
        """Set the status message."""
        if hasattr(self.app, 'status_label'):
            self.app.status_label.setText(message)
        print(f"Status: {message}")

    def update_progress(self, percent: float, message: str = ""):
        """Update progress indication."""
        # For now, just update the status label
        # TODO: Add actual progress bar when implementing progress panel
        if message:
            self.set_status(f"{message} ({percent:.1f}%)")
        else:
            self.set_status(f"Progress: {percent:.1f}%")

    def add_log_message(self, message: str, level: str = "INFO"):
        """Add a log message."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        # TODO: Add to log display when implementing log panel
        
    def update_file_transfer_info(self, file_name: str, speed_mbps: float, eta_str: str, percent: float):
        """Update file transfer information."""
        self.current_transfer_info.update({
            'file_name': file_name,
            'speed_mbps': speed_mbps,
            'eta_str': eta_str,
            'percent': percent,
            'status': 'transferring'
        })
        
        # Update status with transfer info
        status_msg = f"Copying: {file_name} ({percent:.1f}%) - {speed_mbps:.2f} MB/s - ETA: {eta_str}"
        self.set_status(status_msg)
