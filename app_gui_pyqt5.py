# Main application GUI module - PyQt5 Version
print("--- EXECUTING PYQT5 APP_GUI.PY ---")
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QFrame, QLabel, QPushButton, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QStatusBar, QHeaderView,
    QCheckBox, QProgressBar, QMessageBox, QFileDialog, QDialog,
    QSizePolicy, QGroupBox  # Added QGroupBox for preview section
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap

# Import the Nuke-inspired theme
from python.gui_components.nuke_theme import apply_nuke_theme

# --- Start of VLC Path Configuration ---
def get_application_path():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, _MEIPASS is the temp dir
        return sys._MEIPASS
    # For development, __file__ is in CleanIncomings/ (app_gui.py is at the root of the project)
    return os.path.dirname(os.path.abspath(__file__)) 

application_path = get_application_path()
libvlc_dir = os.path.join(application_path, 'libvlc')

if os.path.isdir(libvlc_dir):
    if sys.platform.startswith('win32'):
        try:
            os.add_dll_directory(libvlc_dir)
        except AttributeError:
            # For older Python versions on Windows, os.add_dll_directory might not exist
            # In such cases, modifying PATH might be an alternative, but has broader implications.
            # For now, we'll rely on VLC_PLUGIN_PATH and hope libvlc.dll is found via standard search.
            print("Warning: os.add_dll_directory not available. VLC might not find core DLLs if not in PATH.")
            pass # Or consider adding to PATH as a fallback: os.environ["PATH"] = libvlc_dir + os.pathsep + os.environ["PATH"]

    plugin_path = os.path.join(libvlc_dir, 'plugins')
    if os.path.isdir(plugin_path):
        os.environ['VLC_PLUGIN_PATH'] = plugin_path
    else:
        print(f"Warning: VLC plugin path not found at {plugin_path}")
else:
    print(f"Warning: libvlc directory not found at {libvlc_dir}")
# --- End of VLC Path Configuration ---

# Try importing vlc after path configuration
try:
    import vlc  # Ensure this line is present and active
    _vlc_module_imported_successfully = True
except ImportError as e:
    print(f"Failed to import vlc: {e}. Embedded playback will be disabled.")
    vlc = None # Ensure vlc is defined, even if None
    _vlc_module_imported_successfully = False
except Exception as e:
    print(f"An unexpected error occurred during vlc import: {e}. Embedded playback will be disabled.")
    vlc = None
    _vlc_module_imported_successfully = False

# Import modular components (using PyQt5 compatible versions where available)
from python.gui_components.status_manager_pyqt5 import StatusManager
from python.gui_components.theme_manager_pyqt5 import ThemeManagerPyQt5
from python.gui_components.file_operations_manager import FileOperationsManager
from python.gui_components.tree_manager_pyqt5 import TreeManager
from python.gui_components.scan_manager import ScanManager
from python.gui_components.progress_window_pyqt5 import ProgressWindowPyQt5
from python.gui_components.settings_manager_pyqt5 import SettingsManager
from python.gui_components.widget_factory_pyqt5 import WidgetFactory
from python.gui_components.settings_window_pyqt5 import SettingsWindow
from python.gui_components.batch_edit_dialog_pyqt5 import BatchEditDialogPyQt5
from python.utils.media_player import MediaPlayerUtils

# Import the new collapsible image viewer
from python.gui_components.image_viewer_panel_pyqt5 import CollapsibleImageViewer

from python.gui_normalizer_adapter import GuiNormalizerAdapter

import logging
import re  # Added import re

# Path to script directory
_script_dir = os.path.dirname(os.path.abspath(__file__))


class StringVar(QObject):
    """Qt equivalent of tkinter StringVar for maintaining compatibility."""
    valueChanged = pyqtSignal(str)
    
    def __init__(self, value=""):
        super().__init__()
        self._value = value
    
    def get(self):
        return self._value
    
    def set(self, value):
        if self._value != value:
            self._value = value
            self.valueChanged.emit(value)


class CleanIncomingsApp(QMainWindow):
    def __init__(self, qt_app=None):
        super().__init__()
        self.qt_app = qt_app  # Store QApplication reference

        # Initialize logger first
        self._initialize_logger()

        self.vlc_module_available = _vlc_module_imported_successfully  # Set the flag

        # Initialize the map for storing full data associated with preview tree items
        self.preview_tree_item_data_map = {}
        
        # Initialize file transfer tracking
        self.active_transfers = {}  # Dictionary to store FileTransfer instances by transfer_id

        self.setWindowTitle("Clean Incomings - PyQt5 Edition")
        self.setGeometry(100, 100, 1500, 1000)  # x, y, width, height

        # UI configuration
        self.current_corner_radius = 6  # PyQt uses smaller radius
        self.accent_widgets = []  # List to store widgets that show accent color

        # Variables to store state (PyQt equivalents of tk.StringVar)
        self.selected_source_folder = StringVar()
        self.selected_destination_folder = StringVar()
        self.selected_profile_name = StringVar()
        self.ffplay_path_var = StringVar()  # Added for ffplay path
        self.profiles_data = {} 
        self.profile_names = []

        # Determine config directory path
        self._config_dir_path = self._determine_config_path()
        print(f"Using config directory: {self._config_dir_path}")

        # Initialize normalizer
        self.normalizer = self._initialize_normalizer()

        # Initialize modular components
        self._initialize_managers() # Renamed from _initialize_components for clarity
        self._initialize_services()

        # Floating progress window for scanning
        self.progress_window = ProgressWindowPyQt5(self)

        # Create widgets and setup UI
        self._create_ui()
        # Hardcode the theme to 'nuke_darkson' (or your preferred theme)
        self.theme_manager.current_theme_name = 'nuke_darkson'
        self.theme_manager.apply_theme('nuke_darkson')
        self._configure_profiles()
        self._load_initial_settings()

        # Connect signals after UI is created
        self._connect_signals()

        # self.logger.info(  # (Silenced for normal use. Re-enable for troubleshooting.)"CleanIncomingsApp initialized successfully.")

    def _initialize_logger(self):
        """Initialize a basic logger for the application."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG for development
        # Create a handler if not already configured (e.g., by a parent logger)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Logger initialized for CleanIncomingsApp.")

    def _determine_config_path(self) -> str:
        """Determine the configuration directory path."""
        config_dir_path = os.path.join(_script_dir, "config")
        if not os.path.isdir(config_dir_path):
            # Fallback if app_gui.py is in a subdirectory, try parent's 'config'
            parent_dir = os.path.dirname(_script_dir)
            fallback_config_path = os.path.join(parent_dir, "config")
            if os.path.isdir(fallback_config_path):
                config_dir_path = fallback_config_path
            else:                # Default to a 'config' folder in the current working directory as a last resort
                print(f"Warning: Config directory not found at {config_dir_path} or {fallback_config_path}. Attempting default.")
                config_dir_path = os.path.join(os.getcwd(), "config")
        return config_dir_path

    def _initialize_normalizer(self) -> Optional[GuiNormalizerAdapter]:
        """Initialize the normalizer adapter."""
        try:
            normalizer = GuiNormalizerAdapter(config_dir_path=self._config_dir_path)
            self.profile_names = normalizer.get_profile_names()
            if self.profile_names:
                self.selected_profile_name.set(self.profile_names[0])
            
            # Connect progress signal if the normalizer adapter supports it
            if hasattr(normalizer, 'progress_updated_signal'): # Assuming signal name from ISSUES_3.md context
                normalizer.progress_updated_signal.connect(self.update_progress_from_normalizer)
            elif hasattr(normalizer, 'progress_callback'): # Fallback for older name
                normalizer.progress_callback.connect(self.update_progress_from_normalizer)
            else:
                print("Warning: GuiNormalizerAdapter does not have 'progress_updated_signal' or 'progress_callback'. Progress updates may not work.")

            return normalizer
        except Exception as e: # Catch specific exception
            error_message = f"Failed to initialize Normalizer: {e}. Check config path and files."
            print(error_message)
            self.profile_names = []
            return None

    def _initialize_managers(self):
        """Initialize various manager classes for core functionalities."""
        self.theme_manager = ThemeManagerPyQt5(self.qt_app, logger=self.logger)
        self.widget_factory = WidgetFactory(self)
        self.tree_manager = TreeManager(self)
        self.scan_manager = ScanManager(self)
        # Connect scan progress updates to floating window
        if hasattr(self.scan_manager, 'scan_progress_signal'):
            self.scan_manager.scan_progress_signal.connect(self._handle_scan_progress_update)
        # If using a queue-based callback, patch _check_scan_queue or equivalent
        self._patch_scan_manager_progress_callback()

        self.file_operations_manager = FileOperationsManager(self)
        self.status_manager = StatusManager(self)
        self.settings_manager = SettingsManager(self)
        self.settings = self.settings_manager # Alias for convenience, after manager creation
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Core managers initialized.")

    def _patch_scan_manager_progress_callback(self):
        # Monkey-patch or wrap scan_manager's queue processing to update the floating window
        orig_check_scan_queue = getattr(self.scan_manager, '_check_scan_queue', None)
        if orig_check_scan_queue:
            def wrapped_check_scan_queue(*args, **kwargs):
                result = orig_check_scan_queue(*args, **kwargs)
                # After original processing, update floating window if progress info present
                if hasattr(self.scan_manager, 'last_progress_msg'):
                    msg = self.scan_manager.last_progress_msg
                    if isinstance(msg, dict):
                        self._handle_scan_progress_update(msg)
                return result
            self.scan_manager._check_scan_queue = wrapped_check_scan_queue

    # FIXED _handle_scan_progress_update should end after the progress handling:
    def _handle_scan_progress_update(self, progress_msg):
        """Handle scan progress updates and update floating window."""
        stage = progress_msg.get('stage', 'Scanning')
        percent = int(progress_msg.get('percent', 0))
        details = progress_msg.get('details', '')
        status = progress_msg.get('status', 'in_progress')
        
        if status == 'in_progress':
            self.progress_window.show_progress(stage=stage, percent=percent, details=details)
        elif status == 'completed':
            self.progress_window.show_progress(stage="Completed", percent=100, details=details)
            self.progress_window.close_progress()
            self.refresh_btn.setEnabled(True)
        elif status == 'error':
            self.progress_window.error(details)
            self.refresh_btn.setEnabled(True)
        else:
            self.progress_window.show_progress(stage=stage, percent=percent, details=details)
        # REMOVE THE DUPLICATED MANAGER INITIALIZATION CODE

    def _initialize_services(self):
        """Initialize additional services."""
        self.media_player_utils = MediaPlayerUtils(self)  # Initialize media_player_utils

    def _connect_signals(self):
        """Connect signals from widgets to their handlers."""
        # Top control connections
        self.profile_combobox.currentTextChanged.connect(self._on_profile_changed)
        self.refresh_btn.clicked.connect(self._on_scan_clicked)
        self.settings_btn.clicked.connect(self._open_settings_window)

        # Source tree connections
        if hasattr(self, 'source_tree'):
            self.source_tree.itemSelectionChanged.connect(self.tree_manager.on_source_tree_selection_changed)
            self.show_all_btn.clicked.connect(self.tree_manager.clear_source_folder_filter)

        # Preview tree connections
        if hasattr(self, 'preview_tree'):
            self.preview_tree.itemSelectionChanged.connect(self._on_tree_selection_change)
            self.preview_tree.itemDoubleClicked.connect(self._on_preview_item_double_clicked)
            self.preview_tree.header().sectionClicked.connect(self._on_preview_header_clicked)

        # Preview control connections
        self.sort_menu.currentTextChanged.connect(self._on_sort_change)
        self.sort_direction_btn.clicked.connect(self._toggle_sort_direction)
        self.filter_combo.currentTextChanged.connect(self._on_filter_change)
        self.select_all_seq_btn.clicked.connect(self._select_all_sequences)
        self.select_all_files_btn.clicked.connect(self._select_all_files)
        self.clear_selection_btn.clicked.connect(self._clear_selection)

        # Batch edit button - ensure clean connection
        try:
            self.batch_edit_btn.clicked.disconnect()
        except Exception:
            pass  # No existing connections
        self.batch_edit_btn.clicked.connect(self.on_batch_edit_btn_clicked)

        # File operation connections
        try:
            self.copy_selected_btn.clicked.disconnect()
        except Exception:
            pass
        self.copy_selected_btn.clicked.connect(self.file_operations_manager.on_copy_selected_click)
        try:
            self.move_selected_btn.clicked.disconnect()
        except Exception:
            pass
        self.move_selected_btn.clicked.connect(self.file_operations_manager.on_move_selected_click)



    def _on_scan_clicked(self):
        """Handle scan button click."""
        # Start scan and show floating progress window
        self.progress_window.show_progress(stage="Initializing Scan...", percent=0, details="Preparing to scan...")
        self.refresh_btn.setEnabled(False)
        self.scan_manager.refresh_scan_data()

    def update_progress_from_normalizer(self, progress_data: dict):
        """Update progress from normalizer. Expects a dict with 'value' and 'text'."""
        # This method should be connected to the normalizer's progress signal
        value = progress_data.get('value', 0)
        text = progress_data.get('text', '')
        # print(f"Normalizer progress: {value}% - {text}")
        if hasattr(self, 'status_manager') and hasattr(self.status_manager, 'update_scan_progress'):
            self.status_manager.update_scan_progress(value, text)
        elif hasattr(self, 'status_manager') and hasattr(self.status_manager, 'update_progress'): # older name
            self.status_manager.update_progress(value, text)
        else:
            print("Warning: StatusManager or its progress update method not found.")

    def get_geometry_as_string(self) -> Optional[str]:
        """Returns the window geometry as a 'WxH+X+Y' string."""
        try:
            geom = self.geometry()  # This is QMainWindow.geometry()
            if geom:
                return f"{geom.width()}x{geom.height()}+{geom.x()}+{geom.y()}"
            self.logger.warning("get_geometry_as_string: self.geometry() returned None")
            return None
        except Exception as e:
            self.logger.error(f"Error in get_geometry_as_string: {e}")
            return None

    def set_geometry_from_string(self, geom_string: Optional[str]):
        """Sets the window geometry from a 'WxH+X+Y' string."""
        if not geom_string:
            self.logger.warning("set_geometry_from_string: Received empty or None geom_string.")
            return
        
        match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geom_string)
        if match:
            try:
                width, height, x, y = map(int, match.groups())
                self.resize(width, height)  # QMainWindow.resize
                self.move(x, y)            # QMainWindow.move
                # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Geometry set from string: {geom_string}")
            except ValueError as e:
                self.logger.error(f"Error converting geometry parts to int from string '{geom_string}': {e}")
            except Exception as e:
                self.logger.error(f"Error applying geometry from string '{geom_string}': {e}")
        else:
            self.logger.warning(f"Invalid geometry string format: '{geom_string}'. Expected 'WIDTHxHEIGHT+X+Y'.")

    def _setup_compatibility_layer(self):
        """Set up compatibility methods for tkinter components."""
        # The geometry override has been removed. self.geometry is now the default QMainWindow.geometry().
        
        # Add after method compatibility for QTimer
        def after(delay_ms, callback):
            QTimer.singleShot(delay_ms, callback)
            
        self.after = after
        
        # Add compatibility for StringVar set method
        self.selected_profile_name.valueChanged.connect(
            lambda value: self._handle_profile_change(value)
        )

    def _create_ui(self):
        """Create the main UI layout."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Create top control frame
        self._create_top_control_frame(main_layout)
        
        # Create main resizable layout (horizontal splitter)
        self._create_main_layout(main_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Welcome to Clean Incomings! Select a profile and folders to begin.")
    
    def _create_top_control_frame(self, parent_layout):
        """Create the top control frame with folder selection and profile controls."""
        control_frame = QFrame()
        control_frame.setObjectName("control_frame")
        control_frame.setFixedHeight(120)
        control_layout = QVBoxLayout(control_frame)
        
        # First row: Folder selections
        folder_row = QHBoxLayout()
        
        # Source folder selection
        source_label = QLabel("Source:")
        source_label.setFixedWidth(60)
        folder_row.addWidget(source_label)
        
        self.source_folder_entry = QLineEdit()
        self.source_folder_entry.setPlaceholderText("Select source folder...")
        folder_row.addWidget(self.source_folder_entry)
        
        self.source_browse_btn = QPushButton("Browse")
        self.source_browse_btn.setFixedWidth(70)
        self.source_browse_btn.clicked.connect(self._select_source_folder)
        folder_row.addWidget(self.source_browse_btn)
        
        # Destination folder selection
        dest_label = QLabel("Destination:")
        dest_label.setFixedWidth(70)
        folder_row.addWidget(dest_label)
        
        self.dest_folder_entry = QLineEdit()
        self.dest_folder_entry.setPlaceholderText("Select destination folder...")
        folder_row.addWidget(self.dest_folder_entry)
        
        self.dest_browse_btn = QPushButton("Browse")
        self.dest_browse_btn.setFixedWidth(70)
        self.dest_browse_btn.clicked.connect(self._select_destination_folder)
        folder_row.addWidget(self.dest_browse_btn)
        
        control_layout.addLayout(folder_row)
        
        # Second row: Profile and scan
        profile_row = QHBoxLayout()
        
        profile_label = QLabel("Profile:")
        profile_label.setFixedWidth(60)
        profile_row.addWidget(profile_label)
        
        self.profile_combobox = QComboBox()
        self.profile_combobox.setMinimumWidth(150)
        profile_row.addWidget(self.profile_combobox)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.setFixedWidth(80)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        profile_row.addWidget(self.scan_btn)
        
        profile_row.addStretch()
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedWidth(80)
        self.settings_btn.clicked.connect(self._open_settings_window)
        profile_row.addWidget(self.settings_btn)
        
        control_layout.addLayout(profile_row)
        
        # Third row: Preview actions
        action_row = QHBoxLayout()
        
        # Selection controls
        self.select_all_sequences_btn = QPushButton("Select All Sequences")
        self.select_all_sequences_btn.clicked.connect(self._select_all_sequences)
        action_row.addWidget(self.select_all_sequences_btn)
        
        self.select_all_files_btn = QPushButton("Select All Files")
        self.select_all_files_btn.clicked.connect(self._select_all_files)
        action_row.addWidget(self.select_all_files_btn)
        
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self._clear_selection)
        action_row.addWidget(self.clear_selection_btn)
        
        action_row.addStretch()
        
        # Edit and viewer controls
        self.batch_edit_btn = QPushButton("Batch Edit")
        self.batch_edit_btn.setEnabled(False)
        self.batch_edit_btn.clicked.connect(self.on_batch_edit_btn_clicked)
        action_row.addWidget(self.batch_edit_btn)
        
        self.image_viewer_btn = QPushButton("Image Viewer")
        self.image_viewer_btn.setCheckable(True)
        self.image_viewer_btn.setChecked(False)
        self.image_viewer_btn.clicked.connect(self._toggle_image_viewer)
        action_row.addWidget(self.image_viewer_btn)
        
        control_layout.addLayout(action_row)
        
        parent_layout.addWidget(control_frame)

    def _create_main_layout(self, parent_layout):
        """Create the main layout with resizable panels using QSplitter."""
        # Main horizontal splitter (now only between source tree and preview panel)
        self.main_horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # Style the splitter for thinner handles
        self.main_horizontal_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #777;
            }
        """)
        
        # Create source tree section
        self._create_source_tree_section()
        
        # Create preview section (now includes image viewer)
        self._create_preview_section()
        
        # Set initial splitter sizes (400px for source tree, rest for preview)
        self.main_horizontal_splitter.setSizes([400, 1200])
        
        parent_layout.addWidget(self.main_horizontal_splitter)

    def _create_source_tree_section(self):
        """Create the source tree section with improved layout and controls."""
        source_tree_group = self.widget_factory.create_group_box("Source Folder Structure")
        source_tree_layout = source_tree_group.layout() # QVBoxLayout by default

        # Header for title and Show All button
        source_header_layout = QHBoxLayout()
        
        source_title_label = self.widget_factory.create_label("Source Structure", icon_name="folder_open", bold=True, font_size=11) # Changed icon
        source_header_layout.addWidget(source_title_label)
        source_header_layout.addStretch()
        
        self.show_all_btn = self.widget_factory.create_compact_button("🌲 Show All", icon_name="eye", tooltip="Clear folder filter and show all items in preview") # Changed icon and text
        source_header_layout.addWidget(self.show_all_btn)
        
        source_tree_layout.addLayout(source_header_layout)
        
        # Source tree
        self.source_tree = self.widget_factory.create_source_tree()
        source_tree_layout.addWidget(self.source_tree)
        
        self.main_horizontal_splitter.addWidget(source_tree_group)

    def _create_preview_section(self):
        """Create the preview section with tree, actions, and integrated image viewer."""
        preview_group = QGroupBox("Preview & Actions")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create horizontal splitter for preview tree and image viewer
        self.preview_splitter = QSplitter(Qt.Horizontal)
        self.preview_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #777;
            }
        """)
        
        # Left side: Preview tree and controls
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree controls row
        tree_controls_layout = QHBoxLayout()
        
        # Sort controls
        sort_label = QLabel("Sort by:")
        tree_controls_layout.addWidget(sort_label)
        
        self.sort_menu = QComboBox()
        self.sort_menu.addItems(["Filename", "Type", "Size", "Task", "Asset", "Version", "Resolution"])
        self.sort_menu.currentTextChanged.connect(self._on_sort_change)
        tree_controls_layout.addWidget(self.sort_menu)
        
        self.sort_direction_btn = QPushButton("↑")
        self.sort_direction_btn.setFixedSize(30, 25)
        self.sort_direction_btn.setToolTip("Toggle sort direction")
        self.sort_direction_btn.clicked.connect(self._toggle_sort_direction)
        tree_controls_layout.addWidget(self.sort_direction_btn)
        
        tree_controls_layout.addSpacing(20)
        
        # Filter controls
        filter_label = QLabel("Filter:")
        tree_controls_layout.addWidget(filter_label)
        
        self.filter_entry = QLineEdit()
        self.filter_entry.setPlaceholderText("Filter sequences...")
        self.filter_entry.textChanged.connect(self._on_filter_change)
        tree_controls_layout.addWidget(self.filter_entry)
        
        self.clear_filter_btn = QPushButton("Clear")
        self.clear_filter_btn.setFixedWidth(60)
        self.clear_filter_btn.clicked.connect(lambda: self.filter_entry.clear())
        tree_controls_layout.addWidget(self.clear_filter_btn)
        
        tree_controls_layout.addStretch()
        
        tree_layout.addLayout(tree_controls_layout)
        
        # Preview tree
        self.preview_tree = QTreeWidget()
        self.preview_tree.setHeaderLabels([
            "Filename", "Type", "Size", "Task", "Asset", "Version", "Resolution"
        ])
        self.preview_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.preview_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.preview_tree.customContextMenuRequested.connect(self._show_preview_context_menu)
        self.preview_tree.itemSelectionChanged.connect(self._on_tree_selection_change)
        self.preview_tree.itemDoubleClicked.connect(self._on_preview_item_double_clicked)
        self.preview_tree.headerClicked.connect(self._on_preview_header_clicked)
        
        # Configure header
        header = self.preview_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        tree_layout.addWidget(self.preview_tree)
        
        # Bottom status area
        bottom_layout = QHBoxLayout()
        
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.setEnabled(False)
        bottom_layout.addWidget(self.copy_selected_btn)
        
        self.move_selected_btn = QPushButton("Move Selected")
        self.move_selected_btn.setEnabled(False)
        bottom_layout.addWidget(self.move_selected_btn)
        
        bottom_layout.addStretch()
        
        self.selection_stats_label = QLabel("Selected: 0 items")
        bottom_layout.addWidget(self.selection_stats_label)
        
        tree_layout.addLayout(bottom_layout)
        
        # Add tree widget to splitter
        self.preview_splitter.addWidget(tree_widget)
        
        # Right side: Image viewer (initially hidden)
        self._create_image_viewer_panel()
        
        # Set initial splitter sizes (tree takes most space, viewer is hidden)
        self.preview_splitter.setSizes([800, 0])
        
        # Add splitter to main preview layout
        preview_layout.addWidget(self.preview_splitter)
        
        # Add to main layout
        self.main_horizontal_splitter.addWidget(preview_group)
    
    def _create_image_viewer_panel(self):
        """Create the image viewer panel within the preview section."""
        from python.gui_components.image_viewer_panel_pyqt5 import CollapsibleImageViewer
        
        # Create the image viewer panel (but without its own toggle button)
        self.image_viewer_panel = CollapsibleImageViewer(self, self)
        
        # We'll control visibility through our own button, so force it to expanded state
        # but start hidden via splitter sizes
        self.image_viewer_panel.is_expanded = True
        self.image_viewer_panel.content_frame.setVisible(True)
        self.image_viewer_panel.toggle_button.setVisible(False)  # Hide the internal toggle
        
        # Add to the preview splitter
        self.preview_splitter.addWidget(self.image_viewer_panel)
    
    def _toggle_image_viewer(self):
        """Toggle the image viewer panel visibility."""
        is_visible = self.image_viewer_btn.isChecked()
        
        current_sizes = self.preview_splitter.sizes()
        total_width = sum(current_sizes)
        
        if is_visible:
            # Show image viewer - allocate space for it
            tree_width = max(400, total_width - 450)  # Keep at least 400px for tree
            viewer_width = 450  # Preferred width for image viewer
            new_sizes = [tree_width, viewer_width]
            self.image_viewer_btn.setText("Hide Viewer")
        else:
            # Hide image viewer - give all space to tree
            new_sizes = [total_width, 0]
            self.image_viewer_btn.setText("Image Viewer")
        
        self.preview_splitter.setSizes(new_sizes)
        
        # If we have sequence data and viewer is being shown, update it
        if is_visible and hasattr(self, 'image_viewer_panel'):
            selected_items = self.preview_tree.selectedItems()
            if len(selected_items) == 1:
                item_data = selected_items[0].data(0, Qt.UserRole)
                if item_data and isinstance(item_data, dict):
                    # Check if it's a sequence
                    files = item_data.get('files', [])
                    if files and len(files) > 1:
                        self.image_viewer_panel.set_sequence_data(item_data)

    def _on_tree_selection_change(self):
        """Handle tree selection changes."""
        selected_items = self.preview_tree.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.copy_selected_btn.setEnabled(has_selection)
        self.move_selected_btn.setEnabled(has_selection)
        self.batch_edit_btn.setEnabled(has_selection)
        
        # Update selection stats
        stats_text = f"Selected: {len(selected_items)} items"
        self.selection_stats_label.setText(stats_text)
        
        # Update image viewer panel with selected sequence data
        if hasattr(self, 'image_viewer_panel') and self.image_viewer_btn.isChecked():
            if has_selection and len(selected_items) == 1:
                # Single item selected - show in image viewer if it's a sequence
                item_data = selected_items[0].data(0, Qt.UserRole)
                if item_data and isinstance(item_data, dict):
                    # Check if it's a sequence with multiple files
                    files = item_data.get('files', [])
                    if files and len(files) > 1:
                        self.image_viewer_panel.set_sequence_data(item_data)
                    else:
                        # Single file or no files - clear the viewer
                        self.image_viewer_panel.set_sequence_data(None)
                else:
                    self.image_viewer_panel.set_sequence_data(None)
            else:
                # Multiple items or no selection - clear the viewer
                self.image_viewer_panel.set_sequence_data(None)

    def _on_preview_item_double_clicked(self, item, column):
        """Handle double-click on a preview tree item."""
        # Placeholder: Show details or open file/sequence
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Double-clicked on preview item: {item.text(0)} (column {column})")
        QMessageBox.information(self, "Preview Item", f"Double-clicked: {item.text(0)}")

    def _on_preview_header_clicked(self, logical_index):
        """Handle header click for sorting columns in the preview tree."""
        # Placeholder: Just log the event for now
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Preview tree header clicked: column {logical_index}")
        # Optionally, trigger sort logic here

    def play_with_ffplay_handler(self, media_file):
        """
        Handle playback of a media file or sequence using ffplay via MediaPlayerUtils.
        Accepts either a file path (string) or a sequence metadata dictionary.
        """
        if not media_file:
            self.status_manager.add_log_message("No media file path provided for playback.", "ERROR")
            return False
        try:
            result = self.media_player_utils.play_with_ffplay_handler(media_file)
            if not result:
                self.status_manager.add_log_message("Playback failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.status_manager.add_log_message(f"Playback error: {e}", "ERROR")
            return False

    def play_with_vlc_handler(self, media_file):
        """
        Handle playback of a media file or sequence using VLC via MediaPlayerUtils (if available).
        Accepts either a file path (string) or a sequence metadata dictionary.
        """
        if not self.vlc_module_available:
            QMessageBox.warning(self, "VLC Playback", "VLC module is not available.")
            return False
        if not media_file:
            self.status_manager.add_log_message("No media file path provided for VLC playback.", "ERROR")
            return False
        try:
            if hasattr(self.media_player_utils, 'play_with_vlc_handler'):
                result = self.media_player_utils.play_with_vlc_handler(media_file)
            else:
                QMessageBox.warning(self, "VLC Playback", "VLC playback handler is not implemented in MediaPlayerUtils.")
                return False
            if not result:
                self.status_manager.add_log_message("VLC playback failed or was not launched.", "ERROR")
            return result
        except Exception as e:
            self.status_manager.add_log_message(f"VLC playback error: {e}", "ERROR")
            return False

if __name__ == '__main__':
    # Enable High DPI support for better display scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Apply the Nuke-inspired dark theme
    apply_nuke_theme(app)
    
    window = CleanIncomingsApp(qt_app=app)
    window.show()
    
    sys.exit(app.exec_())
