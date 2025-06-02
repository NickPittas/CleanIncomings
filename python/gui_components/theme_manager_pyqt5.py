"""
Theme Manager Module for PyQt5

Handles icon path resolution and provides a foundation for QSS-based theming
for the Clean Incomings GUI application.
"""
import os
from typing import Optional, Dict, Any
from .nuke_theme import NUKE_DARK_STYLESHEET  # Import the Nuke theme

class ThemeManagerPyQt5:
    """Manages themes, icon paths, and eventually QSS stylesheets for the PyQt5 GUI."""

    def __init__(self, qt_app: Any, logger=None):
        """
        Initialize the ThemeManagerPyQt5.

        Args:
            qt_app: Reference to the QApplication instance (for setStyleSheet).
            logger: Logger instance for logging (optional).
        """
        self.app = qt_app
        self.logger = logger
        try:
            self.project_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.base_icons_dir = os.path.join(self.project_root_dir, "icons")
        except NameError:
            if self.logger:
                self.logger.warning("__file__ not defined, attempting to use a hardcoded relative path for icons.")
            else:
                print("__file__ not defined, attempting to use a hardcoded relative path for icons.")
            self.project_root_dir = os.getcwd()
            self.base_icons_dir = os.path.join(self.project_root_dir, "icons")
            if self.logger:
                self.logger.info(f"ThemeManager using CWD-derived project root: {self.project_root_dir}")
            else:
                print(f"ThemeManager using CWD-derived project root: {self.project_root_dir}")

        self.current_theme_name: str = "nuke_dark"  # Always use Nuke theme by default
        if self.logger:
            # self.logger.info(f"ThemeManagerPyQt5 initialized. Icon base directory: {self.base_icons_dir}")  # (Silenced for normal use. Re-enable for troubleshooting.)
            pass
        else:
            print(f"ThemeManagerPyQt5 initialized. Icon base directory: {self.base_icons_dir}")

        # Define the mapping from logical icon names to actual filenames
        self.icon_mapping: Dict[str, str] = {
            'app_icon': 'NukeApp32.png',
            'folder': 'folder_closed_16.png',
            'folder_open': 'folder_open_16.png',
            'folder_closed': 'folder_closed_16.png',
            'file': 'file_16.png',
            'file_generic': 'file_16.png',
            'sequence': 'sequence_16.png',
            'file_image': 'image_16.png',
            'file_video': 'video_16.png',
            'file_audio': 'audio_16.png',
            'file_document': 'notebook.png',
            'file_archive': 'box_extract.png',
            'file_code': 'BlinkScript.png',
            'file_text': 'NukeDoc16.png',
            'settings': 'settings_16.png',
            'refresh': 'refresh_16.png',
            'task': 'task_16.png',
            'asset': 'asset_16.png',
            'arrow_up': 'arrow_up_16.png',
            'arrow_down': 'arrow_down_16.png',
            'arrow_right': 'arrow_right_16.png',
            'error': 'RotoPaint.png',
            'info': 'NukeDoc16.png',
            'warning': 'ColorWheel.png',
            'success': 'check.png',
            'plus': 'Add.png',
            'minus': 'Remove.png',
            'play': 'media_play.png',
            'pause': 'media_pause.png',
            'stop': 'media_stop.png',
            'next_frame': 'media_step_forward.png',
            'prev_frame': 'media_step_backward.png',
            'zoom_in': 'media_zoom_in.png',
            'zoom_out': 'media_zoom_out.png',
            'reset_zoom': 'media_reset_zoom.png',
            'scan_directory': 'magnify.png',
            'copy_files': 'files.png',
            'batch_edit': 'tools.png'
        }
        self._validate_icon_mappings()

        # Define paths for QSS files
        self.themes_dir = os.path.join(self.project_root_dir, "python", "themes")
        if self.logger:
            # self.logger.info(f"ThemeManagerPyQt5 QSS themes directory: {self.themes_dir}")  # (Silenced for normal use. Re-enable for troubleshooting.)
            pass
        else:
            print(f"ThemeManagerPyQt5 QSS themes directory: {self.themes_dir}")

    def _validate_icon_mappings(self):
        """Checks if mapped icon files exist and logs warnings for missing ones, falling back if needed."""
        fallback_icon = 'file_16.png'
        if not os.path.exists(os.path.join(self.base_icons_dir, fallback_icon)):
            if self.logger:
                self.logger.error(f"Critical: Fallback icon '{fallback_icon}' itself is missing from '{self.base_icons_dir}'. Icon system may fail.")
            else:
                print(f"Critical: Fallback icon '{fallback_icon}' itself is missing from '{self.base_icons_dir}'. Icon system may fail.")

        for name, filename in list(self.icon_mapping.items()):
            path = os.path.join(self.base_icons_dir, filename)
            if not os.path.exists(path):
                if self.logger:
                    self.logger.warning(
                        f"ThemeManager: Icon file '{filename}' for logical name '{name}' not found at '{path}'. "
                        f"Falling back to '{fallback_icon}' for this mapping."
                    )
                else:
                    print(
                        f"ThemeManager: Icon file '{filename}' for logical name '{name}' not found at '{path}'. "
                        f"Falling back to '{fallback_icon}' for this mapping."
                    )
                self.icon_mapping[name] = fallback_icon

    def get_icon_path(self, icon_name: str) -> Optional[str]:
        """
        Retrieves the full path to an icon file based on its logical name.

        Args:
            icon_name: The logical name of the icon (e.g., 'folder', 'sequence').

        Returns:
            The absolute path to the icon file if found, otherwise None.
        """
        if not icon_name:
            if self.logger:
                self.logger.warning("get_icon_path called with empty icon_name.")
            else:
                print("get_icon_path called with empty icon_name.")
            return None

        filename = self.icon_mapping.get(icon_name)

        if filename:
            icon_path = os.path.join(self.base_icons_dir, filename)
            if os.path.exists(icon_path):
                return icon_path
            else:
                if self.logger:
                    self.logger.error(f"ThemeManager: Icon file '{filename}' for '{icon_name}' mapped but NOT FOUND at '{icon_path}'. This indicates an issue post-validation.")
                else:
                    print(f"ThemeManager: Icon file '{filename}' for '{icon_name}' mapped but NOT FOUND at '{icon_path}'. This indicates an issue post-validation.")
                ultimate_fallback_path = os.path.join(self.base_icons_dir, 'file_16.png')
                if os.path.exists(ultimate_fallback_path):
                    return ultimate_fallback_path
                return None
        else:
            if self.logger:
                self.logger.warning(f"ThemeManager: No icon mapping found for logical name: '{icon_name}'")
            else:
                print(f"ThemeManager: No icon mapping found for logical name: '{icon_name}'")
            missing_icon_path = os.path.join(self.base_icons_dir, self.icon_mapping.get('file_generic', 'file_16.png'))
            if os.path.exists(missing_icon_path):
                return missing_icon_path
            return None

    def get_current_theme_stylesheet(self) -> str:
        """
        Loads and returns the QSS stylesheet for the current theme.
        Prioritizes specific hardcoded themes like 'nuke_dark'.
        """
        if self.current_theme_name == "nuke_dark":
            if self.logger:
                # self.logger.info("Using NUKE_DARK_STYLESHEET.")  # (Silenced for normal use. Re-enable for troubleshooting.)
                pass
            else:
                print("Using NUKE_DARK_STYLESHEET.")
            return NUKE_DARK_STYLESHEET

        qss_file_path = os.path.join(self.themes_dir, f"{self.current_theme_name}.qss")
        
        if not os.path.exists(qss_file_path):
            if self.logger:
                self.logger.warning(f"QSS file for theme '{self.current_theme_name}' not found at {qss_file_path}. Using default styles.")
            else:
                print(f"QSS file for theme '{self.current_theme_name}' not found at {qss_file_path}. Using default styles.")
            return """\
                QWidget { font-size: 9pt; }\
                QPushButton { padding: 4px; }\
                QMainWindow { background-color: #F0F0F0; } /* Default light background */\
            """
        
        try:
            with open(qss_file_path, "r") as f:
                stylesheet = f.read()
            if self.logger:
                self.logger.info(f"Successfully loaded QSS for theme '{self.current_theme_name}' from {qss_file_path}")
            else:
                print(f"Successfully loaded QSS for theme '{self.current_theme_name}' from {qss_file_path}")
            return stylesheet
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading QSS file {qss_file_path}: {e}", exc_info=True)
            else:
                print(f"Error loading QSS file {qss_file_path}: {e}")
            return """\
                QWidget { font-size: 9pt; color: red; } /* Error state style */\
                QMainWindow { background-color: #FFE0E0; } /* Light red background for error */\
            """

    def apply_theme(self, theme_name: str = "nuke_dark"):
        """
        Sets the current theme and applies its QSS stylesheet to the application.
        """
        if self.logger:
            # self.logger.info(f"Attempting to apply theme: {theme_name}")  # (Silenced for normal use. Re-enable for troubleshooting.)
            pass
        else:
            print(f"Attempting to apply theme: {theme_name}")
        
        if theme_name != "nuke_dark":
            if self.logger:
                # self.logger.warning(f"Only 'nuke_dark' theme is supported. Forcing 'nuke_dark'.")  # (Silenced for normal use. Re-enable for troubleshooting.)
                pass
            else:
                print("Only 'nuke_dark' theme is supported. Forcing 'nuke_dark'.")
            theme_name = "nuke_dark"
        self.current_theme_name = "nuke_dark"
        stylesheet = self.get_current_theme_stylesheet()
        if stylesheet:
            try:
                self.app.setStyleSheet(stylesheet)
                if self.logger:
                    # self.logger.info(f"Theme 'nuke_dark' applied successfully.")  # (Silenced for normal use. Re-enable for troubleshooting.)
                    pass
                else:
                    print(f"Theme 'nuke_dark' applied successfully.")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error applying stylesheet for theme 'nuke_dark': {e}", exc_info=True)
                else:
                    print(f"Error applying stylesheet for theme 'nuke_dark': {e}")
        else:
            if self.logger:
                self.logger.error(f"No stylesheet content returned for theme 'nuke_dark'. UI may not be styled correctly.")
            else:
                print(f"No stylesheet content returned for theme 'nuke_dark'. UI may not be styled correctly.")

    def get_available_appearance_modes(self):
        """Return a list of available appearance modes (e.g., Light, Dark)."""
        return ["Nuke Dark"]

    def get_current_appearance_mode(self):
        """Return the current appearance mode."""
        return "Nuke Dark"

    def get_available_themes(self):
        """Return a list of available color themes."""
        return ["nuke_dark"]

    def get_current_theme_name(self):
        """Return the current theme name."""
        return self.current_theme_name
