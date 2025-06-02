"""
Copy/Move Progress Window for PyQt5

A floating, non-blocking progress dialog for batch file copy/move operations, matching the scan progress window style.
Displays total progress, current file, speed, ETA, and supports soft pause/resume and immediate cancel.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import time

class CopyMoveProgressWindow(QDialog):
    # Signals for user actions
    pause_resume_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, operation_type="Copy", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{operation_type} Progress")
        # Batch statistics
        self.active_transfers = {}  # file_name -> {bytes_done, total_size, status}
        self.batch_start_time = time.time()
        self.total_files = 0
        self.total_bytes = 0
        self.files_done = 0
        self.bytes_done = 0
        self.speed_history = []
        self.last_speed_update = time.time()
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setModal(False)
        self.resize(480, 180)
        self.setMinimumWidth(420)
        self.setStyleSheet("QDialog { background: #232629; color: #F0F0F0; border: 2px solid #444; }"  # Match scan style
                           "QProgressBar { height: 22px; font-size: 11pt; }" 
                           "QLabel { font-size: 10pt; }")

        self.operation_type = operation_type
        self.is_paused = False
        self.last_update_time = time.time()
        self.speed_history = []  # For smoothing speed
        self.last_bytes_copied = 0
        self.last_speed_update = time.time()

        # UI Elements
        layout = QVBoxLayout(self)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.label_file = QLabel("File: ...")
        self.label_speed = QLabel("Speed: Calculating...")
        self.label_eta = QLabel("ETA: Calculating...")
        self.label_files = QLabel("Files: 0 / 0")
        self.label_bytes = QLabel("Bytes: 0 / 0")
        self.label_type = QLabel(f"Operation: {operation_type}")

        for lbl in [self.label_file, self.label_speed, self.label_eta, self.label_files, self.label_bytes, self.label_type]:
            layout.addWidget(lbl)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_pause_resume = QPushButton("Pause")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_close = QPushButton("Close")
        btn_layout.addWidget(self.btn_pause_resume)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_pause_resume.clicked.connect(self._on_pause_resume)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        self.btn_close.clicked.connect(self.close)

        # Timer for speed/ETA updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_speed_eta)
        self.timer.start(1000)  # 1s tick

        self._reset_stats()

    def _reset_stats(self):
        self.total_files = 0
        self.files_done = 0
        self.total_bytes = 0
        self.bytes_done = 0
        self.start_time = time.time()
        self.last_bytes_copied = 0
        self.speed_history = []
        self.last_speed_update = time.time()
        self.label_speed.setText("Speed: Calculating...")
        self.label_eta.setText("ETA: Calculating...")

    def set_total(self, total_files, total_bytes):
        """Set the total number of files and bytes for this operation."""
        self.total_files = total_files
        self.total_bytes = total_bytes
        self.label_files.setText(f"Files: 0 / {total_files}")
        self.label_bytes.setText(f"Bytes: 0 / {self._format_bytes(total_bytes)}")
        self.progress_bar.setValue(0)
        self._reset_stats()
        self.active_transfers = {}  # reset per batch
        self.batch_start_time = time.time()

    def update_aggregate_progress(self, files_copied, total_files):
        """
        Update the progress bar and file label for aggregate (multi-batch) progress.
        Args:
            files_copied (int): Total files copied so far (across all batches)
            total_files (int): Grand total files to copy (across all batches)
        """
        percent = int(100 * files_copied / total_files) if total_files else 0
        self.progress_bar.setValue(percent)
        self.label_files.setText(f"Files: {files_copied} / {total_files}")
        # Optionally, clear or simplify other labels in aggregate mode
        self.label_file.setText("File: (aggregate)")
        self.label_bytes.setText("")
        # Speed/ETA can be omitted or implemented with smoothing if desired
        self.label_speed.setText("")
        self.label_eta.setText("")


    def update_progress(self, files_done, bytes_done, current_file, file_size=None, status='active'):
        """
        (Legacy/optional) Update the progress window with per-file statistics for a single batch.
        Args:
            files_done (int): Number of files copied/moved so far
            bytes_done (int): Number of bytes copied/moved so far
            current_file (str): Path of the file currently being copied/moved
            file_size (int): Size of the current file (if available)
            status (str): Status of the current file ('active', 'completed', etc.)
        """
        # This method is not used in aggregate mode, but is preserved for single-batch or legacy support.
        if current_file:
            self.active_transfers.setdefault(current_file, {'bytes_done': 0, 'total_size': file_size or 0, 'status': 'active'})
            self.active_transfers[current_file]['bytes_done'] = bytes_done
            if file_size is not None:
                self.active_transfers[current_file]['total_size'] = file_size
            self.active_transfers[current_file]['status'] = status
        total_transferred = sum(f['bytes_done'] for f in self.active_transfers.values())
        total_size = sum(f['total_size'] for f in self.active_transfers.values()) or self.total_bytes
        files_completed = sum(1 for f in self.active_transfers.values() if f['status'] == 'completed' or (f['bytes_done'] >= f['total_size'] > 0))
        files_total = self.total_files or len(self.active_transfers)
        percent = int(100 * total_transferred / total_size) if total_size else 0
        self.progress_bar.setValue(percent)
        self.label_file.setText(f"File: {current_file}")
        self.label_files.setText(f"Files: {files_completed} / {files_total}")
        self.label_bytes.setText(f"Bytes: {self._format_bytes(total_transferred)} / {self._format_bytes(total_size)}")
        # Speed/ETA calculations (optional, only for single batch)
        now = time.time()
        elapsed = now - self.batch_start_time
        speed = total_transferred / elapsed if elapsed > 0 else 0
        if now - self.last_speed_update >= 1:
            self.speed_history.append(speed)
            if len(self.speed_history) > 5:
                self.speed_history.pop(0)
            smoothed_speed = sum(self.speed_history) / len(self.speed_history) if self.speed_history else 0
            self._set_speed(smoothed_speed)
            self._set_eta(smoothed_speed, total_size, total_transferred)
            self.last_speed_update = now
        self.files_done = files_completed
        self.bytes_done = total_transferred

    def _set_speed(self, speed_bps):
        mbps = speed_bps / (1024 * 1024)
        self.label_speed.setText(f"Speed: {mbps:.2f} MB/s" if mbps > 0 else "Speed: Calculating...")

    def _set_eta(self, speed_bps, total_size=None, total_transferred=None):
        if speed_bps > 0:
            if total_size is None:
                total_size = self.total_bytes
            if total_transferred is None:
                total_transferred = self.bytes_done
            remaining = total_size - total_transferred
            eta_sec = int(remaining / speed_bps) if speed_bps > 0 else 0
            self.label_eta.setText(f"ETA: {self._format_time(eta_sec)}")
        else:
            self.label_eta.setText("ETA: Calculating...")

    def _update_speed_eta(self):
        # Called every second by timer, but smoothing is every 5s
        pass

    def _on_pause_resume(self):
        self.is_paused = not self.is_paused
        self.btn_pause_resume.setText("Resume" if self.is_paused else "Pause")
        self.pause_resume_requested.emit()

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

    @staticmethod
    def _format_bytes(num):
        # Format bytes as human-readable
        for unit in ['B','KB','MB','GB','TB']:
            if num < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} PB"

    @staticmethod
    def _format_time(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h {m}m {s}s"
        elif m:
            return f"{m}m {s}s"
        else:
            return f"{s}s"
