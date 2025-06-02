import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class JsonEditorDialog(QDialog):
    """
    Generic JSON editor dialog for editing and validating JSON files (patterns, profiles, etc).
    """
    def __init__(self, parent=None, file_path=None, title=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(title or "JSON Editor")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        self.info_label = QLabel(f"Editing: {file_path if file_path else ''}")
        self.info_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.info_label)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 11))
        layout.addWidget(self.text_edit)

        # Load file content if path is given
        if self.file_path:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pretty = json.dumps(data, indent=4, ensure_ascii=False)
                self.text_edit.setText(pretty)
            except Exception as e:
                self.text_edit.setText("")
                QMessageBox.warning(self, "Load Error", f"Could not load file:\n{e}")

        # Buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_json)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch(1)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def save_json(self):
        text = self.text_edit.toPlainText()
        try:
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=4, ensure_ascii=False)
            if self.file_path:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(pretty)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not save: Invalid JSON.\n{e}")
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
