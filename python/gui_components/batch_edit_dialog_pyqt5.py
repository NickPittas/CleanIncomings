"""
Batch Edit Dialog (PyQt5)

Allows batch editing of properties (Asset, Task, Resolution, Version, Stage, Destination Path) for multiple selected items.
Fields are enabled via checkboxes. Dropdowns are populated from the normalizer/config for the current profile. Pre-fills fields if all selected items share a value.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QCheckBox, QLineEdit, QComboBox, QDialogButtonBox, QLabel, QWidget, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from typing import List, Dict, Any, Optional
import os

class BatchEditDialogPyQt5(QDialog):
    """
    Batch Edit Dialog (PyQt5)
    Allows batch editing of properties (Asset, Task, Resolution, Version, Stage, Destination Path) for multiple selected items.
    Fields are enabled via checkboxes. Dropdowns are populated from the normalizer/config for the current profile. Pre-fills fields if all selected items share a value.
    """
    # Signal now emits a dict of {field: value}
    applied_batch_changes = pyqtSignal(dict)

    def __init__(self, parent: QWidget, items: List[Dict[str, Any]], normalizer: Optional[object], profile_name: str):
        super().__init__(parent)
        self.items = items
        self.normalizer = normalizer
        self.profile_name = profile_name
        self.setWindowTitle(f"Batch Edit - {len(self.items)} Items")
        self.setGeometry(200, 200, 850, 700)
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self.field_widgets: Dict[str, Dict[str, QWidget]] = {}
        
        # Debug print to understand item structure
        if self.items and len(self.items) > 0:
            print(f"[BatchEditDialogPyQt5] Sample item structure: {list(self.items[0].keys())}")
            
        # Define editable fields: (label, field_key, is_dropdown, normalizer_method)
        self.fields = [
            ("Asset", "asset", True, "get_available_assets_for_profile"),
            ("Task", "task", True, "get_available_tasks_for_profile"),
            ("Resolution", "resolution", True, "get_available_resolutions_for_profile"),
            ("Version", "version", False, None),
            ("Stage", "stage", True, "get_available_stages_for_profile"),
            ("Destination Path", "destination_path", False, None)
        ]
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Set consistent width for all form elements
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        layout.addLayout(form_layout)
        
        # Add a label showing current destination root
        if self.items and len(self.items) > 0:
            # Try to get the current destination root from any item
            sample_item = self.items[0]
            current_dest = sample_item.get('new_destination_path', '')
            if current_dest:
                dest_root = '/'.join(current_dest.split('/')[:-1])  # Get parent directory
                root_label = QLabel(f"Current destination root: {dest_root}")
                root_label.setStyleSheet("color: #888; font-style: italic;")
                form_layout.addRow(root_label)
                form_layout.addRow(QLabel(""))  # Spacer
        
        # --- Build form rows with: Label, Widget, Checkbox (checkbox on right) ---
        for label, field_key, is_dropdown, normalizer_method in self.fields:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            # Label (field name) - fixed width for alignment
            field_label = QLabel(label + ':')
            field_label.setFixedWidth(120)  # Fixed width for all labels
            row_layout.addWidget(field_label)
            
            # Widget (dropdown or line edit)
            if is_dropdown:
                widget = QComboBox()
                widget.setMinimumWidth(250)  # Minimum width for consistency
                options = self._get_dropdown_options(field_key, normalizer_method)
                if field_key == 'asset' and not options:
                    assets_from_selection = sorted(set(
                        str(item.get('asset', '')) for item in self.items if item.get('asset', '')
                    ))
                    options = assets_from_selection
                widget.addItems(options)
                widget.setEditable(True)
            else:
                widget = QLineEdit()
                widget.setMinimumWidth(250)  # Minimum width for consistency
                
            row_layout.addWidget(widget)
            
            # Checkbox (move to the right)
            checkbox = QCheckBox()
            checkbox.setFixedWidth(20)  # Fixed width for checkboxes
            row_layout.addWidget(checkbox)
            
            row_layout.setStretch(0, 0)  # Label - no stretch
            row_layout.setStretch(1, 1)  # Widget - stretch to fill
            row_layout.setStretch(2, 0)  # Checkbox - no stretch
            
            form_layout.addRow(row_widget)
            self.field_widgets[field_key] = {'checkbox': checkbox, 'widget': widget, 'label': field_label}

        # --- Add live destination path preview below Destination Path row ---
        self.dest_path_preview_label = QLabel("")
        self.dest_path_preview_label.setStyleSheet("color: #6cf; font-style: italic; margin-left: 16px;")
        self.dest_path_preview_label.setWordWrap(True)  # Allow wrapping for long paths
        
        form_layout.addRow(QWidget())  # Spacer row for alignment
        preview_row_widget = QWidget()
        preview_row_layout = QHBoxLayout(preview_row_widget)
        preview_row_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("New Destination Path Preview:")
        preview_label.setFixedWidth(200)
        preview_row_layout.addWidget(preview_label)
        preview_row_layout.addWidget(self.dest_path_preview_label)
        
        form_layout.addRow(preview_row_widget)

        # Connect signals for live preview
        dest_path_widget = self.field_widgets['destination_path']['widget']
        dest_path_widget.textChanged.connect(self._update_dest_path_preview)
        for key in ('asset', 'task', 'resolution', 'version', 'stage'):
            widget = self.field_widgets[key]['widget']
            if hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self._update_dest_path_preview)
            elif hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self._update_dest_path_preview)
                
        # Populate initial values BEFORE updating preview
        self._populate_initial_values()
        
        # Initial preview
        self._update_dest_path_preview()

        # --- Button Box ---
        self.button_box = QDialogButtonBox()
        self.save_btn = self.button_box.addButton("Save", QDialogButtonBox.AcceptRole)
        self.apply_btn = self.button_box.addButton("Apply", QDialogButtonBox.ApplyRole)
        self.close_btn = self.button_box.addButton("Close", QDialogButtonBox.RejectRole)
        self.save_btn.clicked.connect(self._on_save)
        self.apply_btn.clicked.connect(self._on_apply)
        self.close_btn.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

    def _update_dest_path_preview(self):
        """
        Update the destination path preview label in real time as fields are edited.
        Shows a simplified preview of how the path might change.
        """
        try:
            # Gather current values from widgets
            values = {}
            for _, field_key, _, _ in self.fields:
                widget = self.field_widgets[field_key]['widget']
                if hasattr(widget, 'currentText'):
                    values[field_key] = widget.currentText()
                else:
                    values[field_key] = widget.text()
            
            # If user has entered a custom destination path, show that
            user_dest_path = values.get('destination_path', '').strip()
            if user_dest_path:
                preview_text = f"Custom path: {user_dest_path}"
            else:
                # Show a simple preview based on current values and existing item data
                if self.items and len(self.items) > 0:
                    sample_item = self.items[0]
                    
                    # Get the current destination path as a base
                    current_dest = sample_item.get('new_destination_path', '')
                    
                    if current_dest:
                        # Show which fields will change
                        changes = []
                        for field_key, value in values.items():
                            if field_key != 'destination_path' and value and value != '<multiple values>':
                                current_value = sample_item.get('normalized_parts', {}).get(field_key, '')
                                if current_value != value:
                                    changes.append(f"{field_key}: {current_value} → {value}")
                        
                        if changes:
                            preview_text = f"Changes: {', '.join(changes)}\nBase: {os.path.basename(current_dest)}"
                        else:
                            preview_text = f"No changes (base: {os.path.basename(current_dest)})"
                    else:
                        preview_text = "(No current destination path to preview)"
                else:
                    preview_text = "(No items to preview)"
                    
        except Exception as e:
            # If anything goes wrong with preview, don't crash - just show a simple message
            print(f"[BatchEditDialogPyQt5] Error in preview calculation: {e}")
            preview_text = "(Preview temporarily unavailable)"
                
        self.dest_path_preview_label.setText(preview_text)

    def _get_dropdown_options(self, field_key, normalizer_method):
        """
        Fetch dropdown options from the normalizer for the current profile.
        """
        if self.normalizer and normalizer_method and hasattr(self.normalizer, normalizer_method):
            try:
                method = getattr(self.normalizer, normalizer_method)
                options = method(self.profile_name)
                return options if options else []
            except Exception as e:
                import logging
                logging.warning(f"[BatchEditDialogPyQt5] Error fetching dropdown options for {field_key}: {e}")
                return []
        return []

    def closeEvent(self, event):
        """Handle dialog close event properly."""
        if hasattr(self, '_is_closing') and self._is_closing:
            print("[DEBUG] closeEvent: already closing")
            return
            
        self._is_closing = True
        print("[DEBUG] BatchEditDialogPyQt5 closeEvent: dialog is closing")
        
        # Emit finished signal manually to ensure it's called
        # (sometimes Qt doesn't emit it properly)
        if not self.result():
            self.finished.emit(QDialog.Rejected)
        
        super().closeEvent(event)

    def _populate_initial_values(self):
        """
        For each field, if all items share a value, pre-populate it. Otherwise, show <multiple values>.
        All checkboxes start unchecked.
        """
        for _, field_key, is_dropdown, _ in self.fields:
            # First try to get values from normalized_parts
            values = []
            for item in self.items:
                # Check normalized_parts first
                normalized_parts = item.get('normalized_parts', {})
                if field_key in normalized_parts:
                    values.append(normalized_parts.get(field_key))
                # Fall back to direct field
                elif field_key in item:
                    values.append(item.get(field_key))
                else:
                    values.append(None)
                    
            # Remove None values and get unique
            values = [v for v in values if v is not None]
            unique_values = set(values)
            
            widget = self.field_widgets[field_key]['widget']
            
            # Debug print
            if field_key == 'asset' and len(unique_values) > 0:
                print(f"[BatchEditDialogPyQt5] Pre-populating {field_key} with unique values: {unique_values}")
            
            if len(unique_values) == 1:
                val = values[0] if values else ''
                if is_dropdown:
                    idx = widget.findText(str(val))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                    else:
                        widget.setEditText(str(val))
                else:
                    widget.setText(str(val) if val is not None else "")
            else:
                # Multiple values
                if is_dropdown:
                    widget.setEditText("<multiple values>")
                else:
                    widget.setPlaceholderText("<multiple values>")
            self.field_widgets[field_key]['checkbox'].setChecked(False)

    def _collect_changes(self) -> dict:
        """
        Collect checked fields and their values as a dict.
        """
        changes_to_apply = {}
        for _, field_key, _, _ in self.fields:
            checkbox = self.field_widgets[field_key]['checkbox']
            widget = self.field_widgets[field_key]['widget']
            if checkbox.isChecked():
                if hasattr(widget, 'currentText'):
                    val = widget.currentText()
                else:
                    val = widget.text()
                changes_to_apply[field_key] = val
        return changes_to_apply

    def _on_save(self):
        """Handle save button click."""
        if hasattr(self, '_is_closing') and self._is_closing:
            print("[DEBUG] _on_save called but dialog is closing")
            return
            
        print("[DEBUG] BatchEditDialogPyQt5 _on_save: collecting and emitting changes")
        changes = self._collect_changes()
        
        if not changes:
            QMessageBox.warning(self, "No Changes", "No fields were checked to apply changes.")
            return
        
        print(f"[DEBUG] Emitting changes: {changes}")
        
        # Emit changes first
        self.applied_batch_changes.emit(changes)
        
        # Then close with accepted result
        self._is_closing = True
        self.accept()

    def _on_apply(self):
        """Apply changes but keep dialog open."""
        if hasattr(self, '_is_closing') and self._is_closing:
            print("[DEBUG] _on_apply called but dialog is closing")
            return
            
        print("[DEBUG] BatchEditDialogPyQt5 _on_apply: applying changes")
        changes = self._collect_changes()
        
        if not changes:
            QMessageBox.warning(self, "No Changes", "No fields were checked to apply changes.")
            return
        
        print(f"[DEBUG] Emitting changes (apply): {changes}")
        self.applied_batch_changes.emit(changes)
        # Don't close the dialog for Apply

    def reject(self):
        """Handle reject (Cancel/Close) properly."""
        print("[DEBUG] BatchEditDialogPyQt5 reject called")
        self._is_closing = True
        super().reject()

    def accept(self):
        """Handle accept (Save) properly."""
        print("[DEBUG] BatchEditDialogPyQt5 accept called")
        self._is_closing = True
        super().accept()