"""
Nuke-inspired Dark Theme Stylesheet for PyQt5
Based on Foundry Nuke's interface design with HiDPI support
"""

NUKE_DARK_STYLESHEET = """
/* Main Application - HiDPI Aware */
QMainWindow {
    background-color: #393939;
    color: #cccccc;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11px;
}

/* Frames and Containers */
QFrame {
    background-color: #3a3a3a;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
}

QFrame[class="control_panel_frame"] {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 8px;
    padding: 8px;
}

QFrame[class="transparent"] {
    background-color: transparent;
    border: none;
}

QWidget {
    background-color: #393939;
    color: #cccccc;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Labels */
QLabel {
    background-color: transparent;
    color: #cccccc;
    font-size: 11px;
    font-weight: normal;
    border: none;
}

QLabel[class="header"] {
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}

QLabel[class="small"] {
    font-size: 10px;
    color: #999999;
}

/* Buttons - Enhanced with HiDPI support */
QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    color: #cccccc;
    font-size: 12px;
    font-weight: normal;
    padding: 6px 12px;
    min-height: 16px;
    text-align: center;
}

QPushButton:hover {
    background-color: #5a5a5a;
    border-color: #ff6600;
}

QPushButton:pressed {
    background-color: #333333;
    border-color: #ff6600;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
    border-color: #2a2a2a;
}

QPushButton[class="accent"] {
    background-color: #ff6600;
    color: #ffffff;
    border-color: #cc5500;
}

QPushButton[class="accent"]:hover {
    background-color: #ff7700;
}

QPushButton[class="accent"]:pressed {
    background-color: #cc5500;
}

QPushButton[class="small"] {
    padding: 4px 8px;
    font-size: 10px;
    min-height: 12px;
}

QPushButton[class="compact"] {
    padding: 4px 6px;
    font-size: 14px;
    min-height: 20px;
    max-height: 28px;
    min-width: 28px;
    border-radius: 4px;
}

QPushButton[class="compact"]:hover {
    background-color: #5a5a5a;
    border-color: #ff6600;
}

/* Text Input Fields */
QLineEdit {
    background-color: #2a2a2a;
    border: 1px solid #333333;
    border-radius: 4px;
    color: #cccccc;
    font-size: 11px;
    padding: 6px;
    selection-background-color: #ff6600;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border-color: #ff6600;
    background-color: #333333;
}

QLineEdit:disabled {
    background-color: #1a1a1a;
    color: #666666;
    border-color: #2a2a2a;
}

/* Text Areas */
QTextEdit {
    background-color: #2a2a2a;
    border: 1px solid #333333;
    border-radius: 4px;
    color: #cccccc;
    font-size: 12px;
    selection-background-color: #ff6600;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border-color: #ff6600;
}

QTextEdit:disabled {
    background-color: #1a1a1a;
    color: #666666;
    border-color: #2a2a2a;
}

/* Combo Boxes */
QComboBox {
    background-color: #4a4a4a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    color: #cccccc;
    font-size: 12px;
    padding: 6px;
    min-width: 60px;
}

QComboBox:hover {
    border-color: #ff6600;
    background-color: #5a5a5a;
}

QComboBox:focus {
    border-color: #ff6600;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(icons/arrow_down_16.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #4a4a4a;
    border: 1px solid #ff6600;
    border-radius: 4px;
    color: #cccccc;
    selection-background-color: #ff6600;
    selection-color: #ffffff;
}

/* Tree Widgets */
QTreeWidget {
    background-color: #2a2a2a;
    border: 1px solid #333333;
    border-radius: 4px;
    color: #cccccc;
    font-size: 12px;
    selection-background-color: #ff6600;
    selection-color: #ffffff;
    alternate-background-color: #333333;
}

QTreeWidget::item {
    padding: 4px;
    border: none;
}

QTreeWidget::item:hover {
    background-color: #4a4a4a;
}

QTreeWidget::item:selected {
    background-color: #ff6600;
    color: #ffffff;
}

QTreeWidget::item:selected:!active {
    background-color: #cc5500;
}

QTreeWidget::branch {
    background-color: transparent;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: url(icons/branch-closed.png);
}

QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    image: url(icons/branch-open.png);
}

/* Header Views */
QHeaderView {
    background-color: #4a4a4a;
    border: none;
    border-bottom: 1px solid #2a2a2a;
}

QHeaderView::section {
    background-color: #4a4a4a;
    border: none;
    border-right: 1px solid #2a2a2a;
    color: #cccccc;
    font-size: 12px;
    font-weight: bold;
    padding: 6px;
    text-align: left;
}

QHeaderView::section:hover {
    background-color: #5a5a5a;
}

QHeaderView::section:pressed {
    background-color: #ff6600;
    color: #ffffff;
}

/* Splitters */
QSplitter {
    background-color: #3a3a3a;
}

QSplitter::handle {
    background-color: #555555;
    border: none;
}

QSplitter::handle:horizontal {
    width: 1px;
    margin: 0px;
    border-radius: 0px;
}

QSplitter::handle:vertical {
    height: 1px;
    margin: 0px;
    border-radius: 0px;
}

QSplitter::handle:hover {
    background-color: #777777;
}

QSplitter::handle:pressed {
    background-color: #999999;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #2a2a2a;
    width: 12px;
    border: none;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::handle:vertical:pressed {
    background-color: #ff6600;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2a2a2a;
    height: 12px;
    border: none;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #ff6600;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}

/* Progress Bars */
QProgressBar {
    background-color: #2a2a2a;
    border: 1px solid #333333;
    border-radius: 4px;
    color: #cccccc;
    text-align: center;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #ff6600;
    border-radius: 3px;
}

/* Dialogs */
QDialog {
    background-color: #393939;
    color: #cccccc;
    border: 1px solid #2a2a2a;
}

/* Menus */
QMenu {
    background-color: #4a4a4a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    color: #cccccc;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #ff6600;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #666666;
}

/* Status Bar */
QStatusBar {
    background-color: #2a2a2a;
    border-top: 1px solid #555555;
    color: #cccccc;
    font-size: 11px;
    padding: 4px;
}

QStatusBar::item {
    border: none;
}

/* Tabs */
QTabWidget {
    background-color: #3a3a3a;
    border: none;
}

QTabWidget::pane {
    border: 1px solid #555555;
    border-radius: 6px;
    background-color: #3a3a3a;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #4a4a4a;
    border: 1px solid #2a2a2a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #cccccc;
    padding: 6px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ff6600;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #5a5a5a;
}

/* Checkboxes */
QCheckBox {
    color: #cccccc;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #333333;
    border-radius: 3px;
    background-color: #2a2a2a;
}

QCheckBox::indicator:hover {
    border-color: #ff6600;
}

QCheckBox::indicator:checked {
    background-color: #ff6600;
    border-color: #ff6600;
    image: url(icons/check.png);
}

/* Radio Buttons */
QRadioButton {
    color: #cccccc;
    font-size: 12px;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #333333;
    border-radius: 8px;
    background-color: #2a2a2a;
}

QRadioButton::indicator:hover {
    border-color: #ff6600;
}

QRadioButton::indicator:checked {
    background-color: #ff6600;
    border-color: #ff6600;
}

/* Group Boxes */
QGroupBox {
    background-color: #3a3a3a;
    border: 2px solid #555555;
    border-radius: 8px;
    color: #cccccc;
    font-size: 12px;
    font-weight: bold;
    margin-top: 10px;
    padding-top: 5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    color: #ff6600;
    font-weight: bold;
}

/* List Widgets */
QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #333333;
    border-radius: 4px;
    color: #cccccc;
    font-size: 12px;
    selection-background-color: #ff6600;
    selection-color: #ffffff;
    alternate-background-color: #333333;
}

QListWidget::item {
    padding: 4px;
    border: none;
}

QListWidget::item:hover {
    background-color: #4a4a4a;
}

QListWidget::item:selected {
    background-color: #ff6600;
    color: #ffffff;
}

/* Tool Tips */
QToolTip {
    background-color: #4a4a4a;
    border: 1px solid #ff6600;
    border-radius: 4px;
    color: #ffffff;
    font-size: 11px;
    padding: 4px;
}

/* Message Boxes */
QMessageBox {
    background-color: #3a3a3a;
    color: #cccccc;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 12px;
}

/* File Dialogs */
QFileDialog {
    background-color: #3a3a3a;
    color: #cccccc;
}

QFileDialog QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    color: #cccccc;
    padding: 6px 12px;
}

QFileDialog QPushButton:hover {
    background-color: #5a5a5a;
    border-color: #ff6600;
}

QFileDialog QPushButton[default="true"] {
    background-color: #ff6600;
    color: #ffffff;
    border-color: #cc5500;
}
"""

# Utility function to apply the theme
def apply_nuke_theme(app):
    """Apply the Nuke-inspired dark theme to the application."""
    app.setStyleSheet(NUKE_DARK_STYLESHEET)
