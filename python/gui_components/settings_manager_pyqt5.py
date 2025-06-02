"""
Settings Manager Module - PyQt5 Compatible

Handles UI state persistence and restoration for the Clean Incomings application.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtCore import QTimer


class SettingsManager:
    """Manages application settings and UI state persistence."""
    
    def __init__(self, app_instance):
        """
        Initialize the SettingsManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.settings_file = Path(__file__).parent.parent.parent / "user_settings.json"
        self.default_settings = {
            "ui_state": {
                "window_geometry": "1500x1000",
                "window_position": None,
                "log_panel_collapsed": True,
                "horizontal_pane_position": 400,  # Source tree width
                "vertical_pane_positions": [600, 800],  # Main content area, then log area
                "source_folder": "",
                "destination_folder": "", 
                "selected_profile": "",
                "appearance_mode": "System",
                "color_theme": "blue",
                "scan_threads": 8,  # Balanced for 10GbE scanning
                "copy_threads": 16,  # Balanced for 10GbE copying - good performance without overload
                "ffplay_path": "",  # Path to ffplay executable
                "scan_on_startup": False  # Added scan_on_startup to ui_state defaults
            },
            "performance": {
                "enable_multithreading": True,
                "max_concurrent_scans": 8,
                "max_concurrent_copies": 16  # Balanced for good 10GbE performance
            }
        }

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, return defaults if file doesn't exist."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_settings = self._merge_with_defaults(loaded_settings)
                print(f"Loaded settings from {self.settings_file}")
                return merged_settings
            else:
                print(f"Settings file not found, using defaults")
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}, using defaults")
            return self.default_settings.copy()

    def _merge_with_defaults(self, loaded_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to ensure all keys exist."""
        merged = self.default_settings.copy()
        
        for section_key, section_value in loaded_settings.items():
            if section_key in merged:
                if isinstance(section_value, dict) and isinstance(merged[section_key], dict):
                    merged[section_key].update(section_value)
                else:
                    merged[section_key] = section_value
            else:
                merged[section_key] = section_value
        
        return merged

    def save_settings(self, settings: Dict[str, Any]):
        """Save settings to file."""
        try:
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"Settings saved to {self.settings_file}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def save_current_state(self):
        """Save current UI state."""
        try:
            current_settings = self.load_settings()  # Get existing settings first
            
            # Update UI state section
            ui_state = current_settings.setdefault("ui_state", {})
            
            # Save window geometry using the new method from app_gui_pyqt5
            if hasattr(self.app, 'get_geometry_as_string'):
                ui_state["window_geometry_full"] = self.app.get_geometry_as_string()
                # Clean up old keys if they exist
                ui_state.pop("window_geometry", None)
                ui_state.pop("window_position", None)
            else:
                # Fallback or log warning if method is not found (should not happen with correct app instance)
                self.app.logger.warning("save_current_state: self.app.get_geometry_as_string not found.")
                # Attempt to save using old method as a very basic fallback
                geometry = self.app.geometry()
                ui_state["window_geometry"] = f"{geometry.width()}x{geometry.height()}"
                ui_state["window_position"] = f"+{geometry.x()}+{geometry.y()}"
            
            # Save folder selections
            ui_state["source_folder"] = self.app.selected_source_folder.get()
            ui_state["destination_folder"] = self.app.selected_destination_folder.get()
            
            # Save profile selection
            if hasattr(self.app, 'profile_combobox'):
                ui_state["selected_profile"] = self.app.profile_combobox.currentText()
            
            # Save log panel state
            ui_state["log_panel_collapsed"] = getattr(self.app, 'log_panel_collapsed', True)
            
            # Save thread settings
            ui_state["scan_threads"] = getattr(self.app, 'current_scan_threads', 8)
            ui_state["copy_threads"] = getattr(self.app, 'current_copy_threads', 16)
            
            # Save ffplay path
            if hasattr(self.app, 'ffplay_path_var'):
                ui_state["ffplay_path"] = self.app.ffplay_path_var.get()
            
            # Save splitter positions (PyQt5)
            if hasattr(self.app, 'main_horizontal_splitter'):
                ui_state["horizontal_pane_position"] = self.app.main_horizontal_splitter.sizes()[0]
            
            self.save_settings(current_settings)
            
        except Exception as e:
            print(f"Error saving current state: {e}")

    def restore_ui_state(self, ui_state: Dict[str, Any]):
        """Restore UI state to the application (PyQt5 compatible)."""
        try:
            # Restore window geometry and position using the new method from app_gui_pyqt5
            if ui_state.get("window_geometry_full") and hasattr(self.app, 'set_geometry_from_string'):
                self.app.set_geometry_from_string(ui_state.get("window_geometry_full"))
            elif ui_state.get("window_geometry"): # Fallback to old method if new key not present
                self.app.logger.info("Restoring geometry using old keys (window_geometry, window_position).")
                geometry_str = ui_state["window_geometry"]
                position_str = ui_state.get("window_position")
                full_geom_str = f"{geometry_str}{position_str if position_str else '+0+0'}" # Construct full string
                if hasattr(self.app, 'set_geometry_from_string'):
                    self.app.set_geometry_from_string(full_geom_str)
                else: # Absolute fallback if set_geometry_from_string is also missing
                    self.app.logger.warning("restore_ui_state: self.app.set_geometry_from_string not found, attempting direct resize/move.")
                    try:
                        width, height = map(int, geometry_str.split('x'))
                        self.app.resize(width, height)
                        if position_str:
                            parts = position_str.replace('+', ' ').split()
                            if len(parts) >= 2:
                                x_pos = int(parts[0])
                                y_pos = int(parts[1])
                                self.app.move(x_pos, y_pos)
                    except Exception as e_fallback:
                        self.app.logger.error(f"Error in fallback geometry restoration: {e_fallback}")
            else:
                self.app.logger.info("No window_geometry_full or window_geometry found in ui_state for restoration.")

            # Restore folder selections
            if ui_state.get("source_folder"):
                self.app.selected_source_folder.set(ui_state["source_folder"])
                if hasattr(self.app, 'source_folder_entry'):
                    self.app.source_folder_entry.setText(ui_state["source_folder"])
            
            if ui_state.get("destination_folder"):
                self.app.selected_destination_folder.set(ui_state["destination_folder"])
                if hasattr(self.app, 'dest_folder_entry'):
                    self.app.dest_folder_entry.setText(ui_state["destination_folder"])
            
            # Restore profile selection
            if ui_state.get("selected_profile") and hasattr(self.app, 'profile_combobox'):
                try:
                    # For PyQt5, use setCurrentText instead of set
                    profile_name = ui_state["selected_profile"]
                    # Defer profile combobox setting until widget is fully created
                    QTimer.singleShot(100, lambda: self._restore_profile_selection(profile_name))
                except Exception as e:
                    print(f"Error setting up profile restoration: {e}")

            # Restore log panel state
            self.app.log_panel_collapsed = ui_state.get("log_panel_collapsed", True)  # Default to True (collapsed)
            
            # Restore thread settings
            self.app.current_scan_threads = ui_state.get("scan_threads", 8)
            self.app.current_copy_threads = ui_state.get("copy_threads", 16)
            
            # Restore ffplay path
            if hasattr(self.app, 'ffplay_path_var'):  # Check if the variable exists on app instance
                self.app.ffplay_path_var.set(ui_state.get("ffplay_path", ""))

            # Apply thread settings to components after restoration
            QTimer.singleShot(100, self._apply_thread_settings)
            
            # Apply log panel state after widgets are created with appropriate delay
            QTimer.singleShot(500, lambda: self._restore_log_panel_state(ui_state.get("log_panel_collapsed", True)))

            # Schedule pane position restoration after widgets are created with longer delay
            QTimer.singleShot(200, lambda: self._restore_pane_positions(ui_state))

        except Exception as e:
            print(f"Error restoring UI state: {e}")

    def _restore_profile_selection(self, selected_profile: Optional[str]):
        """Restore profile selection after widget is fully created."""
        try:
            if hasattr(self.app, 'profile_combobox') and selected_profile:
                self.app.profile_combobox.setCurrentText(selected_profile)
                print(f"Restored profile selection: {selected_profile}")
        except Exception as e:
            print(f"Error restoring profile selection: {e}")

    def _apply_thread_settings(self):
        """Apply current thread settings to the normalizer."""
        try:
            if hasattr(self.app, 'normalizer') and self.app.normalizer:
                if hasattr(self.app.normalizer, 'scanner'):
                    self.app.normalizer.scanner.max_workers_local = getattr(self.app, 'current_scan_threads', 8)
                    self.app.normalizer.scanner.max_workers_network = max(2, getattr(self.app, 'current_scan_threads', 8) // 2)
                print(f"Applied thread settings: scan={getattr(self.app, 'current_scan_threads', 8)}, copy={getattr(self.app, 'current_copy_threads', 16)}")
        except Exception as e:
            print(f"Error applying thread settings: {e}")

    def _restore_log_panel_state(self, collapsed: bool):
        """Restore log panel collapse state."""
        try:
            # This will be implemented when log panel is converted to PyQt5
            print(f"Log panel state restoration: collapsed={collapsed}")
        except Exception as e:
            print(f"Error restoring log panel state: {e}")

    def _restore_pane_positions(self, ui_state: Dict[str, Any]):
        """Restore pane positions (PyQt5 splitters)."""
        try:
            # Restore horizontal splitter position
            if hasattr(self.app, 'main_horizontal_splitter') and ui_state.get("horizontal_pane_position"):
                pos = ui_state["horizontal_pane_position"]
                remaining = self.app.main_horizontal_splitter.width() - pos
                self.app.main_horizontal_splitter.setSizes([pos, remaining])
                print(f"Restored horizontal pane position: {pos}")
                
        except Exception as e:
            print(f"Error restoring pane positions: {e}")

    def get_setting(self, section: str, key: str, default=None):
        """Get a specific setting value."""
        settings = self.load_settings()
        return settings.get(section, {}).get(key, default)

    def update_setting(self, section: str, key: str, value):
        """Update a specific setting value."""
        settings = self.load_settings()
        if section not in settings:
            settings[section] = {}
        settings[section][key] = value
        self.save_settings(settings)
