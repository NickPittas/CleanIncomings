# Main application GUI module - Modular Version
print("--- EXECUTING MODULAR APP_GUI.PY ---")
import tkinter as tk
import customtkinter as ctk
import json
import os
import sys  # Added sys
from pathlib import Path
from typing import List, Dict, Any, Optional

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

# Import modular components
from python.gui_components.status_manager import StatusManager
from python.gui_components.theme_manager import ThemeManager
from python.gui_components.file_operations_manager import FileOperationsManager
from python.gui_components.tree_manager import TreeManager
from python.gui_components.widget_factory import WidgetFactory
from python.gui_components.scan_manager import ScanManager
from python.gui_components.settings_manager import SettingsManager
from python.gui_components.vlc_player_window import VLCPlayerWindow  # Added import

from python.utils.media_player import MediaPlayerUtils  # Added import

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

        self.vlc_module_available = _vlc_module_imported_successfully  # Set the flag

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
        self.ffplay_path_var = tk.StringVar()  # Added for ffplay path
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
        self.media_player_utils = MediaPlayerUtils(self)  # Initialize media_player_utils
        self.VLCPlayerWindow = VLCPlayerWindow  # Assign the class to the app instance

        # Load settings first
        self.settings = self.settings_manager.load_settings()
        self.ffplay_path_var.set(self.settings.get("ui_state", {}).get("ffplay_path", ""))  # Initialize ffplay_path_var
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
            # Optionally, prompt user to set it or open settings
            # messagebox.showinfo("ffplay Not Configured", "Please set the path to ffplay in the Settings menu (Advanced tab).")
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
                selected_ids = self.preview_tree.selection()
                if selected_ids and hasattr(self, 'preview_tree_item_data_map'):
                    item_id = selected_ids[0]
                    selected_item_data = self.preview_tree_item_data_map.get(item_id)
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
        # This relies on the context menu providing the 'source_path' which might be a single file from a sequence.
        selected_ids = self.preview_tree.selection()
        if selected_ids and hasattr(self, 'preview_tree_item_data_map'):
            item_id = selected_ids[0]
            selected_item_data = self.preview_tree_item_data_map.get(item_id)
            
            if selected_item_data and selected_item_data.get('type') == 'Sequence':
                sequence_info = selected_item_data.get('sequence_info')
                if sequence_info:
                    # For MPV, often just the first file is enough, or a pattern.
                    # If sequence_info contains a list of files, use the first one.
                    # If it contains a pattern, that would be ideal, but our current structure might not provide it directly here.
                    files = sequence_info.get('files')
                    if files and isinstance(files, list) and len(files) > 0:
                        # Try using the first file of the sequence. MPV is good at detecting the rest.
                        first_file_of_sequence = os.path.join(sequence_info.get('directory', ''), files[0])
                        if os.path.exists(first_file_of_sequence):
                            path_to_play = first_file_of_sequence
                            print(f"[DEBUG_MPV_HANDLER] Identified sequence. Using first file: {path_to_play}")
                        else:
                            print(f"[DEBUG_MPV_HANDLER] First file of sequence not found: {first_file_of_sequence}. Using original path: {media_file_path}")
                    else:
                        # If no 'files' list, but it's a sequence, the media_file_path might already be a pattern or first file.
                        print(f"[DEBUG_MPV_HANDLER] Sequence detected, but no 'files' list in sequence_info. Using provided path: {media_file_path}")
                else:
                    print(f"[DEBUG_MPV_HANDLER] Item is a sequence, but no sequence_info. Using provided path: {media_file_path}")
        
        print(f"[DEBUG_MPV_HANDLER] Attempting to play with MPV: {path_to_play}")
        self.status_manager.add_log_message(f"Attempting to play with MPV: {os.path.basename(path_to_play)}", "INFO")
        
        try:
            process = self.media_player_utils.launch_mpv_subprocess(path_to_play)
            if process:
                print(f"[DEBUG_MPV_HANDLER] MPV subprocess launched successfully (PID: {process.pid}).")
                # Optionally, store the process or monitor it, but for now, just launch.
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