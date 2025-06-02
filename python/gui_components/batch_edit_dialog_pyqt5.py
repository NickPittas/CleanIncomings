"""
Batch Edit Dialog - PyQt5 Version

Provides UI for batch editing of sequence and file properties
including Asset, Task, Resolution, Version, Stage, and destination paths.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QScrollArea, QWidget, QGridLayout, QFrame,
    QSizePolicy, QMessageBox, QFileDialog, QSpacerItem
)
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QDir

class BatchEditDialogPyQt5(QDialog):
    """
    Dialog for batch editing file/sequence properties using PyQt5.

    Workflow:
    - Dialog is always pre-populated with the current values for each selected item.
    - When a field is edited and its checkbox is checked, it will override that variable for all selected items.
    - The destination path preview at the bottom updates in real time as fields are edited.
    - Duplicate dialogs are prevented by checking if one is already open before launching a new one.
    - All debug prints have been replaced with logging (console only).
    """
    applied_batch_changes = pyqtSignal(list)

    def __init__(self, parent: QWidget, items: List[Dict[str, Any]], normalizer: Optional[QObject] = None):
        super().__init__(parent)
        self.items = items
        self.normalizer = normalizer
        self.changes_to_apply: List[Dict[str, Any]] = []

        self.setWindowTitle(f"Batch Edit - {len(self.items)} Items")
        self.setGeometry(200, 200, 850, 700)
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self.field_widgets: Dict[str, Dict[str, QWidget]] = {}
        
        self.fields_meta = [
            ("Shot/Sequence:", "shot_name", False, False, "shot_name"), 
            ("Asset Name:", "asset_name", True, False, "asset_name"),
            ("Task Name:", "task_name", True, False, "task_name"),
            ("Version (e.g., v001):", "version_number", False, False, "version_number"),
            ("Stage:", "stage_name", True, False, "stage_name"),
            ("Resolution:", "resolution_name", True, False, "resolution_name"),
            ("Custom Tag 1:", "custom_tag_1", False, False, "custom_tag_1"),
            ("Custom Tag 2:", "custom_tag_2", False, False, "custom_tag_2"),
            ("Destination Path Override:", "destination_path_override", False, True, "destination_path_override")
        ]

        self._init_ui()
        self._load_initial_values() 

    def _init_ui(self):
    # Ensure all field changes are connected to real-time preview update
    # This is done in _create_scrollable_content_area when widgets are created

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        self._create_header(main_layout)
        self._create_scrollable_content_area(main_layout)
        self._create_preview_area(main_layout) 
        self._create_buttons(main_layout)

        self.setLayout(main_layout)

    def _create_header(self, layout: QVBoxLayout):
        header_label = QLabel(f"Editing {len(self.items)} selected items. Check boxes to apply changes.")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header_label)
        layout.addWidget(self._create_separator())

    def _create_scrollable_content_area(self, main_layout: QVBoxLayout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        content_widget = QWidget()
        self.fields_layout = QGridLayout(content_widget) 
        self.fields_layout.setSpacing(10)
        
        row = 0
        for label_text, internal_name, has_dropdown, has_browse, _ in self.fields_meta:
            self._create_field_row(
                parent_layout=self.fields_layout, 
                row=row, 
                label_text=label_text, 
                internal_name=internal_name,
                has_dropdown=has_dropdown,
                has_browse_button=has_browse
            )
            row += 1
        
        self.fields_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), row, 0, 1, 3)

        content_widget.setLayout(self.fields_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, 1)

    def _create_field_row(self, parent_layout: QGridLayout, row: int, label_text: str, internal_name: str, has_dropdown: bool, has_browse_button: bool = False):
        checkbox = QCheckBox()
        checkbox.setFixedWidth(30)
        
        label = QLabel(label_text)
        
        if has_dropdown:
            entry_widget = QComboBox()
            entry_widget.setEditable(True)
        else:
            entry_widget = QLineEdit()

        entry_widget.setEnabled(False)
        checkbox.stateChanged.connect(lambda state, widget=entry_widget: widget.setEnabled(state == Qt.Checked))
        checkbox.stateChanged.connect(self._update_path_preview)

        parent_layout.addWidget(checkbox, row, 0)
        parent_layout.addWidget(label, row, 1)
        
        if has_browse_button:
            field_hbox = QHBoxLayout()
            field_hbox.addWidget(entry_widget, 1)
            browse_button = QPushButton("...")
            browse_button.setFixedWidth(30)
            browse_button.setEnabled(False)
            browse_button.clicked.connect(lambda _, i_name=internal_name: self._browse_for_path(i_name))
            checkbox.stateChanged.connect(lambda state, btn=browse_button: btn.setEnabled(state == Qt.Checked))
            field_hbox.addWidget(browse_button)
            parent_layout.addLayout(field_hbox, row, 2)
            self.field_widgets[internal_name] = {
                'checkbox': checkbox, 
                'label': label, 
                'entry': entry_widget,
                'browse_button': browse_button
            }
        else:
            parent_layout.addWidget(entry_widget, row, 2)
            self.field_widgets[internal_name] = {
                'checkbox': checkbox, 
                'label': label, 
                'entry': entry_widget
            }
        
        if isinstance(entry_widget, QLineEdit):
            entry_widget.textChanged.connect(self._update_path_preview)
        elif isinstance(entry_widget, QComboBox):
            entry_widget.currentTextChanged.connect(self._update_path_preview)

    def _create_preview_area(self, layout: QVBoxLayout):
        layout.addWidget(self._create_separator())
        preview_label = QLabel("Path Preview (first selected item):")
        layout.addWidget(preview_label)
        
        self.preview_text_edit = QLineEdit()
        self.preview_text_edit.setReadOnly(True)
        self.preview_text_edit.setStyleSheet("background-color: #2D2D2D; color: #CCCCCC;")
        layout.addWidget(self.preview_text_edit)

    def _create_buttons(self, layout: QVBoxLayout):
        layout.addWidget(self._create_separator())
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        reset_button = QPushButton("Reset Fields")
        reset_button.clicked.connect(self._reset_fields)
        button_layout.addWidget(reset_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Changes")
        apply_button.setDefault(True)
        apply_button.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)

    def _create_separator(self) -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def _load_initial_values(self):
        if not self.items:
            for field_label, internal_name, is_dropdown, _, item_key in self.fields_meta:
                widgets_dict = self.field_widgets.get(internal_name)
                if not widgets_dict: continue
                entry_widget = widgets_dict['entry']
                if is_dropdown and isinstance(entry_widget, QComboBox):
                    dropdown_values = self._get_dropdown_values(internal_name)
                    entry_widget.clear()
                    entry_widget.addItems(dropdown_values)
                    if entry_widget.isEditable():
                        entry_widget.lineEdit().setPlaceholderText("<select or type>")
                    elif dropdown_values:
                         entry_widget.setCurrentIndex(0)
            self._update_path_preview()
            return

        first_item_values = {}
        common_values = {}
        multiple_values_fields = set()

        for field_label, internal_name, is_dropdown, _, item_key in self.fields_meta:
            widgets_dict = self.field_widgets.get(internal_name)
            if not widgets_dict: continue
            
            entry_widget = widgets_dict['entry']
            if is_dropdown and isinstance(entry_widget, QComboBox):
                dropdown_values = self._get_dropdown_values(internal_name)
                current_combo_text = entry_widget.lineEdit().text() if entry_widget.isEditable() else entry_widget.currentText()
                entry_widget.clear()
                entry_widget.addItems(dropdown_values)
                if current_combo_text in dropdown_values:
                    entry_widget.setCurrentText(current_combo_text)
                elif entry_widget.isEditable():
                     entry_widget.lineEdit().setText(current_combo_text)
                     if not current_combo_text:
                         entry_widget.lineEdit().setPlaceholderText("<select or type>")
                elif dropdown_values:
                    entry_widget.setCurrentIndex(0)

            first_item_val = self.items[0].get(item_key)
            first_item_values[internal_name] = first_item_val
            if first_item_val is not None:
                common_values[internal_name] = str(first_item_val)
            else:
                common_values[internal_name] = None

        for item in self.items[1:]:
            for field_label, internal_name, _, _, item_key in self.fields_meta:
                if internal_name in multiple_values_fields:
                    continue 
                
                current_item_val = item.get(item_key)
                current_item_val_str = str(current_item_val) if current_item_val is not None else None
                
                if common_values.get(internal_name) != current_item_val_str:
                    common_values.pop(internal_name, None)
                    multiple_values_fields.add(internal_name)

        for field_label, internal_name, is_dropdown, _, item_key in self.fields_meta:
            widgets_dict = self.field_widgets.get(internal_name)
            if not widgets_dict: continue

            checkbox = widgets_dict['checkbox']
            entry_widget = widgets_dict['entry']

            if internal_name in common_values and common_values[internal_name] is not None:
                val_to_set = common_values[internal_name]
                if isinstance(entry_widget, QLineEdit):
                    entry_widget.setText(val_to_set)
                elif isinstance(entry_widget, QComboBox):
                    if val_to_set in [entry_widget.itemText(i) for i in range(entry_widget.count())]:
                        entry_widget.setCurrentText(val_to_set)
                    elif entry_widget.isEditable():
                        entry_widget.lineEdit().setText(val_to_set)
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
                if isinstance(entry_widget, QLineEdit):
                    entry_widget.clear()
                    if internal_name in multiple_values_fields:
                        entry_widget.setPlaceholderText("<multiple values>")
                    else:
                        entry_widget.setPlaceholderText("")
                elif isinstance(entry_widget, QComboBox):
                    if entry_widget.isEditable():
                        entry_widget.lineEdit().clear()
                        if internal_name in multiple_values_fields:
                           entry_widget.lineEdit().setPlaceholderText("<multiple values>")
                        else:
                           entry_widget.lineEdit().setPlaceholderText("<select or type>")
        
        self._update_path_preview()

    def _get_dropdown_values(self, internal_name: str) -> List[str]:
        """
        Always use the real normalizer's get_profile_batch_edit_options for dropdowns.
        Show a warning if options are missing or normalizer is not set.
        """
        if self.normalizer and hasattr(self.normalizer, 'get_profile_batch_edit_options'):
            try:
                options = self.normalizer.get_profile_batch_edit_options()
                return options.get(internal_name, [])
            except Exception as e:
                logging.warning(f"[BatchEditDialogPyQt5] Error fetching dropdown options: {e}")
                QMessageBox.warning(self, "Dropdown Error", f"Could not load options for {internal_name}: {e}")
                return []
        else:
            logging.info(f"[BatchEditDialogPyQt5] No normalizer or get_profile_batch_edit_options for {internal_name}")
            QMessageBox.warning(self, "Dropdown Error", f"No options available for {internal_name}. Normalizer not set or incomplete.")
            return []

    def _browse_for_path(self, internal_name: str):
        if internal_name == "destination_path_override":
            entry_widget = self.field_widgets[internal_name]['entry']
            if isinstance(entry_widget, QLineEdit):
                current_path = entry_widget.text() or QDir.homePath()
                folder_path = QFileDialog.getExistingDirectory(
                    self, 
                    "Select Custom Destination Folder",
                    current_path
                )
                if folder_path:
                    entry_widget.setText(folder_path)

    def _update_path_preview(self, _=None):
        """
        Always use the real normalizer's get_batch_edit_preview_path for preview.
        Show a warning if preview fails.
        """
        if not self.items or not self.normalizer:
            self.preview_text_edit.setText("N/A (No items or normalizer to generate preview)")
            return

        first_item_data = self.items[0]
        preview_changes = {}
        for field_label, internal_name, _, _, item_key in self.fields_meta:
            widgets_dict = self.field_widgets.get(internal_name)
            if not widgets_dict:
                continue
            if widgets_dict['checkbox'].isChecked():
                widget = widgets_dict['entry']
                value = ""
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                preview_changes[item_key] = value
        try:
            # Get the destination root from the parent window if available
            destination_root = None
            parent = self.parent()
            if parent is not None:
                # Try to get destination folder from parent (QMainWindow or dialog)
                if hasattr(parent, 'dest_folder_entry'):
                    destination_root = parent.dest_folder_entry.text()
                elif hasattr(parent, 'selected_destination_folder'):
                    # If using a StringVar-like property
                    destination_root = parent.selected_destination_folder.get()
            if not destination_root:
                destination_root = os.getcwd()  # Fallback to current working directory

            if hasattr(self.normalizer, 'get_batch_edit_preview_path'):
                path_preview = self.normalizer.get_batch_edit_preview_path(first_item_data, preview_changes, destination_root)
                self.preview_text_edit.setText(path_preview)
            else:
                self.preview_text_edit.setText("Preview function not available in normalizer.")
        except Exception as e:
            self.preview_text_edit.setText(f"Error generating preview: {e}")
            logging.warning(f"[BatchEditDialogPyQt5] Preview generation error: {e}")
            QMessageBox.warning(self, "Preview Error", f"Could not generate path preview: {e}")

    def _reset_fields(self):
        for field_label, internal_name, is_dropdown, _, item_key in self.fields_meta:
            widgets_dict = self.field_widgets.get(internal_name)
            if not widgets_dict: continue

            widgets_dict['checkbox'].setChecked(False)
            entry_widget = widgets_dict['entry']
            if isinstance(entry_widget, QLineEdit):
                entry_widget.clear()
            elif isinstance(entry_widget, QComboBox):
                dropdown_values = self._get_dropdown_values(internal_name)
                current_combo_text = ""
                entry_widget.clear()
                entry_widget.addItems(dropdown_values)
                if entry_widget.isEditable():
                    entry_widget.lineEdit().setText(current_combo_text) 
                    entry_widget.lineEdit().setPlaceholderText("<select or type>")
                elif dropdown_values:
                    pass  # No default action needed
        self._load_initial_values()

    def _on_apply(self):
        self.changes_to_apply.clear()
        for field_label, internal_name, _, _, item_key in self.fields_meta:
            widgets_dict = self.field_widgets.get(internal_name)
            if not widgets_dict:
                continue

            if widgets_dict['checkbox'].isChecked():
                widget = widgets_dict['entry']
                value = ""
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                self.changes_to_apply.append({'field': item_key, 'value': value})

        # Log changes and first selected item
        if self.items:
            logging.info(f"[BatchEditDialogPyQt5] Applying changes: {self.changes_to_apply}")
            logging.debug(f"[BatchEditDialogPyQt5] First item data: {self.items[0]}")
        else:
            logging.info(f"[BatchEditDialogPyQt5] Applying changes: {self.changes_to_apply}")
            logging.info("[BatchEditDialogPyQt5] No items to show.")

        if not self.changes_to_apply:
            QMessageBox.information(self, "No Changes", "No fields were selected for batch editing.")
            return

        self.applied_batch_changes.emit(self.changes_to_apply)
        self.accept()

    def get_applied_changes(self) -> List[Dict[str, Any]]:
        return self.changes_to_apply

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

    class DummyNormalizer(QObject):
        def get_profile_batch_edit_options(self):
            return {
                "asset_name": ["TestAsset1", "TestAsset2", "AnotherAsset", "SHARED_ASSET"],
                "task_name": ["modeling", "texturing", "lighting", "comp", "SHARED_TASK"],
                "stage_name": ["wip", "client_review", "final", "archive_candidate"],
                "resolution_name": ["1920x1080", "2048x1152", "source_res"]
            }

        def get_batch_edit_preview_path(self, item_data: Dict[str, Any], changes: Dict[str, Any], destination_root: str = None) -> str:
            path_parts_map = {
                'asset_name': item_data.get('asset_name', 'UNKNOWN_ASSET'),
                'shot_name': item_data.get('shot_name', 'UNKNOWN_SHOT'),
                'task_name': item_data.get('task_name', 'UNKNOWN_TASK'),
            }

            for key, val_in_changes in changes.items():
                if key in path_parts_map:
                    path_parts_map[key] = val_in_changes
            
            ordered_parts = [
                path_parts_map['asset_name'], 
                path_parts_map['shot_name'], 
                path_parts_map['task_name']
            ]
            
            filename = item_data.get('filename', 'file.ext')
            
            new_version_str = changes.get('version_number')
            if new_version_str:
                base, ext = os.path.splitext(filename)
                base = re.sub(r'[_.-]?v\d+', '', base, flags=re.IGNORECASE)
                filename = f"{base}_{new_version_str}{ext}"
            
            if 'destination_path_override' in changes and changes['destination_path_override']:
                return os.path.join(changes['destination_path_override'], filename)

            dest_root = destination_root or "/path/to/destination"
            return os.path.join(dest_root, '/'.join(filter(None, ordered_parts)), filename)

    class TestApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.normalizer_adapter = DummyNormalizer()

            self.button = QPushButton("Open Batch Edit Dialog", self)
            self.button.clicked.connect(self.open_dialog)
            self.setCentralWidget(self.button)
            self.setGeometry(100, 100, 300, 100)

        def open_dialog(self):
            sample_items = [
                {'id': 'item1', 'filename': 'shot010_comp_v001.0101.exr', 'path': '/src/shot010_comp_v001.0101.exr', 
                 'asset_name': 'SHARED_ASSET', 'task_name': 'comp', 'shot_name': 'sh010', 'version_number': 'v001', 
                 'stage_name': 'wip', 'resolution_name': '1920x1080'},
                {'id': 'item2', 'filename': 'shot020_light_v003.0050.dpx', 'path': '/src/shot020_light_v003.0050.dpx', 
                 'asset_name': 'SHARED_ASSET', 'task_name': 'SHARED_TASK', 'shot_name': 'sh020', 'version_number': 'v003',
                 'stage_name': 'review'},
                {'id': 'item3', 'filename': 'assetBuild_charA_model_v010.ma', 'path': '/src/assetBuild_charA_model_v010.ma', 
                 'asset_name': 'charA', 'task_name': 'SHARED_TASK', 'shot_name': 'assetBuild', 'version_number': 'v010',
                 'custom_tag_1': 'LEGACY'}
            ]
            dialog = BatchEditDialogPyQt5(self, sample_items, normalizer=self.normalizer_adapter)
            dialog.applied_batch_changes.connect(self.handle_applied_changes)
            if dialog.exec_() == QDialog.Accepted:
                print("Dialog accepted by user.")
            else:
                print("Dialog cancelled by user.")

        def handle_applied_changes(self, changes: List[Dict[str, Any]]):
            print("Changes to apply:")
            for change in changes:
                print(f"  Field: {change['field']}, Value: {change['value']}")
            QMessageBox.information(self, "Batch Edit Applied", f"{len(changes)} change types will be applied to items.")

    app = QApplication(sys.argv)
    main_window = TestApp()
    main_window.show()
    sys.exit(app.exec_())

