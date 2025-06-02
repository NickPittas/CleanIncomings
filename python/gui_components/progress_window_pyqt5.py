"""
ProgressWindowPyQt5: Standalone progress bar window for CleanIncomings (modular, <300 lines)
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt

class ProgressWindowPyQt5(QDialog):
    """
    A floating, always-on-top progress window with multi-stage support.
    Usage: Instantiate, call show(), update with update_stage_progress(), close on finish.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Progress")
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self.setModal(False)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.header_label = QLabel("\U0001F4C8 Scanning In Progress...")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.header_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.details_label)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)  # Show if needed
        layout.addWidget(self.cancel_btn)

    def show_progress(self, stage:str, percent:int, details:str=None):
        self.header_label.setText(stage)
        self.progress_bar.setValue(percent)
        if details:
            self.details_label.setText(details)
        else:
            self.details_label.setText("")
        self.show()
        self.raise_()
        self.activateWindow()

    def set_cancel_callback(self, callback):
        self.cancel_btn.setVisible(True)
        self.cancel_btn.clicked.connect(callback)

    def close_progress(self):
        self.hide()
        self.progress_bar.setValue(0)
        self.details_label.setText("")

    def error(self, msg:str):
        self.header_label.setText("Error")
        self.details_label.setText(msg)
        self.progress_bar.setValue(0)
        self.show()
        self.raise_()
        self.activateWindow()
