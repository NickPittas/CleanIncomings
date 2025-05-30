"""
Settings Manager Module

Handles UI state persistence and restoration for the Clean Incomings application.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


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
                "copy_threads": 16  # Balanced for 10GbE copying - good performance without overload
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
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults to handle new settings
                    return self._merge_with_defaults(settings)
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()

    def save_settings(self, settings: Dict[str, Any]):
        """Save settings to file."""
        try:
            self.settings_file.parent.mkdir(exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _merge_with_defaults(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded settings with defaults to handle new settings."""
        merged = self.default_settings.copy()
        if "ui_state" in settings:
            merged["ui_state"].update(settings["ui_state"])
        return merged

    def get_current_ui_state(self) -> Dict[str, Any]:
        """Get current UI state from the application."""
        try:
            # Get window geometry and position
            geometry = self.app.geometry()
            window_x = self.app.winfo_x() if self.app.winfo_x() > 0 else None
            window_y = self.app.winfo_y() if self.app.winfo_y() > 0 else None
            window_position = f"+{window_x}+{window_y}" if window_x and window_y else None

            # Get pane positions if available
            horizontal_position = None
            vertical_positions = None
            
            if hasattr(self.app, 'main_horizontal_pane'):
                try:
                    horizontal_position = self.app.main_horizontal_pane.sashpos(0)
                except:
                    pass

            if hasattr(self.app, 'main_vertical_pane'):
                try:
                    sash_positions = []
                    panes = self.app.main_vertical_pane.panes()
                    for i in range(len(panes) - 1):
                        sash_positions.append(self.app.main_vertical_pane.sashpos(i))
                    vertical_positions = sash_positions if sash_positions else None
                except:
                    pass

            return {
                "window_geometry": geometry,
                "window_position": window_position,
                "log_panel_collapsed": getattr(self.app, 'log_panel_collapsed', False),
                "horizontal_pane_position": horizontal_position,
                "vertical_pane_positions": vertical_positions,
                "source_folder": self.app.selected_source_folder.get(),
                "destination_folder": self.app.selected_destination_folder.get(),
                "selected_profile": self.app.selected_profile_name.get(),
                "appearance_mode": getattr(self.app, 'current_appearance_mode', "System"),
                "color_theme": getattr(self.app, 'current_color_theme', "blue"),
                "scan_threads": getattr(self.app, 'current_scan_threads', 8),
                "copy_threads": getattr(self.app, 'current_copy_threads', 16)
            }
        except Exception as e:
            print(f"Error getting current UI state: {e}")
            return self.default_settings["ui_state"].copy()

    def restore_ui_state(self, ui_state: Dict[str, Any]):
        """Restore UI state to the application."""
        try:
            # Restore window geometry and position
            if ui_state.get("window_geometry"):
                geometry = ui_state["window_geometry"]
                if ui_state.get("window_position"):
                    geometry += ui_state["window_position"]
                self.app.geometry(geometry)

            # Restore folder selections
            if ui_state.get("source_folder"):
                self.app.selected_source_folder.set(ui_state["source_folder"])
            
            if ui_state.get("destination_folder"):
                self.app.selected_destination_folder.set(ui_state["destination_folder"])

            # Restore profile selection
            if ui_state.get("selected_profile") and hasattr(self.app, 'profile_combobox'):
                try:
                    self.app.selected_profile_name.set(ui_state["selected_profile"])
                    # Defer profile combobox setting until widget is fully created
                    self.app.after(100, lambda: self._restore_profile_selection(ui_state.get("selected_profile")))
                except:
                    pass

            # Restore log panel state
            self.app.log_panel_collapsed = ui_state.get("log_panel_collapsed", True)  # Default to True (collapsed)
            
            # Restore thread settings
            self.app.current_scan_threads = ui_state.get("scan_threads", 8)
            self.app.current_copy_threads = ui_state.get("copy_threads", 16)
            
            # Apply thread settings to components after restoration
            self.app.after(100, self._apply_thread_settings)
            
            # Apply log panel state after widgets are created with appropriate delay
            self.app.after(500, lambda: self._restore_log_panel_state(ui_state.get("log_panel_collapsed", True)))

            # Schedule pane position restoration after widgets are created with longer delay
            self.app.after(200, lambda: self._restore_pane_positions(ui_state))

        except Exception as e:
            print(f"Error restoring UI state: {e}")

    def _restore_profile_selection(self, selected_profile: str):
        """Restore profile selection after widget is fully created."""
        try:
            if hasattr(self.app, 'profile_combobox') and selected_profile:
                self.app.profile_combobox.set(selected_profile)
                print(f"Restored profile selection: {selected_profile}")
        except Exception as e:
            print(f"Error restoring profile selection: {e}")

    def _restore_pane_positions(self, ui_state: Dict[str, Any]):
        """Restore pane positions after widgets are fully created."""
        try:
            # Restore horizontal pane position
            horizontal_position = ui_state.get("horizontal_pane_position")
            if horizontal_position and hasattr(self.app, 'main_horizontal_pane'):
                try:
                    self.app.main_horizontal_pane.sashpos(0, horizontal_position)
                    print(f"Restored horizontal pane position: {horizontal_position}")
                except Exception as e:
                    print(f"Error setting horizontal pane position: {e}")

            # Restore vertical pane positions
            vertical_positions = ui_state.get("vertical_pane_positions")
            if vertical_positions and hasattr(self.app, 'main_vertical_pane'):
                try:
                    panes = self.app.main_vertical_pane.panes()
                    for i, position in enumerate(vertical_positions):
                        if i < len(panes) - 1:
                            self.app.main_vertical_pane.sashpos(i, position)
                    print(f"Restored vertical pane positions: {vertical_positions}")
                except Exception as e:
                    print(f"Error setting vertical pane positions: {e}")

        except Exception as e:
            print(f"Error restoring pane positions: {e}")

    def _restore_log_panel_state(self, collapsed: bool):
        """Restore log panel state after widgets are fully created."""
        try:
            if hasattr(self.app, 'log_content_frame') and hasattr(self.app, 'log_toggle_btn'):
                self.app.log_panel_collapsed = collapsed
                if collapsed:
                    # Collapse log panel
                    self.app.log_content_frame.grid_remove()
                    self.app.log_toggle_btn.configure(text="🔼")  # Up arrow
                else:
                    # Expand log panel
                    self.app.log_content_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
                    self.app.log_toggle_btn.configure(text="🔽")  # Down arrow
                print(f"Restored log panel state: {'collapsed' if collapsed else 'expanded'}")
        except Exception as e:
            print(f"Error restoring log panel state: {e}")

    def _apply_thread_settings(self):
        """Apply thread settings to components after they are restored."""
        try:
            scan_threads = getattr(self.app, 'current_scan_threads', 8)
            copy_threads = getattr(self.app, 'current_copy_threads', 16)
            
            # Apply to scanner if available
            if hasattr(self.app, 'normalizer') and hasattr(self.app.normalizer, 'scanner'):
                self.app.normalizer.scanner.max_workers_local = scan_threads
                self.app.normalizer.scanner.max_workers_network = max(2, scan_threads // 2)
                print(f"Applied scan thread settings: local={scan_threads}, network={self.app.normalizer.scanner.max_workers_network}")
            
            # Apply to file operations manager if available
            if hasattr(self.app, 'file_operations_manager'):
                self.app.file_operations_manager.max_concurrent_transfers = copy_threads
                # Recreate the thread pool with the new worker count
                if hasattr(self.app.file_operations_manager, 'thread_pool'):
                    self.app.file_operations_manager.thread_pool.shutdown(wait=False)
                    import concurrent.futures
                    self.app.file_operations_manager.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=copy_threads)
                print(f"Applied copy thread settings: {copy_threads}")
            
        except Exception as e:
            print(f"Error applying thread settings: {e}")

    def save_current_state(self):
        """Save current application state."""
        settings = self.load_settings()
        settings["ui_state"] = self.get_current_ui_state()
        self.save_settings(settings) 