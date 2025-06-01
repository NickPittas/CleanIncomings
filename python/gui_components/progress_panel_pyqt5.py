from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel

class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()
        self.details_label = QLabel("Details:")

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_label)

    def update_progress(self, value, status_text="", details_text=""):
        self.progress_bar.setValue(value)
        if status_text:
            self.status_label.setText(status_text)
        if details_text:
            self.details_label.setText(details_text)
