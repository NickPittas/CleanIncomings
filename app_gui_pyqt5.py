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
    QSizePolicy  # Added QSizePolicy for widget sizing
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

    def _handle_scan_progress_update(self, progress_msg):
        # progress_msg: dict with at least 'stage', 'percent', 'details', 'status'
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

        self.file_operations_manager = FileOperationsManager(self)
        self.status_manager = StatusManager(self)
        self.settings_manager = SettingsManager(self)
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Core managers initialized.")

    def _initialize_services(self):
        """Initialize additional services."""
        self.media_player_utils = MediaPlayerUtils(self)  # Initialize media_player_utils

    def _connect_signals(self):
        """Connect signals from widgets to their handlers."""
        # Top control connections
        self.profile_combobox.currentTextChanged.connect(self._on_profile_changed)
        # Source folder entry textChanged is connected in _create_top_control_frame
        # Dest folder entry textChanged is connected in _create_top_control_frame
        self.refresh_btn.clicked.connect(self._on_scan_clicked)
        self.settings_btn.clicked.connect(self._open_settings_window)

    def _on_scan_clicked(self):
        # Start scan and show floating progress window
        self.progress_window.show_progress(stage="Initializing Scan...", percent=0, details="Preparing to scan...")
        self.refresh_btn.setEnabled(False)
        self.scan_manager.refresh_scan_data()

        # Theme is now hardcoded below; no combo boxes or handlers

        # Source tree connections
        if hasattr(self, 'source_tree'):
            self.source_tree.itemSelectionChanged.connect(self.tree_manager.on_source_tree_selection_changed)
            self.show_all_btn.clicked.connect(self.tree_manager.clear_source_folder_filter) # Show all by clearing filter

        # Preview tree connections
        if hasattr(self, 'preview_tree'):
            self.preview_tree.itemSelectionChanged.connect(self._on_tree_selection_change)
            self.preview_tree.itemDoubleClicked.connect(self._on_preview_item_double_clicked)
            # Header click for sorting
            self.preview_tree.header().sectionClicked.connect(self._on_preview_header_clicked)

        # Preview control connections
        self.sort_menu.currentTextChanged.connect(self._on_sort_change)
        self.sort_direction_btn.clicked.connect(self._toggle_sort_direction)
        self.filter_combo.currentTextChanged.connect(self._on_filter_change)
        self.select_all_seq_btn.clicked.connect(self._select_all_sequences)
        self.select_all_files_btn.clicked.connect(self._select_all_files)
        self.clear_selection_btn.clicked.connect(self._clear_selection)
        self.batch_edit_btn.clicked.connect(self._open_batch_edit_dialog)

        # File operation connections
        self.copy_selected_btn.clicked.connect(self.file_operations_manager.on_copy_selected_click)
        self.move_selected_btn.clicked.connect(self.file_operations_manager.on_move_selected_click)

        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"UI signals connected.")

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
        """Create the top control frame with compact, responsive layout."""
        # Create frame
        control_frame = QFrame()
        control_frame.setObjectName("control_panel_frame")  # For styling
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(5, 2, 5, 2)  # Minimal margins
        control_layout.setSpacing(2)  # Minimal spacing
        control_frame.setMinimumHeight(0)
        control_frame.setMaximumHeight(80)  # Cap the height for compactness
        
        # First row - Profile and main actions
        first_row = QHBoxLayout()

        # Profile selection
        profile_label = QLabel("Profile:")
        first_row.addWidget(profile_label)
        self.profile_combobox = QComboBox()
        self.profile_combobox.setMinimumWidth(150)
        self.profile_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        first_row.addWidget(self.profile_combobox)

        first_row.addSpacing(10)

        # Refresh button (Scan)
        self.refresh_btn = self.widget_factory.create_accent_button(
            text="Scan",
            icon_name="scan",
            tooltip="Scan source folder with selected profile",
            min_width=90
        )
        first_row.addWidget(self.refresh_btn)

        # Settings button
        self.settings_btn = self.widget_factory.create_accent_button(
            text="Settings",
            icon_name="settings",
            tooltip="Open application settings",
            min_width=90
        )
        first_row.addWidget(self.settings_btn)

        first_row.addStretch(1) # Pushes theme controls to the right

        
        control_layout.addLayout(first_row)
        
        # Second row - Folder selection
        second_row = QHBoxLayout()
        second_row.setSpacing(2)  # Minimal spacing
        
        # Source folder section
        source_label = QLabel("Source:")
        source_label.setMinimumWidth(50)
        second_row.addWidget(source_label)
        source_btn = self.widget_factory.create_compact_button("📁", tooltip="Select source folder")
        source_btn.clicked.connect(self._select_source_folder)
        second_row.addWidget(source_btn)
        
        self.source_folder_entry = QLineEdit()
        self.source_folder_entry.setPlaceholderText("Select or enter source folder path...")
        self.source_folder_entry.textChanged.connect(self.selected_source_folder.set)
        second_row.addWidget(self.source_folder_entry)
        
        # Destination folder section
        dest_label = QLabel("Dest:")
        dest_label.setMinimumWidth(40)
        second_row.addWidget(dest_label)
        
        dest_btn = self.widget_factory.create_compact_button("📁", tooltip="Select destination folder")
        dest_btn.clicked.connect(self._select_destination_folder)
        second_row.addWidget(dest_btn)
        
        self.dest_folder_entry = QLineEdit()
        self.dest_folder_entry.setPlaceholderText("Select or enter destination folder path...")
        self.dest_folder_entry.textChanged.connect(self.selected_destination_folder.set)
        second_row.addWidget(self.dest_folder_entry)
        
        control_layout.addLayout(second_row)
        
        parent_layout.addWidget(control_frame, stretch=0)  # No stretch for header

    def _create_main_layout(self, parent_layout):
        """Create the main layout with resizable panels using QSplitter."""
        # Main horizontal splitter
        self.main_horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # Create source tree section
        self._create_source_tree_section()
        
        # Create preview section  
        self._create_preview_section()
        
        # Set initial splitter sizes (400px for source tree, rest for preview)
        self.main_horizontal_splitter.setSizes([400, 1100])
        
        parent_layout.addWidget(self.main_horizontal_splitter, stretch=1)  # Main area gets all extra space

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
        """Create the preview section with enhanced layout and controls."""
        preview_group = self.widget_factory.create_group_box("Preview & Actions")
        preview_layout = preview_group.layout()  # Get existing layout
        if preview_layout is None:  # Should not happen
            preview_layout = QVBoxLayout()
            preview_group.setLayout(preview_layout)

        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Preview & Actions")
        header_label.setObjectName("header")
        header_layout.addWidget(header_label)
        
        header_layout.addSpacing(15)
        
        # Sort controls
        sort_label = QLabel("Sort:")
        header_layout.addWidget(sort_label)
        
        self.sort_menu = QComboBox()
        self.sort_menu.addItems(["Filename", "Task", "Asset", "Destination", "Type"])
        self.sort_menu.setMaximumWidth(100)
        self.sort_menu.currentTextChanged.connect(self._on_sort_change)
        header_layout.addWidget(self.sort_menu)
        
        # Sort direction button
        self.sort_direction_btn = QPushButton("↑")  # Up arrow
        self.sort_direction_btn.setMaximumWidth(30)
        self.sort_direction_btn.clicked.connect(self._toggle_sort_direction)
        header_layout.addWidget(self.sort_direction_btn)
        
        header_layout.addSpacing(15)
        
        # Filter controls
        filter_label = QLabel("Filter:")
        header_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Sequences", "Files"])
        self.filter_combo.setMaximumWidth(100)
        self.filter_combo.currentTextChanged.connect(self._on_filter_change)
        header_layout.addWidget(self.filter_combo)
        
        header_layout.addSpacing(15)
        
        # Selection buttons
        self.select_all_seq_btn = QPushButton("Select Sequences")
        self.select_all_seq_btn.setMaximumWidth(160)
        self.select_all_seq_btn.clicked.connect(self._select_all_sequences)
        header_layout.addWidget(self.select_all_seq_btn)

        self.select_all_files_btn = QPushButton("Select Files")
        self.select_all_files_btn.setMaximumWidth(130)
        self.select_all_files_btn.clicked.connect(self._select_all_files)
        header_layout.addWidget(self.select_all_files_btn)

        self.clear_selection_btn = QPushButton("Clear")
        self.clear_selection_btn.setMaximumWidth(90)
        self.clear_selection_btn.clicked.connect(self._clear_selection)
        header_layout.addWidget(self.clear_selection_btn)

        self.batch_edit_btn = QPushButton("Batch Edit")
        self.batch_edit_btn.setMaximumWidth(110)
        self.batch_edit_btn.clicked.connect(self._open_batch_edit_dialog)
        header_layout.addWidget(self.batch_edit_btn)
        
        header_layout.addStretch()
        
        preview_layout.addLayout(header_layout)
        
        # Selection stats
        self.selection_stats_label = QLabel("")
        self.selection_stats_label.setObjectName("small")
        preview_layout.addWidget(self.selection_stats_label)
          # Preview tree
        self.preview_tree = self.widget_factory.create_preview_tree()
        self.preview_tree.itemSelectionChanged.connect(self._on_tree_selection_change)
        preview_layout.addWidget(self.preview_tree)
        # --- Enhanced context menu for playback/debug ---
        from PyQt5.QtWidgets import QMenu, QAction, QMessageBox, QApplication
        from PyQt5.QtCore import Qt
        self.preview_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        import json
        def show_preview_context_menu(point):
            selected = self.preview_tree.selectedItems()
            if not selected:
                return
            item = selected[0]
            item_data = item.data(0, Qt.UserRole) or {}
            is_sequence = item_data.get('type', '').lower() == 'sequence' and item_data.get('sequence_info')
            menu = QMenu(self.preview_tree)
            action_vlc = QAction("Play with VLC", self.preview_tree)
            action_ffplay = QAction("Play with ffplay", self.preview_tree)
            action_show_data = QAction("Show Item Data", self.preview_tree)
            action_copy_path = QAction("Copy Path to Clipboard", self.preview_tree)
            action_print_console = QAction("Print Item to Console", self.preview_tree)
            menu.addAction(action_vlc)
            menu.addAction(action_ffplay)
            if is_sequence:
                action_show_seq = QAction("Show Sequence Frame List", self.preview_tree)
                menu.addAction(action_show_seq)
            menu.addSeparator()
            menu.addAction(action_show_data)
            menu.addAction(action_copy_path)
            menu.addAction(action_print_console)
            def play_vlc():
                # print("[DEBUG CONTEXT MENU] VLC item_data:", item_data)
                # print("[DEBUG CONTEXT MENU] VLC path:", item_data.get('path'))
                # print("[DEBUG CONTEXT MENU] VLC name:", item_data.get('name'))
                # Always use the ACTUAL source_path for playback (never destination fields)
                media_path = item_data.get('source_path') or item_data.get('path')
                # print("[DEBUG CONTEXT MENU] VLC media_path (to player):", media_path)
                if hasattr(self, 'play_with_vlc_handler'):
                    if is_sequence:
                        self.play_with_vlc_handler(item_data['sequence_info'])
                    else:
                        self.play_with_vlc_handler(media_path)
                elif hasattr(self, 'play_with_vlc'):
                    self.play_with_vlc(media_path)
                else:
                    QMessageBox.warning(self, "VLC Playback", "VLC playback handler is not implemented.")
            def play_ffplay():
                # print("[DEBUG CONTEXT MENU] FFPLAY item_data:", item_data)
                # print("[DEBUG CONTEXT MENU] FFPLAY path:", item_data.get('path'))
                # print("[DEBUG CONTEXT MENU] FFPLAY name:", item_data.get('name'))
                # Always use the ACTUAL source_path for playback (never destination fields)
                media_path = item_data.get('source_path') or item_data.get('path')
                # print("[DEBUG CONTEXT MENU] FFPLAY media_path (to player):", media_path)
                if hasattr(self, 'play_with_ffplay_handler'):
                    if is_sequence:
                        self.play_with_ffplay_handler(item_data['sequence_info'])
                    else:
                        self.play_with_ffplay_handler(media_path)
                else:
                    QMessageBox.warning(self, "ffplay Playback", "ffplay playback handler is not implemented.")
            action_vlc.triggered.connect(play_vlc)
            action_ffplay.triggered.connect(play_ffplay)

            def show_item_data():
                data_str = json.dumps(item_data, indent=2)
                QMessageBox.information(self, "Item Data", data_str)
            def copy_path():
                path = item_data.get('path', '')
            def show_sequence_frames():
                if is_sequence:
                    seq = item_data['sequence_info']
                    frames = seq.get('files', [])
                    frame_names = [f.get('filename', str(f)) if isinstance(f, dict) else str(f) for f in frames]
                    QMessageBox.information(self, "Sequence Frames", "\n".join(frame_names) if frame_names else "No frames found.")
            if is_sequence:
                action_show_seq.triggered.connect(show_sequence_frames)
            menu.exec_(self.preview_tree.viewport().mapToGlobal(point))
        self.preview_tree.customContextMenuRequested.connect(show_preview_context_menu)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.setObjectName("accent")
        self.copy_selected_btn.setEnabled(False)
        self.copy_selected_btn.clicked.connect(self.file_operations_manager.on_copy_selected_click)
        action_layout.addWidget(self.copy_selected_btn)
        
        self.move_selected_btn = QPushButton("Move Selected")
        self.move_selected_btn.setEnabled(False)
        self.move_selected_btn.clicked.connect(self.file_operations_manager.on_move_selected_click)
        action_layout.addWidget(self.move_selected_btn)
        
        action_layout.addStretch()
        
        preview_layout.addLayout(action_layout)
        

        
        self.main_horizontal_splitter.addWidget(preview_group)

    def _configure_profiles(self):
        """Configure profiles based on loaded data and saved settings."""
        if not self.normalizer:
            self.logger.error("Normalizer not initialized, cannot configure profiles.")
            return

        self.profile_names = self.normalizer.get_profile_names()
        self.profile_combobox.clear()
        if self.profile_names:
            self.profile_combobox.addItems(self.profile_names)
            
            # Attempt to restore the last selected profile from settings
            # Use the get_setting method of SettingsManager
            saved_profile = self.settings.get_setting("ui_state", "selected_profile", default="")
            
            if saved_profile and saved_profile in self.profile_names:
                self.profile_combobox.setCurrentText(saved_profile)
                self.selected_profile_name.set(saved_profile)
                self.normalizer.set_profile(saved_profile)
                # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Restored and applied profile: {saved_profile}")
            elif self.profile_names: # If no saved profile or saved is invalid, use the first available
                first_profile = self.profile_names[0]
                self.profile_combobox.setCurrentText(first_profile)
                self.selected_profile_name.set(first_profile)
                self.normalizer.set_profile(first_profile)
                # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"No valid saved profile, applied first available profile: {first_profile}")
        else:
            self.logger.warning("No profiles found to configure.")
            # Optionally, disable profile-dependent UI elements here

    def _load_initial_settings(self):
        """Load initial settings and apply them."""
        try:
            # Load all settings using the SettingsManager's method
            all_settings = self.settings.load_settings()
            
            # Now get the ui_state section from the loaded dictionary
            ui_state = all_settings.get("ui_state", {})
            
            if ui_state: # Check if ui_state dictionary is not empty
                self.settings.restore_ui_state(ui_state)
                # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"UI state restored from settings.")
        except Exception as e:
            self.logger.error(f"Error loading initial settings: {e}")

    def _handle_profile_change(self, profile_name: str):
        """Handle profile change from StringVar."""
        if hasattr(self, 'profile_combobox'):
            self.profile_combobox.setCurrentText(profile_name)

    def _on_profile_changed(self, profile_name: str):
        """Handle profile combobox change."""
        self.selected_profile_name.set(profile_name)
        print(f"Profile changed to: {profile_name}")

    def _on_theme_mode_change(self, mode: str):
        """Handle theme mode (appearance) change."""
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Theme mode changed to: {mode}")
        self.theme_manager.apply_theme(self.theme_manager.get_current_theme_name())

    def _on_color_theme_change(self, theme_name: str):
        """Handle color theme change."""
        # # self.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Color theme changed to: {theme_name}")
        self.theme_manager.apply_theme(theme_name)

    # Placeholder methods for the various UI actions
    def _select_source_folder(self):
        """Handle source folder selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.selected_source_folder.set(folder)
            self.source_folder_entry.setText(folder)
            self.status_label.setText(f"Source folder: {folder}")

    def _select_destination_folder(self):
        """Handle destination folder selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.selected_destination_folder.set(folder)
            self.dest_folder_entry.setText(folder)
            self.status_label.setText(f"Destination folder: {folder}")

    def _open_settings_window(self):
        """Open the settings window as a modal dialog, preventing multiple instances."""
        try:
            # Prevent multiple settings windows
            if hasattr(self, 'settings_window') and self.settings_window is not None:
                if self.settings_window.isVisible():
                    self.settings_window.raise_()
                    self.settings_window.activateWindow()
                    return
                else:
                    self.settings_window = None  # Reset if closed

            self.settings_window = SettingsWindow(
                parent=self,
                config_dir=self._config_dir_path,
                settings_manager=self.settings_manager
            )
            # Connect to settings changes
            self.settings_window.settings_changed.connect(self._on_settings_changed)
            # Show modally
            self.settings_window.exec_()
            # After closing, clear the reference
            self.settings_window = None
        except ImportError as e:
            QMessageBox.warning(
                self,
                "Settings Not Available",
                f"Settings window is not available:\n{e}"
            )

    def _on_settings_changed(self):
        """Handle settings changes from the settings window."""
        # Reload settings
        self.settings = self.settings_manager.load_settings()
        
        # Apply any immediate changes
        self.status_label.setText("Settings updated successfully.")
        print("Settings have been updated.")

    def _on_sort_change(self, sort_column_text: str):
        """Handle sort column change."""
        try:
            if hasattr(self, 'tree_manager') and hasattr(self.tree_manager, 'sort_preview_tree'):
                ascending = self.sort_direction_btn.text() == "↑"
                self.tree_manager.sort_preview_tree(sort_column_text, ascending)
                print(f"Sorting preview tree by: {sort_column_text}, Ascending: {ascending}")
            else:
                print("Warning: TreeManager or sort_preview_tree method not found.")
                pass
        except Exception as e:
            print(f"Error during sort: {e}")

    def _toggle_sort_direction(self):
        """Toggle sort direction and re-apply sort."""
        current_text = self.sort_direction_btn.text()
        new_text = "↓" if current_text == "↑" else "↑"
        self.sort_direction_btn.setText(new_text)
        
        # Re-apply sort with new direction
        current_sort_column = self.sort_menu.currentText()
        if current_sort_column: # Ensure a column is actually selected
            self._on_sort_change(current_sort_column)

    def _on_filter_change(self, filter_text: str):
        """Handle filter change in the preview tree."""
        try:
            if hasattr(self, 'tree_manager') and hasattr(self.tree_manager, 'filter_preview_tree'):
                self.tree_manager.filter_preview_tree(filter_text)
                print(f"Filtering preview tree by: {filter_text}")
            else:
                print("Warning: TreeManager or filter_preview_tree method not found.")
        except Exception as e:
            print(f"Error during filter: {e}")

    def _select_all_sequences(self):
        """Select all sequences in preview tree."""
        try:
            if hasattr(self, 'tree_manager') and hasattr(self.tree_manager, 'select_all_sequences_in_preview_tree'):
                self.tree_manager.select_all_sequences_in_preview_tree()
                print("Selected all sequences in preview tree.")
                self._on_tree_selection_change() # Update selection-dependent UI
            else:
                print("Warning: TreeManager or select_all_sequences_in_preview_tree method not found.")
        except Exception as e:
            print(f"Error during select all sequences: {e}")

    def _select_all_files(self):
        """Select all files in preview tree."""
        try:
            if hasattr(self, 'tree_manager') and hasattr(self.tree_manager, 'select_all_files_in_preview_tree'):
                self.tree_manager.select_all_files_in_preview_tree()
                print("Selected all files in preview tree.")
                self._on_tree_selection_change() # Update selection-dependent UI
            else:
                print("Warning: TreeManager or select_all_files_in_preview_tree method not found.")
        except Exception as e:
            print(f"Error during select all files: {e}")

    def _clear_selection(self):
        """Clear selection in preview tree."""
        self.preview_tree.clearSelection()
        self._on_tree_selection_change()

    def _open_batch_edit_dialog(self):
        """
        Open batch edit dialog for selected preview items. Prevents multiple dialogs from being open at once.
        Ensures only one signal connection per dialog instance. Adds debug prints for troubleshooting.
        """
        selected_preview_items_data = []
        if hasattr(self, 'preview_tree') and self.preview_tree.selectedItems():
            for item_widget in self.preview_tree.selectedItems():
                item_data = item_widget.data(0, Qt.UserRole)
                if item_data and isinstance(item_data, dict):
                    selected_preview_items_data.append(item_data)
                else:
                    print(f"Warning: Preview item {item_widget.text(0)} lacks expected data for batch editing.")

        if not selected_preview_items_data:
            QMessageBox.information(self, "No Items Selected", "Please select items in the preview tree to batch edit.")
            return

        if not self.normalizer:
            QMessageBox.critical(self, "Error", "Normalizer is not available. Cannot perform batch edit.")
            return

        # --- Prevent multiple dialogs ---
        if hasattr(self, 'batch_edit_dialog') and self.batch_edit_dialog is not None:
            if self.batch_edit_dialog.isVisible():
                self.batch_edit_dialog.raise_()
                self.batch_edit_dialog.activateWindow()
                return
            else:
                self.batch_edit_dialog = None  # Reset if closed

        try:
            self.batch_edit_dialog = BatchEditDialogPyQt5(
                parent=self,
                items=selected_preview_items_data,
                normalizer=self.normalizer
            )
            # Only connect the signal ONCE per dialog instance
            self.batch_edit_dialog.applied_batch_changes.connect(self._handle_applied_batch_changes)
            result = self.batch_edit_dialog.exec_()
            self.batch_edit_dialog = None  # Reset after dialog closes
            if result == QDialog.Accepted:
                print("Batch edit dialog accepted by user.")
            else:
                print("Batch edit dialog cancelled by user.")
        except Exception as e:
            QMessageBox.critical(self, "Batch Edit Error", f"Could not open batch edit dialog:\n{e}")
            print(f"Error opening batch edit dialog: {e}")

    def _handle_applied_batch_changes(self, changes: List[Dict[str, Any]]):
        """
        Handle the changes emitted from the BatchEditDialog. Adds debug prints and always forces a full preview tree refresh for UI sync.
        """
        print(f"[DEBUG] _handle_applied_batch_changes received: {changes}")
        if not changes:
            print("No changes were applied from batch edit dialog.")
            return

        selected_tree_items = self.preview_tree.selectedItems()
        if not selected_tree_items:
            print("No items selected in the preview tree to apply changes to.")
            return
            
        print(f"Applying batch changes to {len(selected_tree_items)} items: {changes}")
        
        updated_item_ids = []
        items_to_re_scan_for_sequences = False

        for tree_item_widget in selected_tree_items:
            original_item_data = tree_item_widget.data(0, Qt.UserRole)
            if not original_item_data or not isinstance(original_item_data, dict):
                print(f"Warning: Skipping item {tree_item_widget.text(0)} due to missing or invalid data.")
                continue

            item_id = original_item_data.get('id')
            if not item_id:
                print(f"Warning: Skipping item {tree_item_widget.text(0)} because it has no ID.")
                continue

            # Create a new dictionary for the modified data to avoid direct mutation issues
            # if the original_item_data is referenced elsewhere or needs to remain pristine until a full commit.
            modified_item_data = original_item_data.copy()
            
            change_applied_to_this_item = False
            for change_instruction in changes:
                field_to_change = change_instruction['field']
                new_value = change_instruction['value']
                
                if field_to_change in modified_item_data and modified_item_data[field_to_change] == new_value:
                    continue # No actual change for this field

                modified_item_data[field_to_change] = new_value
                change_applied_to_this_item = True
                
                # Check if a change might affect sequence grouping (e.g., shot_name, task_name, version_number, or filename itself)
                # This is a heuristic; your actual sequence detection logic might depend on more specific fields.
                if field_to_change in ["shot_name", "task_name", "version_number", "filename"]:
                    items_to_re_scan_for_sequences = True
            
            if change_applied_to_this_item:
                # Now, we need the TreeManager to handle this update.
                # The TreeManager should internally call the normalizer to get the new display name, path, etc.
                # and then update the tree widget item.
                if hasattr(self.tree_manager, 'update_item_properties_and_refresh_display'):
                    success = self.tree_manager.update_item_properties_and_refresh_display(item_id, modified_item_data)
                    if success:
                        updated_item_ids.append(item_id)
                        # Update the item_data_map as well, as TreeManager might not do it directly
                        # Or, ensure TreeManager does update its internal representation that feeds this map.
                        self.preview_tree_item_data_map[item_id] = modified_item_data 
                    else:
                        print(f"Warning: Failed to update item {item_id} via TreeManager.")
                else:
                    print("Error: TreeManager does not have 'update_item_properties_and_refresh_display' method.")
                    # Fallback or error message
                    QMessageBox.critical(self, "Update Error", "TreeManager is missing a required update method.")
                    return # Stop further processing if a critical component is missing
            
        if updated_item_ids:
            # Always force a full preview tree refresh for UI sync (even if not sequence-affecting)
            print("[DEBUG] Forcing full preview tree refresh after batch edit (UI sync).")
            self.tree_manager.rebuild_preview_tree_from_current_data(preserve_selection=True)
            QMessageBox.information(self, 
                                    "Batch Edit Applied", 
                                    f"{len(updated_item_ids)} items were updated based on your selections.")
            self.status_manager.set_status(f"Batch edit applied to {len(updated_item_ids)} items.")
            print(f"Batch edit successfully applied to items: {updated_item_ids}")
        elif changes: # If changes were requested but none were applied (e.g. all values were already set)
            QMessageBox.information(self, "No Effective Changes", "The selected batch changes did not result in any modifications to the items (values might have been the same).")
        # If no changes were requested initially, the dialog handles it.

        self._on_tree_selection_change() # Update UI based on potential changes (e.g., button states)

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
