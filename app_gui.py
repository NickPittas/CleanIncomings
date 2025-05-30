# Main application GUI module - Modular Version
print("--- EXECUTING MODULAR APP_GUI.PY ---")
import tkinter as tk
import customtkinter as ctk
import json
import os
from typing import List, Dict, Any, Optional

# Import modular components
from python.gui_components.status_manager import StatusManager
from python.gui_components.theme_manager import ThemeManager
from python.gui_components.file_operations_manager import FileOperationsManager
from python.gui_components.tree_manager import TreeManager
from python.gui_components.widget_factory import WidgetFactory
from python.gui_components.scan_manager import ScanManager
from python.gui_components.settings_manager import SettingsManager

from python.gui_normalizer_adapter import GuiNormalizerAdapter

# Appearance and Theme Settings - Should be called before creating the CTk App instance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"

# Path to your custom theme file
_script_dir = os.path.dirname(os.path.abspath(__file__))
custom_theme_path = os.path.join(_script_dir, "themes", "custom_blue.json")

if os.path.exists(custom_theme_path):
    print(f"Loading custom theme from: {custom_theme_path}")
    ctk.set_default_color_theme(custom_theme_path)
else:
    print(f"Custom theme file not found at {custom_theme_path}. Using default blue theme.")
    ctk.set_default_color_theme("blue")  # Fallback to a default theme


class CleanIncomingsApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the map for storing full data associated with preview tree items
        self.preview_tree_item_data_map = {}
        
        # Initialize file transfer tracking
        self.active_transfers = {}  # Dictionary to store FileTransfer instances by transfer_id

        self.title("Clean Incomings - CustomTkinter Edition")
        self.geometry("1500x1000")  # Increased from 1300x850 to accommodate progress panel

        # UI configuration
        self.current_corner_radius = 10
        self.accent_widgets = []  # List to store widgets that show accent color

        # Variables to store state
        self.selected_source_folder = tk.StringVar()
        self.selected_destination_folder = tk.StringVar()
        self.selected_profile_name = tk.StringVar()
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
        self.widget_factory.create_widgets()
        self.theme_manager.setup_treeview_style()
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
            else:
                # Default to a 'config' folder in the current working directory as a last resort
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
        except Exception as e:
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
        self.widget_factory = WidgetFactory(self)
        self.scan_manager = ScanManager(self)
        self.settings_manager = SettingsManager(self)

        # Load settings first
        self.settings = self.settings_manager.load_settings()
        print(f"Loaded settings: {self.settings}")
        
        # Bind window close event to save settings
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _configure_profiles(self):
        """Configure the profile combobox based on loaded profiles."""
        if hasattr(self, 'profile_combobox'):
            if self.normalizer and self.profile_names:
                self.profile_combobox.configure(values=self.profile_names)
                if self.profile_names:
                    # Check if we have a saved profile selection
                    saved_profile = self.settings.get("ui_state", {}).get("selected_profile", "")
                    if saved_profile and saved_profile in self.profile_names:
                        default_profile_to_set = saved_profile
                    else:
                        default_profile_to_set = self.profile_names[0]
                    
                    self.profile_combobox.set(default_profile_to_set)
                    self.selected_profile_name.set(default_profile_to_set)
                    print(f"Set profile to: {default_profile_to_set}")
                else:
                    if hasattr(self, 'status_label'): 
                        self.status_label.configure(text="No profiles available in config.")
                    self.profile_combobox.configure(values=["No Profiles Available"], state="disabled")
                    self.profile_combobox.set("No Profiles Available")
            elif self.normalizer is None:
                if hasattr(self, 'status_label'): 
                    self.status_label.configure(text="Normalizer error. Check logs.")
                self.profile_combobox.configure(values=["Error: Profiles N/A"], state="disabled")
                self.profile_combobox.set("Error: Profiles N/A")
            else:
                if hasattr(self, 'status_label'): 
                    self.status_label.configure(text="No profiles found after init.")
                self.profile_combobox.configure(values=["No Profiles Loaded"], state="disabled")
                self.profile_combobox.set("No Profiles Loaded")
        else:
            print("[CRITICAL] CleanIncomingsApp.__init__: profile_combobox widget not found when trying to configure it.")
            if hasattr(self, 'status_label'): 
                self.status_label.configure(text="GUI Error: Profile dropdown missing.")

        # Restore UI state after widgets are created
        self.after(100, lambda: self.settings_manager.restore_ui_state(self.settings.get("ui_state", {})))

    def _load_profiles(self):
        """Load profiles from the profiles.json file (legacy method for compatibility)."""
        profiles_path = os.path.join(os.path.dirname(__file__), "config", "profiles.json")
        try:
            if not os.path.exists(profiles_path):
                self.status_label.configure(text=f"Error: profiles.json not found at {profiles_path}")
                self.profile_combobox.configure(values=[])
                return

            with open(profiles_path, 'r') as f:
                self.profiles_data = json.load(f)
            
            self.profile_names = list(self.profiles_data.keys())
            self.profile_combobox.configure(values=self.profile_names)
            if self.profile_names:
                self.selected_profile_name.set(self.profile_names[0])
                self.status_label.configure(text=f"Profiles loaded. Selected: {self.profile_names[0]}")
            else:
                self.status_label.configure(text="No profiles found in profiles.json.")
        except Exception as e:
            self.status_label.configure(text=f"Error loading profiles: {str(e)}")
            self.profile_combobox.configure(values=[])
            print(f"Error loading profiles: {e}")

    def _on_closing(self):
        """Handle application closing - save current state."""
        try:
            self.settings_manager.save_current_state()
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")
        finally:
            self.destroy()


if __name__ == '__main__':
    app = CleanIncomingsApp()
    app.mainloop() 