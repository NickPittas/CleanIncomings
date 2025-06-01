"""
PyQt5 Widget Factory - Enhanced Modular UI Components
Converts tkinter/customtkinter components to PyQt5 equivalents with modern styling
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QVBoxLayout, QHBoxLayout,
    QSplitter, QHeaderView, QAbstractItemView, QCheckBox, QProgressBar,
    QGridLayout, QScrollArea, QGroupBox, QTabWidget, QListWidget, 
    QListWidgetItem, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap
import os
from typing import Optional, List, Dict, Any, Callable
from PyQt5.QtGui import QFont, QIcon, QPixmap
import os


class WidgetFactory:
    """Creates and configures PyQt5 widgets for the GUI with Nuke-style theming."""
    
    def __init__(self, app):
        self.app = app
        self.icon_cache = {}
        self._load_icons()
        
    def _load_icons(self):
        """Load and cache icons for reuse."""
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "icons")
        
        icon_files = {
            'folder': 'folder_open_16.png',
            'folder_closed': 'folder_closed_16.png',
            'file': 'file_16.png',
            'sequence': 'sequence_16.png',
            'image': 'image_16.png',
            'video': 'video_16.png',
            'audio': 'audio_16.png',
            'settings': 'settings_16.png',
            'refresh': 'refresh_16.png',
            'task': 'task_16.png',
            'asset': 'asset_16.png',
            'arrow_up': 'arrow_up_16.png',
            'arrow_down': 'arrow_down_16.png',
            'arrow_right': 'arrow_right_16.png'
        }
        
        for icon_name, icon_file in icon_files.items():
            icon_path = os.path.join(icons_dir, icon_file)
            if os.path.exists(icon_path):
                self.icon_cache[icon_name] = QIcon(icon_path)
            else:
                # Create empty icon as fallback
                self.icon_cache[icon_name] = QIcon()
    
    def get_icon(self, icon_name: str) -> QIcon:
        """Get a cached icon by name."""
        return self.icon_cache.get(icon_name, QIcon())

    def create_widgets(self):
        """Create all widgets - this method maintains compatibility with the tkinter version."""
        # In the PyQt5 version, widgets are created in the main app's _create_ui method
        # This method exists for compatibility but doesn't need to do anything
        pass
        
    def get_icon_path(self, icon_name, size=16):
        """Get the path to an icon file."""
        if not icon_name:
            return None
            
        # Try different variations of the icon name
        icon_variations = [
            f"{icon_name}_{size}.png",
            f"{icon_name}.png",
            f"{icon_name}_16.png",
            f"{icon_name}_24.png",
            f"{icon_name}_32.png"
        ]
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "icons")
        
        for variation in icon_variations:
            icon_path = os.path.join(icons_dir, variation)
            if os.path.exists(icon_path):
                return icon_path
                
        return None
        
    def create_icon_button(self, parent, text, icon_name=None, callback=None, **kwargs):
        """Create a button with an icon."""
        button = QPushButton(text, parent)
        
        if icon_name:
            icon_path = self.get_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                
        if callback:
            button.clicked.connect(callback)
            
        # Apply any additional properties
        if 'width' in kwargs:
            button.setMinimumWidth(kwargs['width'])
        if 'height' in kwargs:
            button.setMinimumHeight(kwargs['height'])
        if 'object_name' in kwargs:
            button.setObjectName(kwargs['object_name'])
            
        return button

    # Enhanced button creation methods
    def create_accent_button(self, text: str, icon_name: Optional[str] = None,
                           tooltip: Optional[str] = None, min_width: Optional[int] = None,
                           max_width: Optional[int] = None) -> QPushButton:
        """Create an accent-styled button."""
        button = QPushButton(text)
        button.setObjectName("accent")
        
        if icon_name and icon_name in self.icon_cache:
            button.setIcon(self.get_icon(icon_name))
        
        if tooltip:
            button.setToolTip(tooltip)
        
        if min_width:
            button.setMinimumWidth(min_width)
        if max_width:
            button.setMaximumWidth(max_width)
        
        return button
    
    def create_compact_button(self, text: str, icon_name: Optional[str] = None,
                            tooltip: Optional[str] = None) -> QPushButton:
        """Create a compact-styled button."""
        button = QPushButton(text)
        button.setObjectName("compact")
        
        if icon_name and icon_name in self.icon_cache:
            button.setIcon(self.get_icon(icon_name))
        
        if tooltip:
            button.setToolTip(tooltip)
        
        button.setMaximumWidth(35)
        
        return button

    def create_header_label(self, text: str) -> QLabel:
        """Create a header-style label."""
        label = QLabel(text)
        label.setObjectName("header")
        font = label.font()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        return label
    
    def create_group_box(self, title: str, layout_type: str = "vertical") -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        
        if layout_type == "vertical":
            layout = QVBoxLayout(group)
        elif layout_type == "horizontal":
            layout = QHBoxLayout(group)
        elif layout_type == "grid":
            layout = QGridLayout(group)
        else:
            layout = QVBoxLayout(group)
        
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        return group

    def create_tree_widget(self, parent, columns, **kwargs):
        """Create a tree widget with specified columns."""
        tree = QTreeWidget(parent)
        tree.setHeaderLabels(columns)
        
        # Configure header
        header = tree.header()
        for i, column in enumerate(columns):
            if i == 0 and 'first_column_width' in kwargs:
                header.resizeSection(i, kwargs['first_column_width'])
            elif 'column_widths' in kwargs and i < len(kwargs['column_widths']):
                header.resizeSection(i, kwargs['column_widths'][i])
                
        # Set selection mode
        if kwargs.get('multi_select', False):
            tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            tree.setSelectionMode(QAbstractItemView.SingleSelection)
            
        return tree

    # Enhanced tree creation methods
    def create_source_tree(self) -> QTreeWidget:
        """Create the source tree widget with proper configuration."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name", "Type", "Size"])
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        tree.header().resizeSection(1, 80)
        tree.header().resizeSection(2, 80)
        
        # Add compatibility methods
        def get_children():
            root = tree.invisibleRootItem()
            return [root.child(i) for i in range(root.childCount())]
            
        def delete(item):
            if hasattr(item, 'parent') and item.parent():
                item.parent().removeChild(item)
            else:
                root = tree.invisibleRootItem()
                root.removeChild(item)
        
        tree.get_children = get_children
        tree.delete = delete
        
        return tree
    
    def create_preview_tree(self) -> QTreeWidget:
        """Create the preview tree widget with proper configuration."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["☐", "File/Sequence Name", "Task", "Asset", "New Destination Path", "Matched Tags"])
        tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        tree.header().setSectionResizeMode(3, QHeaderView.Fixed)
        tree.header().setSectionResizeMode(4, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(5, QHeaderView.Fixed)
        
        # Set column widths
        tree.header().resizeSection(0, 40)   # Checkbox
        tree.header().resizeSection(1, 200)  # Filename
        tree.header().resizeSection(2, 80)   # Task
        tree.header().resizeSection(3, 80)   # Asset
        tree.header().resizeSection(5, 150)  # Tags
        
        tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        
        # Add compatibility methods
        def get_children():
            root = tree.invisibleRootItem()
            return [root.child(i) for i in range(root.childCount())]
            
        def delete(item):
            if hasattr(item, 'parent') and item.parent():
                item.parent().removeChild(item)
            else:
                root = tree.invisibleRootItem()
                root.removeChild(item)
        
        tree.get_children = get_children
        tree.delete = delete
        
        return tree
        
    def clear_tree_widget(self, tree_widget):
        """Clear all items from a tree widget (PyQt5 equivalent of tkinter's get_children/delete)."""
        tree_widget.clear()
        
    def add_tree_item(self, tree_widget, values, parent=None):
        """Add an item to a tree widget."""
        if parent is None:
            item = QTreeWidgetItem(tree_widget)
        else:
            item = QTreeWidgetItem(parent)
        item.setText(0, str(values.get("name", "")))
        item.setText(1, str(values.get("status", "")))
        item.setText(2, str(values.get("path", "")))
        item.setText(3, str(values.get("type", "")))
        item.setText(4, str(values.get("size", "")))
        item.setText(5, str(values.get("date_modified", "")))
        return item
        
    def get_tree_selection(self, tree_widget):
        """Get selected items from a tree widget."""
        return tree_widget.selectedItems()
        
    def set_tree_selection(self, tree_widget, items):
        """Set selected items in a tree widget."""
        tree_widget.clearSelection()
        for item in items:
            item.setSelected(True)
            
    def create_resizable_layout(self, parent, orientation=Qt.Horizontal):
        """Create a resizable splitter layout."""
        splitter = QSplitter(orientation, parent)
        return splitter
        
    def create_frame(self, parent, **kwargs):
        """Create a frame widget."""
        frame = QFrame(parent)
        
        if 'object_name' in kwargs:
            frame.setObjectName(kwargs['object_name'])
            
        return frame
        
    def create_label(self, text_content: str, parent: Optional[QWidget] = None, icon_name: Optional[str] = None, bold: bool = False, font_size: Optional[int] = None, object_name: Optional[str] = None) -> QLabel:
        """Create a label widget."""
        label = QLabel(text_content, parent)  # Corrected order

        if object_name:
            label.setObjectName(object_name)

        current_font = label.font()
        if font_size:
            current_font.setPointSize(font_size)
        if bold:
            current_font.setBold(True)
        label.setFont(current_font)

        if icon_name:
            icon = self.get_icon(icon_name)
            if not icon.isNull():
                # This will set the pixmap. If text is also set, QLabel tries to display both.
                # For a true "compound left" effect like CTkLabel, a more complex setup
                # (e.g., custom widget or QHBoxLayout with two QLabels) would be needed.
                # This basic version primarily fixes the constructor TypeError.
                label.setPixmap(icon.pixmap(QSize(16, 16)))
        return label
        
    def create_line_edit(self, parent, placeholder="", **kwargs):
        """Create a line edit widget."""
        edit = QLineEdit(parent)
        
        if placeholder:
            edit.setPlaceholderText(placeholder)
            
        if 'object_name' in kwargs:
            edit.setObjectName(kwargs['object_name'])
            
        return edit
        
    def create_combo_box(self, parent, items=None, **kwargs):
        """Create a combo box widget."""
        combo = QComboBox(parent)
        
        if items:
            combo.addItems(items)
            
        if 'width' in kwargs:
            combo.setMinimumWidth(kwargs['width'])
        if 'object_name' in kwargs:
            combo.setObjectName(kwargs['object_name'])
            
        return combo
        
    def create_text_edit(self, parent, **kwargs):
        """Create a text edit widget."""
        text_edit = QTextEdit(parent)
        
        if 'read_only' in kwargs and kwargs['read_only']:
            text_edit.setReadOnly(True)
        if 'object_name' in kwargs:
            text_edit.setObjectName(kwargs['object_name'])
            
        return text_edit
        
    def create_progress_bar(self, parent, **kwargs):
        """Create a progress bar widget."""
        progress = QProgressBar(parent)
        
        if 'minimum' in kwargs:
            progress.setMinimum(kwargs['minimum'])
        if 'maximum' in kwargs:
            progress.setMaximum(kwargs['maximum'])
        if 'object_name' in kwargs:
            progress.setObjectName(kwargs['object_name'])
            
        return progress
        
    def create_checkbox(self, parent, text="", **kwargs):
        """Create a checkbox widget."""
        checkbox = QCheckBox(text, parent)
        
        if 'object_name' in kwargs:
            checkbox.setObjectName(kwargs['object_name'])
            
        return checkbox
        
    # Compatibility methods for tkinter-style operations
    def configure_widget(self, widget, **kwargs):
        """Configure a widget with various properties (compatibility method)."""
        if hasattr(widget, 'setText') and 'text' in kwargs:
            widget.setText(kwargs['text'])
        if hasattr(widget, 'setEnabled') and 'state' in kwargs:
            widget.setEnabled(kwargs['state'] != 'disabled')
        if hasattr(widget, 'clear') and 'values' in kwargs:
            widget.clear()
            if hasattr(widget, 'addItems'):
                widget.addItems(kwargs['values'])
                
    def pack_widget(self, widget, layout, **kwargs):
        """Add widget to layout (compatibility method)."""
        if hasattr(layout, 'addWidget'):
            layout.addWidget(widget)
        elif hasattr(layout, 'addLayout'):
            layout.addLayout(widget)
            
    def grid_widget(self, widget, layout, row=0, column=0, **kwargs):
        """Add widget to grid layout (compatibility method)."""
        # PyQt5 uses different layout management, this is for compatibility
        if hasattr(layout, 'addWidget'):
            layout.addWidget(widget)
