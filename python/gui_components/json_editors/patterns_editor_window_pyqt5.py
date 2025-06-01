"""
PyQt5 Patterns Editor Window - Advanced visual editor for patterns.json
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QPushButton, QFrame, QTextEdit, QListWidget, QListWidgetItem,
    QLineEdit, QGroupBox, QFormLayout, QSplitter, QMessageBox,
    QScrollArea, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os
import json
import re
from typing import Dict, List, Any, Optional, Callable


class PatternsEditorWindow(QDialog):
    """Visual editor for patterns.json with tabbed interface."""
    
    patterns_changed = pyqtSignal()
    
    def __init__(self, parent, config_dir: str, on_save_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.on_save_callback = on_save_callback
        self.patterns_data = {}
        
        self.setWindowTitle("Patterns Configuration Editor")
        self.setModal(False)  # Allow interaction with parent
        self.resize(1200, 800)
        
        # Center on parent
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 1200) // 2
            y = parent_geo.y() + (parent_geo.height() - 800) // 2
            self.move(x, y)
        
        self.load_patterns()
        self.create_ui()
        
    def load_patterns(self):
        """Load patterns from patterns.json."""
        patterns_file = os.path.join(self.config_dir, "patterns.json")
        default_patterns = {
            "shotPatterns": [],
            "taskPatterns": {},
            "resolutionPatterns": [],
            "versionPatterns": [],
            "assetPatterns": [],
            "stagePatterns": []
        }
        
        try:
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.patterns_data = json.load(f)
            else:
                self.patterns_data = default_patterns
                
            # Ensure all required keys exist
            for key in default_patterns:
                if key not in self.patterns_data:
                    self.patterns_data[key] = default_patterns[key]
                    
        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load patterns.json:\n{e}\n\nUsing default patterns."
            )
            self.patterns_data = default_patterns
    
    def create_ui(self):
        """Create the patterns editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎨 Patterns Configuration Editor")
        title_label.setFont(QFont("", 18, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Header buttons
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self.save_patterns)
        header_layout.addWidget(save_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.create_pattern_tabs()
        
    def create_pattern_tabs(self):
        """Create tabs for different pattern types."""
        # Simple pattern tabs (lists)
        simple_patterns = [
            ("Shot Patterns", "shotPatterns", 
             "Regex patterns for shot identification\n(e.g., SC\\d{3}, sh\\d{3}, SHOT_\\d{4})"),
            ("Resolution Patterns", "resolutionPatterns", 
             "Resolution identifiers\n(e.g., 4k, 2k, hd, uhd, 1080p, 720p)"),
            ("Version Patterns", "versionPatterns", 
             "Version number patterns\n(e.g., v\\d{3}, ver\\d{3}, V\\d{2})"),
            ("Asset Patterns", "assetPatterns", 
             "Asset type keywords\n(e.g., hero, vehicle, character, prop, environment)"),
            ("Stage Patterns", "stagePatterns", 
             "Production stage keywords\n(e.g., PREVIZ, ANIM, LAYOUT, COMP, LIGHTING)")
        ]
        
        for tab_name, pattern_key, description in simple_patterns:
            tab = self.create_simple_pattern_tab(pattern_key, description)
            self.tab_widget.addTab(tab, tab_name)
        
        # Special tab for task patterns (dictionary)
        task_tab = self.create_task_patterns_tab()
        self.tab_widget.addTab(task_tab, "Task Patterns")
        
    def create_simple_pattern_tab(self, pattern_key: str, description: str):
        """Create a tab for simple pattern lists."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { background: #4a4a4a; padding: 15px; border-radius: 6px; color: #cccccc; }")
        layout.addWidget(desc_label)
        
        # Splitter for two-column layout
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Pattern list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        list_header = QLabel("Current Patterns:")
        list_header.setFont(QFont("", 12, QFont.Bold))
        left_layout.addWidget(list_header)
        
        pattern_list = QListWidget()
        pattern_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Populate the list
        patterns = self.patterns_data.get(pattern_key, [])
        for pattern in patterns:
            item = QListWidgetItem(pattern)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            pattern_list.addItem(item)
        
        left_layout.addWidget(pattern_list)
        
        # List buttons
        list_btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Pattern")
        add_btn.clicked.connect(lambda: self.add_pattern_to_list(pattern_list))
        list_btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(lambda: self.remove_selected_patterns(pattern_list))
        list_btn_layout.addWidget(remove_btn)
        
        list_btn_layout.addStretch()
        left_layout.addLayout(list_btn_layout)
        
        splitter.addWidget(left_widget)
        
        # Right side - Pattern editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        editor_header = QLabel("Pattern Editor:")
        editor_header.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(editor_header)
        
        # Pattern entry
        pattern_entry = QLineEdit()
        pattern_entry.setPlaceholderText("Enter new pattern...")
        right_layout.addWidget(pattern_entry)
        
        # Test area
        test_label = QLabel("Test Pattern:")
        right_layout.addWidget(test_label)
        
        test_input = QLineEdit()
        test_input.setPlaceholderText("Enter text to test against pattern...")
        right_layout.addWidget(test_input)
        
        test_result = QLabel("Test result will appear here")
        test_result.setStyleSheet("QLabel { background: #3a3a3a; padding: 10px; border-radius: 4px; }")
        right_layout.addWidget(test_result)
        
        # Connect test functionality
        def test_pattern():
            pattern = pattern_entry.text()
            test_text = test_input.text()
            
            if not pattern or not test_text:
                test_result.setText("Enter both pattern and test text")
                test_result.setStyleSheet("QLabel { background: #3a3a3a; padding: 10px; border-radius: 4px; color: #aaa; }")
                return
            
            try:
                if re.search(pattern, test_text, re.IGNORECASE):
                    test_result.setText(f"✅ MATCH: '{test_text}' matches pattern '{pattern}'")
                    test_result.setStyleSheet("QLabel { background: #2a4a2a; padding: 10px; border-radius: 4px; color: #90ff90; }")
                else:
                    test_result.setText(f"❌ NO MATCH: '{test_text}' does not match pattern '{pattern}'")
                    test_result.setStyleSheet("QLabel { background: #4a2a2a; padding: 10px; border-radius: 4px; color: #ff9090; }")
            except re.error as e:
                test_result.setText(f"❌ INVALID REGEX: {e}")
                test_result.setStyleSheet("QLabel { background: #4a2a2a; padding: 10px; border-radius: 4px; color: #ff9090; }")
        
        pattern_entry.textChanged.connect(test_pattern)
        test_input.textChanged.connect(test_pattern)
        
        # Add pattern button
        add_pattern_btn = QPushButton("Add to List")
        add_pattern_btn.setObjectName("accent")
        add_pattern_btn.clicked.connect(lambda: self.add_pattern_from_entry(pattern_entry, pattern_list))
        right_layout.addWidget(add_pattern_btn)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        
        # Set splitter sizes
        splitter.setSizes([400, 500])
        
        # Store references for saving
        setattr(tab, 'pattern_list', pattern_list)
        setattr(tab, 'pattern_key', pattern_key)
        
        return tab
    
    def create_task_patterns_tab(self):
        """Create the special tab for task patterns (dictionary structure)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Description
        desc_text = ("Task patterns organize keywords into categories.\n"
                    "Each task category can have multiple aliases/keywords.\n"
                    "Example: 'compositing': ['comp', 'composite', 'final']")
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("QLabel { background: #4a4a4a; padding: 15px; border-radius: 6px; color: #cccccc; }")
        layout.addWidget(desc_label)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left side - Task categories
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        categories_label = QLabel("Task Categories:")
        categories_label.setFont(QFont("", 12, QFont.Bold))
        left_layout.addWidget(categories_label)
        
        self.task_categories_list = QListWidget()
        self.task_categories_list.itemSelectionChanged.connect(self.on_task_category_selected)
        left_layout.addWidget(self.task_categories_list)
        
        # Category buttons
        cat_btn_layout = QHBoxLayout()
        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.clicked.connect(self.add_task_category)
        cat_btn_layout.addWidget(add_cat_btn)
        
        remove_cat_btn = QPushButton("Remove Category")
        remove_cat_btn.clicked.connect(self.remove_task_category)
        cat_btn_layout.addWidget(remove_cat_btn)
        
        left_layout.addLayout(cat_btn_layout)
        
        content_layout.addWidget(left_widget)
        
        # Right side - Keywords for selected category
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.keywords_label = QLabel("Keywords for category:")
        self.keywords_label.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(self.keywords_label)
        
        self.task_keywords_list = QListWidget()
        self.task_keywords_list.setEnabled(False)
        right_layout.addWidget(self.task_keywords_list)
        
        # Keyword entry
        keyword_entry_layout = QHBoxLayout()
        self.keyword_entry = QLineEdit()
        self.keyword_entry.setPlaceholderText("Enter keyword...")
        self.keyword_entry.setEnabled(False)
        self.keyword_entry.returnPressed.connect(self.add_keyword_to_category)
        keyword_entry_layout.addWidget(self.keyword_entry)
        
        add_keyword_btn = QPushButton("Add")
        add_keyword_btn.clicked.connect(self.add_keyword_to_category)
        add_keyword_btn.setEnabled(False)
        keyword_entry_layout.addWidget(add_keyword_btn)
        
        right_layout.addLayout(keyword_entry_layout)
        
        # Keyword buttons
        keyword_btn_layout = QHBoxLayout()
        remove_keyword_btn = QPushButton("Remove Selected")
        remove_keyword_btn.clicked.connect(self.remove_selected_keywords)
        remove_keyword_btn.setEnabled(False)
        keyword_btn_layout.addWidget(remove_keyword_btn)
        keyword_btn_layout.addStretch()
        
        right_layout.addLayout(keyword_btn_layout)
        
        # Store button references
        self.add_keyword_btn = add_keyword_btn
        self.remove_keyword_btn = remove_keyword_btn
        
        content_layout.addWidget(right_widget)
        layout.addLayout(content_layout)
        
        # Populate task patterns
        self.populate_task_patterns()
        
        return tab
    
    def populate_task_patterns(self):
        """Populate task patterns into the UI."""
        task_patterns = self.patterns_data.get("taskPatterns", {})
        
        self.task_categories_list.clear()
        for category in task_patterns.keys():
            item = QListWidgetItem(category)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.task_categories_list.addItem(item)
    
    def on_task_category_selected(self):
        """Handle task category selection."""
        selected_items = self.task_categories_list.selectedItems()
        
        if not selected_items:
            self.task_keywords_list.setEnabled(False)
            self.keyword_entry.setEnabled(False)
            self.add_keyword_btn.setEnabled(False)
            self.remove_keyword_btn.setEnabled(False)
            self.keywords_label.setText("Keywords for category:")
            self.task_keywords_list.clear()
            return
        
        category_name = selected_items[0].text()
        self.keywords_label.setText(f"Keywords for '{category_name}':")
        
        # Enable keyword editing
        self.task_keywords_list.setEnabled(True)
        self.keyword_entry.setEnabled(True)
        self.add_keyword_btn.setEnabled(True)
        self.remove_keyword_btn.setEnabled(True)
        
        # Populate keywords
        task_patterns = self.patterns_data.get("taskPatterns", {})
        keywords = task_patterns.get(category_name, [])
        
        self.task_keywords_list.clear()
        for keyword in keywords:
            item = QListWidgetItem(keyword)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.task_keywords_list.addItem(item)
    
    def add_task_category(self):
        """Add a new task category."""
        from PyQt5.QtWidgets import QInputDialog
        
        category_name, ok = QInputDialog.getText(
            self, 
            "Add Task Category", 
            "Enter category name:"
        )
        
        if ok and category_name:
            # Add to data
            if "taskPatterns" not in self.patterns_data:
                self.patterns_data["taskPatterns"] = {}
            
            self.patterns_data["taskPatterns"][category_name] = []
            
            # Add to list
            item = QListWidgetItem(category_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.task_categories_list.addItem(item)
            
            # Select the new item
            self.task_categories_list.setCurrentItem(item)
    
    def remove_task_category(self):
        """Remove selected task category."""
        selected_items = self.task_categories_list.selectedItems()
        if not selected_items:
            return
        
        category_name = selected_items[0].text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the category '{category_name}' and all its keywords?"
        )
        
        if reply == QMessageBox.Yes:
            # Remove from data
            if "taskPatterns" in self.patterns_data and category_name in self.patterns_data["taskPatterns"]:
                del self.patterns_data["taskPatterns"][category_name]
            
            # Remove from list
            row = self.task_categories_list.row(selected_items[0])
            self.task_categories_list.takeItem(row)
    
    def add_keyword_to_category(self):
        """Add keyword to selected category."""
        keyword = self.keyword_entry.text().strip()
        if not keyword:
            return
        
        selected_items = self.task_categories_list.selectedItems()
        if not selected_items:
            return
        
        category_name = selected_items[0].text()
        
        # Add to data
        if "taskPatterns" not in self.patterns_data:
            self.patterns_data["taskPatterns"] = {}
        if category_name not in self.patterns_data["taskPatterns"]:
            self.patterns_data["taskPatterns"][category_name] = []
        
        if keyword not in self.patterns_data["taskPatterns"][category_name]:
            self.patterns_data["taskPatterns"][category_name].append(keyword)
            
            # Add to list
            item = QListWidgetItem(keyword)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.task_keywords_list.addItem(item)
        
        self.keyword_entry.clear()
    
    def remove_selected_keywords(self):
        """Remove selected keywords from category."""
        selected_items = self.task_keywords_list.selectedItems()
        if not selected_items:
            return
        
        category_items = self.task_categories_list.selectedItems()
        if not category_items:
            return
        
        category_name = category_items[0].text()
        
        for item in selected_items:
            keyword = item.text()
            
            # Remove from data
            if ("taskPatterns" in self.patterns_data and 
                category_name in self.patterns_data["taskPatterns"] and
                keyword in self.patterns_data["taskPatterns"][category_name]):
                self.patterns_data["taskPatterns"][category_name].remove(keyword)
            
            # Remove from list
            row = self.task_keywords_list.row(item)
            self.task_keywords_list.takeItem(row)
    
    def add_pattern_to_list(self, pattern_list: QListWidget):
        """Add a new pattern to the list."""
        item = QListWidgetItem("new_pattern")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        pattern_list.addItem(item)
        pattern_list.setCurrentItem(item)
        pattern_list.editItem(item)
    
    def add_pattern_from_entry(self, entry: QLineEdit, pattern_list: QListWidget):
        """Add pattern from entry field to list."""
        pattern = entry.text().strip()
        if pattern:
            item = QListWidgetItem(pattern)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            pattern_list.addItem(item)
            entry.clear()
    
    def remove_selected_patterns(self, pattern_list: QListWidget):
        """Remove selected patterns from list."""
        for item in pattern_list.selectedItems():
            row = pattern_list.row(item)
            pattern_list.takeItem(row)
    
    def collect_patterns_from_ui(self):
        """Collect all patterns from the UI."""
        collected_data = {}
        
        # Collect simple patterns
        for i in range(self.tab_widget.count() - 1):  # Exclude task patterns tab
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'pattern_list') and hasattr(tab, 'pattern_key'):
                pattern_list = tab.pattern_list
                pattern_key = tab.pattern_key
                
                patterns = []
                for row in range(pattern_list.count()):
                    item = pattern_list.item(row)
                    pattern = item.text().strip()
                    if pattern:
                        patterns.append(pattern)
                
                collected_data[pattern_key] = patterns
        
        # Collect task patterns
        task_patterns = {}
        for row in range(self.task_categories_list.count()):
            category_item = self.task_categories_list.item(row)
            category_name = category_item.text()
            
            # Get keywords for this category
            if category_name in self.patterns_data.get("taskPatterns", {}):
                task_patterns[category_name] = self.patterns_data["taskPatterns"][category_name]
        
        collected_data["taskPatterns"] = task_patterns
        
        return collected_data
    
    def save_patterns(self):
        """Save patterns to file."""
        try:
            # Collect current data from UI
            self.patterns_data = self.collect_patterns_from_ui()
            
            # Save to file
            patterns_file = os.path.join(self.config_dir, "patterns.json")
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                "Success",
                "Patterns saved successfully!"
            )
            
            if self.on_save_callback:
                self.on_save_callback("patterns.json")
            
            self.patterns_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save patterns:\n{e}"
            )
