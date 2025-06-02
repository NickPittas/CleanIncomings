from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, QPushButton, QSizePolicy, QFrame
from PyQt5.QtCore import Qt

class ProgressPanel(QWidget):
    """
    Multi-stage progress panel for PyQt5, matching the Tkinter version.
    Supports: Initialization, File Collection, Sequence Detection, Path Mapping, Final Processing.
    Each stage has an icon, label, progress bar (if applicable), and details.
    """
    STAGES = [
        {
            'id': 'initialization',
            'title': '1. Initialization',
            'icon_pending': '\u23f3',
            'icon_progress': '\U0001F504',
            'icon_completed': '\u2705',
            'icon_error': '\u274c',
            'has_progress': False
        },
        {
            'id': 'collection',
            'title': '2. File Collection',
            'icon_pending': '\u23f3',
            'icon_progress': '\U0001F4C1',
            'icon_completed': '\u2705',
            'icon_error': '\u274c',
            'has_progress': False
        },
        {
            'id': 'sequencing',
            'title': '3. Sequence Detection',
            'icon_pending': '\u23f3',
            'icon_progress': '\U0001F50D',
            'icon_completed': '\u2705',
            'icon_error': '\u274c',
            'has_progress': True
        },
        {
            'id': 'mapping',
            'title': '4. Path Mapping',
            'icon_pending': '\u23f3',
            'icon_progress': '\U0001F5FA',
            'icon_completed': '\u2705',
            'icon_error': '\u274c',
            'has_progress': True
        },
        {
            'id': 'processing',
            'title': '5. Final Processing',
            'icon_pending': '\u23f3',
            'icon_progress': '\u2699',
            'icon_completed': '\u2705',
            'icon_error': '\u274c',
            'has_progress': False
        }
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setWindowTitle("Progress")
        self.stage_widgets = {}
        self.stage_status = {stage['id']: 'pending' for stage in self.STAGES}
        self.current_stage = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        # Header
        self.header_label = QLabel("\U0001F4C8 Progress")
        self.header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        # Set header height to 25% of the minimum panel height
        header_height = int(self.minimumHeight() * 0.25)
        self.header_label.setFixedHeight(header_height)
        layout.addWidget(self.header_label, stretch=0)
        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.overall_progress)
        # Per-stage widgets
        for stage in self.STAGES:
            row = QHBoxLayout()
            icon = QLabel(stage['icon_pending'])
            icon.setFixedWidth(30)
            icon.setAlignment(Qt.AlignCenter)
            label = QLabel(stage['title'])
            label.setMinimumWidth(160)
            label.setStyleSheet("font-size: 14px;")
            row.addWidget(icon)
            row.addWidget(label)
            # Optional progress bar
            if stage['has_progress']:
                pbar = QProgressBar()
                pbar.setMinimum(0)
                pbar.setMaximum(100)
                pbar.setValue(0)
                pbar.setTextVisible(False)
                pbar.setFixedWidth(120)
                row.addWidget(pbar)
            else:
                pbar = None
            # Details label
            details = QLabel("")
            details.setStyleSheet("color: gray; font-size: 12px;")
            row.addWidget(details)
            row.addStretch(1)
            frame = QFrame()
            frame.setLayout(row)
            layout.addWidget(frame)
            self.stage_widgets[stage['id']] = {
                'icon': icon,
                'label': label,
                'progress': pbar,
                'details': details
            }
        layout.addStretch(1)

    def reset(self):
        """Reset all stages to pending and clear progress."""
        self.overall_progress.setValue(0)
        for stage in self.STAGES:
            w = self.stage_widgets[stage['id']]
            w['icon'].setText(stage['icon_pending'])
            w['label'].setStyleSheet("font-size: 14px;")
            if w['progress']:
                w['progress'].setValue(0)
            w['details'].setText("")
            self.stage_status[stage['id']] = 'pending'
        self.current_stage = None

    def start_stage(self, stage_id, details=""):
        """Mark a stage as in progress."""
        stage = next((s for s in self.STAGES if s['id'] == stage_id), None)
        if not stage:
            return
        w = self.stage_widgets[stage_id]
        w['icon'].setText(stage['icon_progress'])
        w['label'].setStyleSheet("font-size: 14px; font-weight: bold; color: #0078d7;")
        w['details'].setText(details)
        self.stage_status[stage_id] = 'in_progress'
        self.current_stage = stage_id

    def update_stage_progress(self, stage_id, value, details=""):
        """Update the progress bar for a stage (0-100)."""
        w = self.stage_widgets.get(stage_id)
        if w and w['progress']:
            w['progress'].setValue(int(value))
        if details:
            w['details'].setText(details)

    def complete_stage(self, stage_id, details=""):
        """Mark a stage as completed."""
        stage = next((s for s in self.STAGES if s['id'] == stage_id), None)
        if not stage:
            return
        w = self.stage_widgets[stage_id]
        w['icon'].setText(stage['icon_completed'])
        w['label'].setStyleSheet("font-size: 14px; color: green;")
        w['details'].setText(details)
        self.stage_status[stage_id] = 'completed'

    def error_stage(self, stage_id, error_message=""):
        """Mark a stage as errored."""
        stage = next((s for s in self.STAGES if s['id'] == stage_id), None)
        if not stage:
            return
        w = self.stage_widgets[stage_id]
        w['icon'].setText(stage['icon_error'])
        w['label'].setStyleSheet("font-size: 14px; color: red;")
        w['details'].setText(error_message)
        self.stage_status[stage_id] = 'error'

    def set_overall_progress(self, value):
        self.overall_progress.setValue(int(value))

    def show_panel(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_panel(self):
        self.hide()
