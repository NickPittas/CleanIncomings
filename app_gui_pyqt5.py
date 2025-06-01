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
    QCheckBox, QProgressBar, QMessageBox, QFileDialog
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
from python.gui_components.theme_manager import ThemeManager  
from python.gui_components.file_operations_manager import FileOperationsManager
from python.gui_components.tree_manager_pyqt5 import TreeManager
from python.gui_components.scan_manager import ScanManager
from python.gui_components.settings_manager_pyqt5 import SettingsManager
from python.gui_components.widget_factory_pyqt5 import WidgetFactory
# from python.gui_components.vlc_player_window import VLCPlayerWindow  # Skip for now

from python.utils.media_player import MediaPlayerUtils

from python.gui_normalizer_adapter import GuiNormalizerAdapter

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
    def __init__(self):
        super().__init__()

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
        self._initialize_components()

        # Create widgets and setup
        self._create_ui()
        self._configure_profiles()

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
            return normalizer
        except Exception as e: # Catch specific exception
            error_message = f"Failed to initialize Normalizer: {e}. Check config path and files."
            print(error_message)
            self.profile_names = []
            return None

    def _initialize_components(self):
        """Initialize all modular components."""
        self.status_manager = StatusManager(self)
        self.theme_manager = ThemeManager(self)
        self.file_operations_manager = FileOperationsManager(self)
        self.tree_manager = TreeManager(self)
        self.scan_manager = ScanManager(self)
        self.settings_manager = SettingsManager(self)
        self.widget_factory = WidgetFactory(self)  # Initialize widget factory
        self.media_player_utils = MediaPlayerUtils(self)  # Initialize media_player_utils
        
        # Skip VLC player window for now
        # self.VLCPlayerWindow = VLCPlayerWindow  # Assign the class to the app instance

        # Create compatibility layer for tkinter components
        self._setup_compatibility_layer()

        # Load settings first
        self.settings = self.settings_manager.load_settings()
        self.ffplay_path_var.set(self.settings.get("ui_state", {}).get("ffplay_path", ""))  # Initialize ffplay_path_var
        print(f"Loaded settings: {self.settings}")

    def _setup_compatibility_layer(self):
        """Set up compatibility methods for tkinter components."""
        # Add methods that original components might call but don't exist in PyQt5
        
        # Add tkinter-like geometry method for settings manager
        def geometry(geom_string=None):
            if geom_string is None:
                # Return current geometry
                geom = self.geometry()
                return f"{geom.width()}x{geom.height()}+{geom.x()}+{geom.y()}"
            else:
                # Parse and set geometry (format: "WIDTHxHEIGHT+X+Y")
                try:
                    size_part, pos_part = geom_string.split('+', 1)
                    width, height = map(int, size_part.split('x'))
                    x, y = map(int, pos_part.split('+'))
                    self.resize(width, height)
                    self.move(x, y)
                except:
                    print(f"Invalid geometry string: {geom_string}")
          # Bind the compatibility method
        self.geometry = geometry
        
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
        control_layout = QVBoxLayout(control_frame)  # Changed to vertical for better organization
        control_layout.setContentsMargins(10, 8, 10, 8)
        control_layout.setSpacing(8)
        
        # First row - Profile and main actions
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        
        # Profile Selection (more compact)
        profile_label = QLabel("Profile:")
        profile_label.setMinimumWidth(50)
        first_row.addWidget(profile_label)
        
        self.profile_combobox = QComboBox()
        self.profile_combobox.setMinimumWidth(180)
        self.profile_combobox.setMaximumWidth(220)
        first_row.addWidget(self.profile_combobox)
        
        first_row.addSpacing(10)
          # Compact action buttons
        self.refresh_btn = self.widget_factory.create_accent_button("🔄 Scan", "refresh", "Scan source folder for files", min_width=80, max_width=100)
        self.refresh_btn.clicked.connect(self.scan_manager.refresh_scan_data)
        first_row.addWidget(self.refresh_btn)
        
        settings_btn = self.widget_factory.create_accent_button("⚙️ Settings", "settings", tooltip="Open application settings", min_width=80, max_width=110)
        settings_btn.clicked.connect(self._open_settings_window)
        first_row.addWidget(settings_btn)
        
        first_row.addStretch()  # Push everything to the left
        
        control_layout.addLayout(first_row)
        
        # Second row - Folder selections with compact layout
        second_row = QHBoxLayout()
        second_row.setSpacing(10)
        
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
        
        parent_layout.addWidget(control_frame)

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
        
        parent_layout.addWidget(self.main_horizontal_splitter)

    def _create_source_tree_section(self):
        """Create the source tree section with improved layout and controls."""
        source_tree_group = self.widget_factory.create_group_box("Source Folder Structure")
        source_tree_layout = source_tree_group.layout()  # Get existing layout
        if source_tree_layout is None:  # Should not happen with current factory
            source_tree_layout = QVBoxLayout()
            source_tree_group.setLayout(source_tree_layout)

        # Header for title and Show All button
        source_header_layout = QHBoxLayout()
        
        source_title_label = self.widget_factory.create_label("Source Folder", icon_name="folder_closed", bold=True, font_size=12)
        source_header_layout.addWidget(source_title_label)
        source_header_layout.addStretch()
        
        self.show_all_btn = self.widget_factory.create_compact_button("Show All", icon_name="info", tooltip="Show all sequences in the source tree") # Changed to create_compact_button
        self.show_all_btn.clicked.connect(self._show_all_sequences)
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
        select_all_seq_btn = QPushButton("Select Sequences")
        select_all_seq_btn.setMaximumWidth(160)
        select_all_seq_btn.clicked.connect(self._select_all_sequences)
        header_layout.addWidget(select_all_seq_btn)
        
        select_all_files_btn = QPushButton("Select Files")
        select_all_files_btn.setMaximumWidth(130)
        select_all_files_btn.clicked.connect(self._select_all_files)
        header_layout.addWidget(select_all_files_btn)
        
        clear_selection_btn = QPushButton("Clear")
        clear_selection_btn.setMaximumWidth(90)
        clear_selection_btn.clicked.connect(self._clear_selection)
        header_layout.addWidget(clear_selection_btn)
        
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
        
        # Info display placeholder
        info_frame = QFrame()
        info_frame.setFixedHeight(60)
        info_layout = QHBoxLayout(info_frame)
        info_label = QLabel("Details of selected item - Coming Soon!")
        info_layout.addWidget(info_label)
        preview_layout.addWidget(info_frame)
        
        self.main_horizontal_splitter.addWidget(preview_group)

    def _configure_profiles(self):
        """Configure the profile combobox based on loaded profiles."""
        if self.normalizer and self.profile_names:
            self.profile_combobox.clear()
            self.profile_combobox.addItems(self.profile_names)
            if self.profile_names:
                # Check if we have a saved profile selection
                saved_profile = self.settings.get("ui_state", {}).get("selected_profile", "")
                if saved_profile and saved_profile in self.profile_names:
                    default_profile_to_set = saved_profile
                else:
                    default_profile_to_set = self.profile_names[0]
                
                self.profile_combobox.setCurrentText(default_profile_to_set)
                self.selected_profile_name.set(default_profile_to_set)
                print(f"Set profile to: {default_profile_to_set}")
            else:
                if hasattr(self, 'status_label'): 
                    self.status_label.setText("No profiles available in config.")
                self.profile_combobox.addItem("No Profiles Available")
                self.profile_combobox.setEnabled(False)
        elif self.normalizer is None:
            if hasattr(self, 'status_label'): 
                self.status_label.setText("Normalizer error. Check logs.")
            self.profile_combobox.addItem("Error: Profiles N/A")
            self.profile_combobox.setEnabled(False)
        else:
            if hasattr(self, 'status_label'): 
                self.status_label.setText("No profiles found after init.")
            self.profile_combobox.addItem("No Profiles Loaded")
            self.profile_combobox.setEnabled(False)

        # Connect profile combobox signal
        self.profile_combobox.currentTextChanged.connect(self._on_profile_changed)

        # Restore UI state after widgets are created
        QTimer.singleShot(100, lambda: self.settings_manager.restore_ui_state(self.settings.get("ui_state", {})))

    def _handle_profile_change(self, profile_name: str):
        """Handle profile change from StringVar."""
        if hasattr(self, 'profile_combobox'):
            self.profile_combobox.setCurrentText(profile_name)

    def _on_profile_changed(self, profile_name: str):
        """Handle profile combobox change."""
        self.selected_profile_name.set(profile_name)
        print(f"Profile changed to: {profile_name}")

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
        """Open settings window."""
        try:
            from python.gui_components.settings_window_pyqt5 import SettingsWindow
            
            settings_window = SettingsWindow(
                parent=self,
                config_dir=self._config_dir_path,
                settings_manager=self.settings_manager
            )
            
            # Connect to settings changes
            settings_window.settings_changed.connect(self._on_settings_changed)
            
            settings_window.show()
            
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

    def _show_all_sequences(self):
        """Show all sequences in source tree."""
        # Placeholder - will be connected to scan manager
        print("Show all sequences clicked")

    def _on_sort_change(self, value):
        """Handle sort column change."""
        print(f"Sort changed to: {value}")

    def _toggle_sort_direction(self):
        """Toggle sort direction."""
        current_text = self.sort_direction_btn.text()
        new_text = "↓" if current_text == "↑" else "↑"
        self.sort_direction_btn.setText(new_text)

    def _on_filter_change(self, value):
        """Handle filter change."""
        print(f"Filter changed to: {value}")

    def _select_all_sequences(self):
        """Select all sequences in preview tree."""
        print("Select all sequences clicked")

    def _select_all_files(self):
        """Select all files in preview tree."""
        print("Select all files clicked")

    def _clear_selection(self):
        """Clear selection in preview tree."""
        self.preview_tree.clearSelection()
        self._on_tree_selection_change()

    def _open_batch_edit_dialog(self):
        """Open batch edit dialog."""
        QMessageBox.information(self, "Batch Edit", "Batch edit dialog will be implemented in PyQt5")

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

    # Media player methods - preserve original functionality
    def play_with_ffplay_handler(self, media_file_path: Optional[str]):
        """Handles the call to play a media file with ffplay."""
        print(f"[DEBUG_FFPLAY_HANDLER] Called with media_file_path: {media_file_path}")
        
        if not media_file_path:
            print(f"[DEBUG_FFPLAY_HANDLER] No media file path provided")
            self.status_manager.add_log_message("No media file path provided for playback.", "ERROR")
            return

        ffplay_exe_path = self.ffplay_path_var.get()
        print(f"[DEBUG_FFPLAY_HANDLER] ffplay_exe_path from settings: {ffplay_exe_path}")
        
        if not ffplay_exe_path:
            print(f"[DEBUG_FFPLAY_HANDLER] ffplay path is not configured")
            self.status_manager.add_log_message("ffplay path is not configured in settings.", "ERROR")
            return
        
        # Check if the path is for an existing file or a sequence pattern
        if os.path.isfile(media_file_path):
            # Regular file
            print(f"[DEBUG_FFPLAY_HANDLER] Regular file detected")
            print(f"[DEBUG_FFPLAY_HANDLER] Calling media_player_utils.play_with_ffplay({ffplay_exe_path}, {media_file_path})")
            self.status_manager.add_log_message(f"Attempting to play: {media_file_path} with ffplay at {ffplay_exe_path}", "INFO")
            
            try:
                result = self.media_player_utils.play_with_ffplay(ffplay_exe_path, media_file_path)
                print(f"[DEBUG_FFPLAY_HANDLER] play_with_ffplay returned: {result}")
                return result
            except Exception as e:
                print(f"[DEBUG_FFPLAY_HANDLER] Exception in play_with_ffplay: {e}")
                import traceback
                traceback.print_exc()
                self.status_manager.add_log_message(f"Error launching ffplay: {e}", "ERROR")
                return False
        else:
            # Likely a sequence or doesn't exist
            print(f"[DEBUG_FFPLAY_HANDLER] Sequence or non-existent file detected: {media_file_path}")
            
            # Try to find selected item ID to get sequence info if available
            try:
                selected_items = self.preview_tree.selectedItems()
                if selected_items and hasattr(self, 'preview_tree_item_data_map'):
                    # In PyQt5, we'll need to get the item ID differently
                    # For now, use a simple approach
                    selected_item_data = None
                    print(f"[DEBUG_FFPLAY_HANDLER] Selected item data: {selected_item_data}")
                    
                    # Check if it's a sequence with sequence_info
                    if selected_item_data and selected_item_data.get('type') == 'Sequence' and selected_item_data.get('sequence_info'):
                        seq_info = selected_item_data.get('sequence_info')
                        print(f"[DEBUG_FFPLAY_HANDLER] Found sequence info: {seq_info}")
                        
                        # Prepare rich sequence data for the player
                        sequence_data = {
                            'base_name': seq_info.get('base_name', ''),
                            'directory': os.path.dirname(media_file_path),
                            'files': seq_info.get('files', []),
                            'frame_numbers': seq_info.get('frame_numbers', []),
                            'frame_range': seq_info.get('range', ''),
                            'frame_count': len(seq_info.get('files', [])),
                            'suffix': seq_info.get('suffix', '')
                        }
                        
                        self.status_manager.add_log_message(f"Attempting to play sequence: {media_file_path}", "INFO")
                        try:
                            result = self.media_player_utils.launch_ffplay_from_sequence_data(
                                sequence_data,
                                frame_rate=24,
                                window_size=(800, 600),
                                enable_loop=True,
                                ffplay_executable=ffplay_exe_path
                            )
                            print(f"[DEBUG_FFPLAY_HANDLER] launch_ffplay_from_sequence_data returned: {result}")
                            return result is not None
                        except Exception as e:
                            print(f"[DEBUG_FFPLAY_HANDLER] Exception in launch_ffplay_from_sequence_data: {e}")
                            import traceback
                            traceback.print_exc()
                            # Fall back to simpler method if rich sequence data fails
            except Exception as e:
                print(f"[DEBUG_FFPLAY_HANDLER] Error trying to get sequence info: {e}")
            
            # Fallback: try generic sequence detection
            self.status_manager.add_log_message(f"Attempting to play sequence: {media_file_path} with ffplay", "INFO")
            try:
                result = self.media_player_utils.play_sequence(
                    media_file_path, 
                    frame_rate=24, 
                    window_size=(800, 600),
                    enable_loop=True,
                    ffplay_executable=ffplay_exe_path
                )
                print(f"[DEBUG_FFPLAY_HANDLER] play_sequence returned: {result}")
                return result is not None
            except Exception as e:
                print(f"[DEBUG_FFPLAY_HANDLER] Exception in play_sequence: {e}")
                import traceback
                traceback.print_exc()
                self.status_manager.add_log_message(f"Error launching ffplay for sequence: {e}", "ERROR")
                return False

    def play_with_mpv_handler(self, media_file_path: Optional[str]):
        """Handles the call to play a media file or sequence with MPV via launch_mpv_subprocess."""
        print(f"[DEBUG_MPV_HANDLER] Called with media_file_path: {media_file_path}")
        
        if not media_file_path:
            print(f"[DEBUG_MPV_HANDLER] No media file path provided for MPV.")
            self.status_manager.add_log_message("No media file path provided for MPV playback.", "ERROR")
            return False

        if not hasattr(self, 'media_player_utils') or not hasattr(self.media_player_utils, 'launch_mpv_subprocess'):
            print(f"[DEBUG_MPV_HANDLER] MediaPlayerUtils or launch_mpv_subprocess not available.")
            self.status_manager.add_log_message("MPV playback utility is not available.", "ERROR")
            return False

        path_to_play = media_file_path # Default to the provided path

        # Check if it's a sequence by looking at the selected item's data
        selected_items = self.preview_tree.selectedItems()
        if selected_items and hasattr(self, 'preview_tree_item_data_map'):
            # In PyQt5, we'll need to implement this differently
            # For now, use the provided path directly
            pass
        
        print(f"[DEBUG_MPV_HANDLER] Attempting to play with MPV: {path_to_play}")
        self.status_manager.add_log_message(f"Attempting to play with MPV: {os.path.basename(path_to_play)}", "INFO")
        
        try:
            process = self.media_player_utils.launch_mpv_subprocess(path_to_play)
            if process:
                print(f"[DEBUG_MPV_HANDLER] MPV subprocess launched successfully (PID: {process.pid}).")
                return True # Indicates successful launch attempt
            else:
                print(f"[DEBUG_MPV_HANDLER] Failed to launch MPV subprocess (process is None).")
                self.status_manager.add_log_message(f"Failed to launch MPV for: {os.path.basename(path_to_play)}", "ERROR")
                return False
        except Exception as e:
            print(f"[DEBUG_MPV_HANDLER] Exception during MPV launch: {e}")
            import traceback
            traceback.print_exc()
            self.status_manager.add_log_message(f"Error launching MPV: {e}", "ERROR")
            return False

    def closeEvent(self, event):
        """Handle application closing - save current state."""
        try:
            self.settings_manager.save_current_state()
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")
        finally:
            event.accept()


if __name__ == '__main__':
    # Enable High DPI support for better display scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Apply the Nuke-inspired dark theme
    apply_nuke_theme(app)
    
    window = CleanIncomingsApp()
    window.show()
    
    sys.exit(app.exec_())
