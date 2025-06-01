from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout

class JsonPatternEditor(QDialog):
    def __init__(self, parent=None, current_patterns=None):
        super().__init__(parent)
        self.setWindowTitle("JSON Pattern Editor")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        if current_patterns:
            self.text_edit.setText(current_patterns)
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def get_patterns(self):
        return self.text_edit.toPlainText()
