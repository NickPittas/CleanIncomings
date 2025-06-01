"""
PyQt5 Profiles Editor Window - Advanced visual editor for profiles.json
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QPushButton, QFrame, QTextEdit, QListWidget, QListWidgetItem,
    QLineEdit, QGroupBox, QFormLayout, QSplitter, QMessageBox,
    QScrollArea, QCheckBox, QComboBox, QTreeWidget, QTreeWidgetItem,
    QInputDialog, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os
import json
from typing import Dict, List, Any, Optional, Callable


class ProfilesEditorWindow(QDialog):
    """Visual editor for profiles.json with full profile management."""
    
    profiles_changed = pyqtSignal()
    
    def __init__(self, parent, config_dir: str, on_save_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.on_save_callback = on_save_callback
        self.profiles_data = {}
        self.current_profile = None
        
        self.setWindowTitle("Profiles Configuration Editor")
        self.setModal(False)  # Allow interaction with parent
        self.resize(1400, 900)
        
        # Center on parent
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 1400) // 2
            y = parent_geo.y() + (parent_geo.height() - 900) // 2
            self.move(x, y)
        
        self.load_profiles()
        self.create_ui()
        
    def load_profiles(self):
        """Load profiles from profiles.json."""
        profiles_file = os.path.join(self.config_dir, "profiles.json")
        default_profiles = {
            "Default Profile": [
                {
                    "folderRule": "VFX/Shots/{shot}/",
                    "patterns": ["shotPatterns"],
                    "priority": 1
                }
            ]
        }
        
        try:
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.profiles_data = json.load(f)
            else:
                self.profiles_data = default_profiles
                
            # Ensure we have at least one profile
            if not self.profiles_data:
                self.profiles_data = default_profiles
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load profiles.json:\n{e}\n\nUsing default profiles."
            )
            self.profiles_data = default_profiles
    
    def create_ui(self):
        """Create the profiles editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Profiles Configuration Editor")
        title_label.setFont(QFont("", 18, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Header buttons
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self.save_profiles)
        header_layout.addWidget(save_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Main content - horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left side - Profile list
        self.create_profile_list(main_splitter)
        
        # Right side - Profile details
        self.create_profile_details(main_splitter)
        
        # Set initial splitter sizes
        main_splitter.setSizes([350, 1050])
        
    def create_profile_list(self, parent):
        """Create the profile list section."""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Profile list header
        header_layout = QHBoxLayout()
        profiles_label = QLabel("Project Profiles")
        profiles_label.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(profiles_label)
        header_layout.addStretch()
        
        left_layout.addLayout(header_layout)
        
        # Profile list
        self.profiles_list = QListWidget()
        self.profiles_list.itemSelectionChanged.connect(self.on_profile_selected)
        left_layout.addWidget(self.profiles_list)
        
        # Profile management buttons
        profile_btn_layout = QVBoxLayout()
        
        add_profile_btn = QPushButton("➕ Add Profile")
        add_profile_btn.clicked.connect(self.add_profile)
        profile_btn_layout.addWidget(add_profile_btn)
        
        duplicate_profile_btn = QPushButton("📄 Duplicate Profile")
        duplicate_profile_btn.clicked.connect(self.duplicate_profile)
        profile_btn_layout.addWidget(duplicate_profile_btn)
        
        rename_profile_btn = QPushButton("✏️ Rename Profile")
        rename_profile_btn.clicked.connect(self.rename_profile)
        profile_btn_layout.addWidget(rename_profile_btn)
        
        delete_profile_btn = QPushButton("🗑️ Delete Profile")
        delete_profile_btn.setStyleSheet("QPushButton { background-color: #8B0000; }")
        delete_profile_btn.clicked.connect(self.delete_profile)
        profile_btn_layout.addWidget(delete_profile_btn)
        
        left_layout.addLayout(profile_btn_layout)
        
        # Populate profiles
        self.populate_profiles_list()
        
        parent.addWidget(left_widget)
        
    def create_profile_details(self, parent):
        """Create the profile details section."""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # Profile details header
        self.profile_details_label = QLabel("Select a profile to edit")
        self.profile_details_label.setFont(QFont("", 14, QFont.Bold))
        right_layout.addWidget(self.profile_details_label)
        
        # Description
        desc_text = """Profile Configuration Help:

• Each profile contains multiple folder rules that define how files are organized
• Folder rules specify destination paths using template variables like {shot}, {task}, {asset}
• Patterns determine which types of content trigger each rule
• Rules are processed in priority order (lower numbers = higher priority)

Available template variables:
{shot} - Shot identifier from shot patterns
{task} - Task name from task patterns  
{asset} - Asset type from asset patterns
{version} - Version number from version patterns
{resolution} - Resolution from resolution patterns
{stage} - Production stage from stage patterns
{sequence} - Sequence name (auto-detected)
{file_ext} - Original file extension"""
        
        self.help_label = QLabel(desc_text)
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("QLabel { background: #4a4a4a; padding: 15px; border-radius: 6px; color: #cccccc; }")
        right_layout.addWidget(self.help_label)
        
        # Folder rules section
        rules_header = QLabel("Folder Rules:")
        rules_header.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(rules_header)
        
        # Rules tree
        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["Priority", "Folder Rule", "Patterns", "Actions"])
        self.rules_tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.rules_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rules_tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.rules_tree.header().setSectionResizeMode(3, QHeaderView.Fixed)
        self.rules_tree.header().resizeSection(0, 80)
        self.rules_tree.header().resizeSection(2, 200)
        self.rules_tree.header().resizeSection(3, 150)
        
        self.rules_tree.itemSelectionChanged.connect(self.on_rule_selected)
        right_layout.addWidget(self.rules_tree)
        
        # Rules management buttons
        rules_btn_layout = QHBoxLayout()
        
        add_rule_btn = QPushButton("➕ Add Rule")
        add_rule_btn.clicked.connect(self.add_folder_rule)
        rules_btn_layout.addWidget(add_rule_btn)
        
        edit_rule_btn = QPushButton("✏️ Edit Rule")
        edit_rule_btn.clicked.connect(self.edit_folder_rule)
        rules_btn_layout.addWidget(edit_rule_btn)
        
        delete_rule_btn = QPushButton("🗑️ Delete Rule")
        delete_rule_btn.clicked.connect(self.delete_folder_rule)
        rules_btn_layout.addWidget(delete_rule_btn)
        
        rules_btn_layout.addStretch()
        
        move_up_btn = QPushButton("⬆️ Move Up")
        move_up_btn.clicked.connect(self.move_rule_up)
        rules_btn_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("⬇️ Move Down")
        move_down_btn.clicked.connect(self.move_rule_down)
        rules_btn_layout.addWidget(move_down_btn)
        
        right_layout.addLayout(rules_btn_layout)
        
        # Initially disable the rules section
        self.rules_tree.setEnabled(False)
        for i in range(rules_btn_layout.count()):
            widget = rules_btn_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(False)
        
        parent.addWidget(right_widget)
        
    def populate_profiles_list(self):
        """Populate the profiles list."""
        self.profiles_list.clear()
        
        for profile_name in self.profiles_data.keys():
            item = QListWidgetItem(profile_name)
            self.profiles_list.addItem(item)
        
        # Select first profile if available
        if self.profiles_list.count() > 0:
            self.profiles_list.setCurrentRow(0)
    
    def on_profile_selected(self):
        """Handle profile selection."""
        selected_items = self.profiles_list.selectedItems()
        
        if not selected_items:
            self.current_profile = None
            self.profile_details_label.setText("Select a profile to edit")
            self.rules_tree.setEnabled(False)
            self.rules_tree.clear()
            return
        
        profile_name = selected_items[0].text()
        self.current_profile = profile_name
        self.profile_details_label.setText(f"Editing Profile: '{profile_name}'")
        
        # Enable rules editing
        self.rules_tree.setEnabled(True)
        for i in range(self.layout().itemAt(1).widget().widget(1).layout().itemAt(-1).layout().count()):
            widget = self.layout().itemAt(1).widget().widget(1).layout().itemAt(-1).layout().itemAt(i).widget()
            if widget:
                widget.setEnabled(True)
        
        # Populate rules
        self.populate_folder_rules()
    
    def populate_folder_rules(self):
        """Populate folder rules for the current profile."""
        self.rules_tree.clear()
        
        if not self.current_profile or self.current_profile not in self.profiles_data:
            return
        
        rules = self.profiles_data[self.current_profile]
        
        for i, rule in enumerate(rules):
            item = QTreeWidgetItem()
            
            # Priority
            priority = rule.get('priority', i + 1)
            item.setText(0, str(priority))
            
            # Folder rule
            folder_rule = rule.get('folderRule', '')
            item.setText(1, folder_rule)
            
            # Patterns
            patterns = rule.get('patterns', [])
            patterns_text = ', '.join(patterns) if patterns else 'None'
            item.setText(2, patterns_text)
            
            # Actions (placeholder)
            item.setText(3, "Edit | Delete")
            
            # Store the rule data
            item.setData(0, Qt.UserRole, rule)
            
            self.rules_tree.addTopLevelItem(item)
    
    def add_profile(self):
        """Add a new profile."""
        profile_name, ok = QInputDialog.getText(
            self,
            "Add Profile",
            "Enter profile name:"
        )
        
        if ok and profile_name:
            if profile_name in self.profiles_data:
                QMessageBox.warning(
                    self,
                    "Profile Exists",
                    f"A profile named '{profile_name}' already exists."
                )
                return
            
            # Create new profile with default rule
            self.profiles_data[profile_name] = [
                {
                    "folderRule": "Organized/{shot}/",
                    "patterns": ["shotPatterns"],
                    "priority": 1
                }
            ]
            
            # Add to list
            item = QListWidgetItem(profile_name)
            self.profiles_list.addItem(item)
            self.profiles_list.setCurrentItem(item)
    
    def duplicate_profile(self):
        """Duplicate the selected profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "No Selection", "Please select a profile to duplicate.")
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Duplicate Profile",
            f"Enter name for copy of '{self.current_profile}':",
            text=f"{self.current_profile} Copy"
        )
        
        if ok and new_name:
            if new_name in self.profiles_data:
                QMessageBox.warning(
                    self,
                    "Profile Exists",
                    f"A profile named '{new_name}' already exists."
                )
                return
            
            # Deep copy the profile
            import copy
            self.profiles_data[new_name] = copy.deepcopy(self.profiles_data[self.current_profile])
            
            # Add to list
            item = QListWidgetItem(new_name)
            self.profiles_list.addItem(item)
            self.profiles_list.setCurrentItem(item)
    
    def rename_profile(self):
        """Rename the selected profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "No Selection", "Please select a profile to rename.")
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Profile",
            f"Enter new name for '{self.current_profile}':",
            text=self.current_profile
        )
        
        if ok and new_name and new_name != self.current_profile:
            if new_name in self.profiles_data:
                QMessageBox.warning(
                    self,
                    "Profile Exists",
                    f"A profile named '{new_name}' already exists."
                )
                return
            
            # Rename the profile
            self.profiles_data[new_name] = self.profiles_data.pop(self.current_profile)
            
            # Update the list
            current_item = self.profiles_list.currentItem()
            current_item.setText(new_name)
            self.current_profile = new_name
            self.profile_details_label.setText(f"Editing Profile: '{new_name}'")
    
    def delete_profile(self):
        """Delete the selected profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "No Selection", "Please select a profile to delete.")
            return
        
        if len(self.profiles_data) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Cannot delete the last profile. At least one profile must exist."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the profile '{self.current_profile}'?"
        )
        
        if reply == QMessageBox.Yes:
            # Remove from data
            del self.profiles_data[self.current_profile]
            
            # Remove from list
            current_item = self.profiles_list.currentItem()
            row = self.profiles_list.row(current_item)
            self.profiles_list.takeItem(row)
            
            # Select another profile
            if self.profiles_list.count() > 0:
                self.profiles_list.setCurrentRow(0)
            else:
                self.current_profile = None
    
    def add_folder_rule(self):
        """Add a new folder rule."""
        if not self.current_profile:
            return
        
        dialog = FolderRuleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            rule_data = dialog.get_rule_data()
            
            # Add to profile
            self.profiles_data[self.current_profile].append(rule_data)
            
            # Refresh the display
            self.populate_folder_rules()
    
    def edit_folder_rule(self):
        """Edit the selected folder rule."""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a rule to edit.")
            return
        
        item = selected_items[0]
        rule_data = item.data(0, Qt.UserRole)
        
        dialog = FolderRuleDialog(self, rule_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_rule = dialog.get_rule_data()
            
            # Update in profile data
            rules = self.profiles_data[self.current_profile]
            rule_index = self.rules_tree.indexOfTopLevelItem(item)
            if 0 <= rule_index < len(rules):
                rules[rule_index] = updated_rule
            
            # Refresh the display
            self.populate_folder_rules()
    
    def delete_folder_rule(self):
        """Delete the selected folder rule."""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a rule to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this folder rule?"
        )
        
        if reply == QMessageBox.Yes:
            item = selected_items[0]
            rule_index = self.rules_tree.indexOfTopLevelItem(item)
            
            # Remove from profile data
            if 0 <= rule_index < len(self.profiles_data[self.current_profile]):
                del self.profiles_data[self.current_profile][rule_index]
            
            # Refresh the display
            self.populate_folder_rules()
    
    def move_rule_up(self):
        """Move selected rule up in priority."""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        rule_index = self.rules_tree.indexOfTopLevelItem(item)
        
        if rule_index > 0:
            rules = self.profiles_data[self.current_profile]
            # Swap rules
            rules[rule_index], rules[rule_index - 1] = rules[rule_index - 1], rules[rule_index]
            # Update priorities
            rules[rule_index]['priority'] = rule_index + 1
            rules[rule_index - 1]['priority'] = rule_index
            
            # Refresh display and maintain selection
            self.populate_folder_rules()
            self.rules_tree.setCurrentItem(self.rules_tree.topLevelItem(rule_index - 1))
    
    def move_rule_down(self):
        """Move selected rule down in priority."""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        rule_index = self.rules_tree.indexOfTopLevelItem(item)
        rules = self.profiles_data[self.current_profile]
        
        if rule_index < len(rules) - 1:
            # Swap rules
            rules[rule_index], rules[rule_index + 1] = rules[rule_index + 1], rules[rule_index]
            # Update priorities
            rules[rule_index]['priority'] = rule_index + 1
            rules[rule_index + 1]['priority'] = rule_index + 2
            
            # Refresh display and maintain selection
            self.populate_folder_rules()
            self.rules_tree.setCurrentItem(self.rules_tree.topLevelItem(rule_index + 1))
    
    def on_rule_selected(self):
        """Handle rule selection."""
        # Could add rule preview or additional details here
        pass
    
    def save_profiles(self):
        """Save profiles to file."""
        try:
            profiles_file = os.path.join(self.config_dir, "profiles.json")
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                "Success",
                "Profiles saved successfully!"
            )
            
            if self.on_save_callback:
                self.on_save_callback("profiles.json")
            
            self.profiles_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save profiles:\n{e}"
            )


class FolderRuleDialog(QDialog):
    """Dialog for editing individual folder rules."""
    
    def __init__(self, parent, rule_data: Optional[Dict] = None):
        super().__init__(parent)
        self.rule_data = rule_data or {}
        
        self.setWindowTitle("Edit Folder Rule")
        self.setModal(True)
        self.resize(600, 500)
        
        self.create_ui()
        self.load_rule_data()
    
    def create_ui(self):
        """Create the rule editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("📁 Folder Rule Configuration")
        header_label.setFont(QFont("", 16, QFont.Bold))
        layout.addWidget(header_label)
        
        # Form
        form_group = QGroupBox("Rule Settings")
        form_layout = QFormLayout(form_group)
        
        # Folder rule path
        self.folder_rule_entry = QLineEdit()
        self.folder_rule_entry.setPlaceholderText("e.g., VFX/Shots/{shot}/{task}/")
        form_layout.addRow("Folder Rule:", self.folder_rule_entry)
        
        # Priority
        self.priority_entry = QLineEdit()
        self.priority_entry.setPlaceholderText("e.g., 1 (lower numbers = higher priority)")
        form_layout.addRow("Priority:", self.priority_entry)
        
        layout.addWidget(form_group)
        
        # Patterns selection
        patterns_group = QGroupBox("Pattern Types")
        patterns_layout = QVBoxLayout(patterns_group)
        
        patterns_help = QLabel("Select which pattern types should trigger this rule:")
        patterns_help.setWordWrap(True)
        patterns_layout.addWidget(patterns_help)
        
        # Available pattern types
        self.pattern_checkboxes = {}
        pattern_types = [
            ("shotPatterns", "Shot Patterns"),
            ("taskPatterns", "Task Patterns"),
            ("assetPatterns", "Asset Patterns"),
            ("versionPatterns", "Version Patterns"),
            ("resolutionPatterns", "Resolution Patterns"),
            ("stagePatterns", "Stage Patterns")
        ]
        
        for pattern_key, pattern_label in pattern_types:
            checkbox = QCheckBox(pattern_label)
            self.pattern_checkboxes[pattern_key] = checkbox
            patterns_layout.addWidget(checkbox)
        
        layout.addWidget(patterns_group)
        
        # Template variables help
        help_group = QGroupBox("Available Template Variables")
        help_layout = QVBoxLayout(help_group)
        
        help_text = """Use these variables in your folder rule:

{shot} - Shot identifier (requires shotPatterns)
{task} - Task name (requires taskPatterns)
{asset} - Asset type (requires assetPatterns)
{version} - Version number (requires versionPatterns)
{resolution} - Resolution (requires resolutionPatterns)
{stage} - Production stage (requires stagePatterns)
{sequence} - Sequence name (auto-detected)
{file_ext} - Original file extension

Example: "VFX/Shots/{shot}/{task}/v{version}/" """
        
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("QLabel { background: #4a4a4a; padding: 10px; border-radius: 4px; }")
        help_layout.addWidget(help_label)
        
        layout.addWidget(help_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Rule")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_rule_data(self):
        """Load rule data into the form."""
        if not self.rule_data:
            return
        
        # Load folder rule
        self.folder_rule_entry.setText(self.rule_data.get('folderRule', ''))
        
        # Load priority
        self.priority_entry.setText(str(self.rule_data.get('priority', 1)))
        
        # Load patterns
        patterns = self.rule_data.get('patterns', [])
        for pattern_key, checkbox in self.pattern_checkboxes.items():
            checkbox.setChecked(pattern_key in patterns)
    
    def get_rule_data(self) -> Dict:
        """Get rule data from the form."""
        # Get selected patterns
        selected_patterns = []
        for pattern_key, checkbox in self.pattern_checkboxes.items():
            if checkbox.isChecked():
                selected_patterns.append(pattern_key)
        
        # Get priority
        try:
            priority = int(self.priority_entry.text())
        except ValueError:
            priority = 1
        
        return {
            'folderRule': self.folder_rule_entry.text(),
            'patterns': selected_patterns,
            'priority': priority
        }
