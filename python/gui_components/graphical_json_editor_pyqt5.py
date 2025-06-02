import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QLineEdit, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt

class GraphicalJsonEditorDialog(QDialog):
    """
    Beautiful graphical JSON editor for editing patterns.json or profiles.json.
    Allows adding, editing, and removing items and subitems in a tree structure.
    Supports loading from and saving to file, with validation and error feedback.
    """
    def __init__(self, parent=None, file_path=None, title=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(title or "Graphical JSON Editor")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree)
        # Buttons
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Root Item")
        self.add_btn.clicked.connect(self.add_root_item)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_json)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.add_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)
        # Load file
        if self.file_path:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.populate_tree(data)
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Could not load file:\n{e}")
        self.tree.itemDoubleClicked.connect(self.edit_item)
    def populate_tree(self, data, parent=None):
        if parent is None:
            self.tree.clear()
        if isinstance(data, dict):
            for k, v in data.items():
                item = QTreeWidgetItem([str(k), self.value_to_str(v)])
                if parent:
                    parent.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)
                self.populate_tree(v, item)
        elif isinstance(data, list):
            for i, v in enumerate(data):
                item = QTreeWidgetItem([str(i), self.value_to_str(v)])
                if parent:
                    parent.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)
                self.populate_tree(v, item)
    def value_to_str(self, v):
        if isinstance(v, (dict, list)):
            return "[object]"
        return str(v)
    def tree_to_data(self, parent=None):
        if parent is None:
            items = [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        else:
            items = [parent.child(i) for i in range(parent.childCount())]
        # Detect if dict or list
        is_list = all(self.is_int(item.text(0)) for item in items)
        if is_list:
            arr = []
            for item in items:
                if item.childCount() > 0:
                    arr.append(self.tree_to_data(item))
                else:
                    arr.append(self.parse_value(item.text(1)))
            return arr
        else:
            obj = {}
            for item in items:
                key = item.text(0)
                if item.childCount() > 0:
                    obj[key] = self.tree_to_data(item)
                else:
                    obj[key] = self.parse_value(item.text(1))
            return obj
    def is_int(self, s):
        try:
            int(s)
            return True
        except Exception:
            return False
    def parse_value(self, s):
        # Try to parse as int, float, bool, or keep as string
        if s.lower() == 'true':
            return True
        if s.lower() == 'false':
            return False
        try:
            if '.' in s:
                return float(s)
            return int(s)
        except Exception:
            return s
    def add_root_item(self):
        item = QTreeWidgetItem(["key", "value"])
        self.tree.addTopLevelItem(item)
        self.tree.editItem(item, 0)
    def open_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        if item:
            menu.addAction("Add Child", lambda: self.add_child_item(item))
            menu.addAction("Edit", lambda: self.edit_item(item, 0))
            menu.addAction("Delete", lambda: self.delete_item(item))
        menu.exec_(self.tree.viewport().mapToGlobal(pos))
    def add_child_item(self, parent):
        item = QTreeWidgetItem(["key", "value"])
        parent.addChild(item)
        parent.setExpanded(True)
        self.tree.editItem(item, 0)
    def edit_item(self, item, column):
        self.tree.editItem(item, column)
    def delete_item(self, item):
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            idx = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(idx)
    def save_json(self):
        try:
            data = self.tree_to_data()
            pretty = json.dumps(data, indent=4, ensure_ascii=False)
            if self.file_path:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(pretty)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not save: {e}")
