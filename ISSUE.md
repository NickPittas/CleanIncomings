# PyQt5 Conversion: Changed and New Files List

This file lists all Python files that have been newly created or significantly modified as part of the PyQt5 conversion. This list will be used for detailed comparison with their Tkinter counterparts to ensure feature parity and identify missing or broken functionality.

## Main Application
- app_gui_pyqt5.py

## GUI Components (PyQt5)
- python/gui_components/widget_factory_pyqt5.py
- python/gui_components/settings_window_pyqt5.py
- python/gui_components/json_pattern_editor_pyqt5.py
- python/gui_components/profile_editor_pyqt5.py
- python/gui_components/progress_panel_pyqt5.py
- python/gui_components/vlc_player_pyqt5.py
- python/gui_components/tree_manager_pyqt5.py
- python/gui_components/status_manager_pyqt5.py
- python/gui_components/settings_manager_pyqt5.py
- python/gui_components/file_operations_manager_pyqt5.py
- python/gui_components/theme_manager_pyqt5.py
- python/gui_components/batch_edit_dialog_pyqt5.py

## Tkinter Backups (for reference)
- python/gui_components/widget_factory_tkinter_backup.py
- python/gui_components/settings_manager_tkinter_backup.py
- python/gui_components/scan_manager_tkinter_backup.py

## Core Logic / Adapters
- python/gui_normalizer_adapter.py (PyQt5 adaptation required)

## JSON Editors (PyQt5)
- python/gui_components/json_editors/patterns_editor_window_pyqt5.py
- python/gui_components/json_editors/profiles_editor_window_pyqt5.py

## Other Supporting Files
- python/gui_components/nuke_theme.py

---

This list will be the basis for a detailed, method-by-method and feature-by-feature comparison with the original Tkinter files. Each file will be analyzed for missing methods, incomplete logic, broken imports, and any deviation from the original application's functionality.
