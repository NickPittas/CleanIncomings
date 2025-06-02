"""
PyQt5 Settings Window - Comprehensive settings dialog with JSON editors
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QPushButton, QFrame, QSpinBox, QCheckBox, QLineEdit,
    QFileDialog, QMessageBox, QTextEdit, QSplitter, QGroupBox,
    QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os
import json
from typing import Dict, Any, Optional


class SettingsWindow(QDialog):
    """Main settings window with multiple tabs for different configurations."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent, config_dir: str, settings_manager):
        super().__init__(parent)
        self.parent_app = parent
        self.config_dir = config_dir
        self.settings_manager = settings_manager
        
        self.setWindowTitle("CleanIncomings Settings")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Center on parent
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 1000) // 2
            y = parent_geo.y() + (parent_geo.height() - 700) // 2
            self.move(x, y)
        
        self.create_ui()
        
    def create_ui(self):
        """Create the settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_general_settings_tab()
        self._create_appearance_settings_tab()
        self._create_normalization_rules_tab()
        self._create_profile_management_tab()
        self._create_advanced_settings_tab()

        # Add Save/Cancel buttons
        self._create_action_buttons(layout)

        self.load_settings()

    def _create_general_settings_tab(self):
        """Creates the General Settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Example: Default Source Folder
        self.default_source_edit = QLineEdit()
        self.default_source_edit.setPlaceholderText("e.g., C:/Users/YourUser/Downloads")
        browse_source_btn = QPushButton("Browse...")
        browse_source_btn.clicked.connect(lambda: self._browse_folder(self.default_source_edit))
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.default_source_edit)
        source_layout.addWidget(browse_source_btn)
        layout.addRow(QLabel("Default Source Folder:"), source_layout)

        # Example: Default Destination Folder
        self.default_dest_edit = QLineEdit()
        self.default_dest_edit.setPlaceholderText("e.g., D:/Projects/Cleaned")
        browse_dest_btn = QPushButton("Browse...")
        browse_dest_btn.clicked.connect(lambda: self._browse_folder(self.default_dest_edit))
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(self.default_dest_edit)
        dest_layout.addWidget(browse_dest_btn)
        layout.addRow(QLabel("Default Destination Folder:"), dest_layout)

        # Example: Scan on Startup
        self.scan_on_startup_check = QCheckBox("Automatically scan source folder on application startup")
        layout.addRow(self.scan_on_startup_check)
        
        # Scan Threads
        self.scan_threads_spin = QSpinBox()
        self.scan_threads_spin.setMinimum(1)
        self.scan_threads_spin.setMaximum(32)
        self.scan_threads_spin.setValue(8)
        self.scan_threads_spin.setToolTip("Number of threads used for scanning directories and finding files/sequences.")
        layout.addRow(QLabel("Scan Threads:"), self.scan_threads_spin)

        # Copy Threads
        self.copy_threads_spin = QSpinBox()
        self.copy_threads_spin.setMinimum(1)
        self.copy_threads_spin.setMaximum(32)
        self.copy_threads_spin.setValue(16)
        self.copy_threads_spin.setToolTip("Number of threads used for copying individual files in parallel.")
        layout.addRow(QLabel("Copy Threads:"), self.copy_threads_spin)

        self.tab_widget.addTab(tab, "General")

    def _browse_folder(self, line_edit_widget):
        """Opens a folder dialog and sets the path to the line edit."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            line_edit_widget.setText(folder_path)

    def _create_appearance_settings_tab(self):
        """Creates the Appearance Settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Example: Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Nuke Dark", "Light", "System Default"]) # Placeholder
        layout.addRow(QLabel("UI Theme:"), self.theme_combo)

        # Example: Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(20)
        layout.addRow(QLabel("Interface Font Size:"), self.font_size_spin)
        
        # Example: Corner Radius
        self.corner_radius_spin = QSpinBox()
        self.corner_radius_spin.setMinimum(0)
        self.corner_radius_spin.setMaximum(15)
        layout.addRow(QLabel("Widget Corner Radius:"), self.corner_radius_spin)

        self.tab_widget.addTab(tab, "Appearance")

    def _create_normalization_rules_tab(self):
        """Creates the Normalization Rules tab with a JSON editor."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Splitter for patterns.json and profiles.json
        splitter = QSplitter(Qt.Horizontal)
        
        # Patterns.json editor
        patterns_group = QGroupBox("Shot/Task Patterns (patterns.json)")
        patterns_layout = QVBoxLayout(patterns_group)
        self.patterns_editor = QTextEdit()
        self.patterns_editor.setPlaceholderText("Enter JSON content for shot/task normalization patterns...")
        self.patterns_editor.setFont(QFont("Courier New", 10))
        patterns_layout.addWidget(self.patterns_editor)
        # Add Edit Patterns button
        edit_patterns_btn = QPushButton("Edit Patterns (Dialog)")
        edit_patterns_btn.clicked.connect(self._open_patterns_editor_dialog)
        patterns_layout.addWidget(edit_patterns_btn)
        # Add Graphical Edit Patterns button
        graphical_patterns_btn = QPushButton("Graphical Edit Patterns")
        graphical_patterns_btn.clicked.connect(self._open_graphical_patterns_editor)
        patterns_layout.addWidget(graphical_patterns_btn)
        splitter.addWidget(patterns_group)
        
        # Profiles.json editor
        profiles_group = QGroupBox("Naming Profiles (profiles.json)")
        profiles_layout = QVBoxLayout(profiles_group)
        self.profiles_editor = QTextEdit()
        self.profiles_editor.setPlaceholderText("Enter JSON content for naming profiles...")
        self.profiles_editor.setFont(QFont("Courier New", 10))
        profiles_layout.addWidget(self.profiles_editor)
        # Add Edit Profiles button
        edit_profiles_btn = QPushButton("Edit Profiles (Dialog)")
        edit_profiles_btn.clicked.connect(self._open_profiles_editor_dialog)
        profiles_layout.addWidget(edit_profiles_btn)
        # Add Graphical Edit Profiles button
        graphical_profiles_btn = QPushButton("Graphical Edit Profiles")
        graphical_profiles_btn.clicked.connect(self._open_graphical_profiles_editor)
        profiles_layout.addWidget(graphical_profiles_btn)
        splitter.addWidget(profiles_group)
        
        splitter.setSizes([self.width() // 2, self.width() // 2]) # Initial equal split
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(tab, "Normalization Rules")

    def _open_patterns_editor_dialog(self):
        from python.gui_components.json_pattern_editor_pyqt5 import JsonEditorDialog
        patterns_path = os.path.join(self.config_dir, "patterns.json")
        dlg = JsonEditorDialog(self, file_path=patterns_path, title="Edit Patterns (patterns.json)")
        if dlg.exec_():
            # Reload content after save
            try:
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    self.patterns_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error Reloading Patterns", f"Could not reload patterns.json: {e}")

    def _open_profiles_editor_dialog(self):
        from python.gui_components.json_pattern_editor_pyqt5 import JsonEditorDialog
        profiles_path = os.path.join(self.config_dir, "profiles.json")
        dlg = JsonEditorDialog(self, file_path=profiles_path, title="Edit Profiles (profiles.json)")
        if dlg.exec_():
            # Reload content after save
            try:
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    self.profiles_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error Reloading Profiles", f"Could not reload profiles.json: {e}")

    def _open_graphical_patterns_editor(self):
        from python.gui_components.graphical_json_editor_pyqt5 import GraphicalJsonEditorDialog
        patterns_path = os.path.join(self.config_dir, "patterns.json")
        dlg = GraphicalJsonEditorDialog(self, file_path=patterns_path, title="Graphical Edit Patterns (patterns.json)")
        if dlg.exec_():
            try:
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    self.patterns_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error Reloading Patterns", f"Could not reload patterns.json: {e}")

    def _open_graphical_profiles_editor(self):
        from python.gui_components.graphical_json_editor_pyqt5 import GraphicalJsonEditorDialog
        profiles_path = os.path.join(self.config_dir, "profiles.json")
        dlg = GraphicalJsonEditorDialog(self, file_path=profiles_path, title="Graphical Edit Profiles (profiles.json)")
        if dlg.exec_():
            try:
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    self.profiles_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error Reloading Profiles", f"Could not reload profiles.json: {e}")

    def _create_profile_management_tab(self):
        """Creates the Profile Management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.addWidget(QLabel("Profile management UI will go here (e.g., list, add, edit, delete profiles)."))
        self.tab_widget.addTab(tab, "Profile Management")

    def _create_advanced_settings_tab(self):
        """Creates the Advanced Settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Example: Enable Debug Logging
        self.debug_logging_check = QCheckBox("Enable detailed debug logging")
        layout.addRow(self.debug_logging_check)
        
        # Example: Temp Folder Path
        self.temp_folder_edit = QLineEdit()
        self.temp_folder_edit.setPlaceholderText("Default: system temp")
        browse_temp_btn = QPushButton("Browse...")
        browse_temp_btn.clicked.connect(lambda: self._browse_folder(self.temp_folder_edit))
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_folder_edit)
        temp_layout.addWidget(browse_temp_btn)
        layout.addRow(QLabel("Temporary Files Path:"), temp_layout)

        # Batch Copy Threads (Robocopy /MT)
        self.batch_copy_threads_spin = QSpinBox()
        self.batch_copy_threads_spin.setMinimum(1)
        self.batch_copy_threads_spin.setMaximum(128)
        self.batch_copy_threads_spin.setValue(32)
        self.batch_copy_threads_spin.setToolTip("Number of threads Robocopy uses for parallel file copy within a batch operation. Too high may overload your system.")
        layout.addRow(QLabel("Batch Copy Threads (Robocopy /MT):"), self.batch_copy_threads_spin)

        # Progress Update Interval
        from PyQt5.QtWidgets import QDoubleSpinBox
        self.progress_update_interval_spin = QDoubleSpinBox()
        self.progress_update_interval_spin.setMinimum(0.05)
        self.progress_update_interval_spin.setMaximum(2.0)
        self.progress_update_interval_spin.setSingleStep(0.05)
        self.progress_update_interval_spin.setDecimals(2)
        self.progress_update_interval_spin.setValue(0.5)
        self.progress_update_interval_spin.setToolTip("How often the progress bar updates during batch copy/move operations.")
        layout.addRow(QLabel("Progress Update Interval (seconds):"), self.progress_update_interval_spin)

        self.tab_widget.addTab(tab, "Advanced")

    def _create_action_buttons(self, main_layout):
        """Creates Save, Apply, and Cancel buttons."""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        
        self.save_button = QPushButton("Save & Close")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject) # QDialog's reject

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addWidget(button_frame)

    def load_settings(self):
        """Load settings from the settings manager and populate the UI."""
        # General Settings
        self.default_source_edit.setText(self.settings_manager.get_setting("ui_state", "default_source_folder", "")) # Corrected section
        self.default_dest_edit.setText(self.settings_manager.get_setting("ui_state", "default_destination_folder", "")) # Corrected section
        self.scan_on_startup_check.setChecked(self.settings_manager.get_setting("ui_state", "scan_on_startup", False)) # Corrected section
        self.scan_threads_spin.setValue(self.settings_manager.get_setting("ui_state", "scan_threads", 8))
        self.copy_threads_spin.setValue(self.settings_manager.get_setting("ui_state", "copy_threads", 16))

        # Appearance Settings
        current_theme = self.settings_manager.get_setting("ui_state", "theme", "Nuke Dark") # Corrected section
        idx = self.theme_combo.findText(current_theme)
        if idx != -1:
            self.theme_combo.setCurrentIndex(idx)
        
        self.font_size_spin.setValue(self.settings_manager.get_setting("ui_state", "font_size", 10)) # Corrected section
        self.corner_radius_spin.setValue(self.settings_manager.get_setting("ui_state", "corner_radius", self.parent_app.current_corner_radius if hasattr(self.parent_app, 'current_corner_radius') else 4)) # Corrected section

        # Normalization Rules
        try:
            patterns_path = os.path.join(self.config_dir, "patterns.json")
            if os.path.exists(patterns_path):
                with open(patterns_path, 'r') as f:
                    self.patterns_editor.setText(f.read())
            
            profiles_path = os.path.join(self.config_dir, "profiles.json")
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r') as f:
                    self.profiles_editor.setText(f.read())
        except Exception as e:
            QMessageBox.warning(self, "Error Loading Rules", f"Could not load normalization rules: {e}")

        # Advanced Settings
        self.debug_logging_check.setChecked(self.settings_manager.get_setting("ui_state", "debug_logging_enabled", False)) # Corrected section
        self.temp_folder_edit.setText(self.settings_manager.get_setting("ui_state", "temporary_files_path", "")) # Corrected section
        self.batch_copy_threads_spin.setValue(self.settings_manager.get_setting("performance", "batch_copy_threads", 32))
        self.progress_update_interval_spin.setValue(self.settings_manager.get_setting("performance", "progress_update_interval", 0.5))

    def apply_settings(self):
        """Apply current settings without closing the dialog."""
        self._save_current_settings()
        self.settings_changed.emit()
        QMessageBox.information(self, "Settings Applied", "Settings have been applied.")

    def save_settings(self):
        """Save current settings and close the dialog."""
        self._save_current_settings()
        self.settings_changed.emit()
        self.accept() # QDialog's accept

    def _save_current_settings(self):
        """Internal method to save all settings from UI to manager and files."""
        # General Settings
        self.settings_manager.update_setting("ui_state", "default_source_folder", self.default_source_edit.text()) # Corrected section
        self.settings_manager.update_setting("ui_state", "default_destination_folder", self.default_dest_edit.text()) # Corrected section
        self.settings_manager.update_setting("ui_state", "scan_on_startup", self.scan_on_startup_check.isChecked()) # Corrected section
        self.settings_manager.update_setting("ui_state", "scan_threads", self.scan_threads_spin.value())
        self.settings_manager.update_setting("ui_state", "copy_threads", self.copy_threads_spin.value())

        # Appearance Settings
        self.settings_manager.update_setting("ui_state", "theme", self.theme_combo.currentText()) # Corrected section
        self.settings_manager.update_setting("ui_state", "font_size", self.font_size_spin.value()) # Corrected section
        self.settings_manager.update_setting("ui_state", "corner_radius", self.corner_radius_spin.value()) # Corrected section

        # Normalization Rules
        try:
            patterns_path = os.path.join(self.config_dir, "patterns.json")
            with open(patterns_path, 'w') as f:
                f.write(self.patterns_editor.toPlainText())
            
            profiles_path = os.path.join(self.config_dir, "profiles.json")
            with open(profiles_path, 'w') as f:
                f.write(self.profiles_editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Rules", f"Could not save normalization rules: {e}")

        # Advanced Settings
        self.settings_manager.update_setting("ui_state", "debug_logging_enabled", self.debug_logging_check.isChecked()) # Corrected section
        self.settings_manager.update_setting("ui_state", "temporary_files_path", self.temp_folder_edit.text()) # Corrected section
        self.settings_manager.update_setting("performance", "batch_copy_threads", self.batch_copy_threads_spin.value())
        self.settings_manager.update_setting("performance", "progress_update_interval", self.progress_update_interval_spin.value())

# Example usage (for testing, typically instantiated by the main app)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # Mock SettingsManager for standalone testing
    class MockSettingsManager:
        def __init__(self, config_file_path="test_settings.json"):
            self.config_file_path = config_file_path
            self.settings = {}
            self._load_settings_from_file()

        def _load_settings_from_file(self):
            if os.path.exists(self.config_file_path):
                try:
                    with open(self.config_file_path, 'r') as f:
                        self.settings = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {self.config_file_path}. Using default settings.")
                    self.settings = {} # Fallback to empty if file is corrupt
            else: # If no file, initialize with some defaults
                self.settings = {
                    "default_source_folder": "C:/Test/Source",
                    "default_destination_folder": "C:/Test/Destination",
                    "scan_on_startup": True,
                    "max_concurrent_operations": 2,
                    "theme": "Nuke Dark",
                    "font_size": 11,
                    "corner_radius": 3,
                    "debug_logging_enabled": False,
                    "temporary_files_path": ""
                }
                self.save_all_settings() # Create the file with defaults

        def get_setting(self, section: str, key: str, default: Any = None) -> Any:
            return self.settings.get(key, default)

        def update_setting(self, section: str, key: str, value: Any):
            self.settings[key] = value

        def save_all_settings(self):
            try:
                with open(self.config_file_path, 'w') as f:
                    json.dump(self.settings, f, indent=4)
                print(f"Settings saved to {self.config_file_path}")
            except Exception as e:
                print(f"Error saving settings to {self.config_file_path}: {e}")
        
        def get_available_themes(self): # Mock method
            return ["Nuke Dark", "Light", "System Default"]


    app = QApplication(sys.argv)
    
    # Create a dummy config directory for testing
    test_config_dir = os.path.join(os.getcwd(), "test_config")
    os.makedirs(test_config_dir, exist_ok=True)
    
    # Create dummy patterns.json and profiles.json for testing
    dummy_patterns_content = {"version": 1, "patterns": []}
    dummy_profiles_content = {"version": 1, "profiles": []}
    
    with open(os.path.join(test_config_dir, "patterns.json"), 'w') as f:
        json.dump(dummy_patterns_content, f, indent=4)
    with open(os.path.join(test_config_dir, "profiles.json"), 'w') as f:
        json.dump(dummy_profiles_content, f, indent=4)

    mock_settings_manager = MockSettingsManager(os.path.join(test_config_dir, "app_settings.json"))
    
    # Mock parent app for corner radius
    class MockApp:
        def __init__(self):
            self.current_corner_radius = 5 # Example value
            
    mock_parent_app = MockApp()

    dialog = SettingsWindow(parent=mock_parent_app, config_dir=test_config_dir, settings_manager=mock_settings_manager)
    dialog.show()
    sys.exit(app.exec_())
