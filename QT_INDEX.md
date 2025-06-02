\
# Project Instrumentality: PyQt5 Conversion Task Index

This document outlines the prioritized tasks for the CleanIncomings PyQt5 UI conversion, referencing their detailed analysis in the `ISSUES*.md` files.

## Severity: CRITICAL (Core System Integrity & Essential Functionality)

1.  **PyQt5 File:** `app_gui_pyqt5.py`
    *   **Tkinter Counterpart:** `app_gui.py`
    *   **Analysis Location:** `ISSUES.md` (Section 1, approx. line 5)
    *   **Sub-Issues Addressed:**
        *   **1.B.4 (Normalizer Initialization):** Corrected `try-except` block, ensured progress signal connection from `GuiNormalizerAdapter` (anticipating `progress_updated_signal` or `progress_callback`).
        *   **1.D.11 (update_progress_from_normalizer):** Ensured method exists and handles dictionary-based progress data, calling `StatusManager` appropriately.
        *   **1.C.5 (Preview Section - Sorting):** Implemented `_on_sort_change` and `_toggle_sort_direction` to call `tree_manager.sort_preview_tree`.
        *   **1.C.5 (Preview Section - Filtering):** Implemented `_on_filter_change` to call `tree_manager.filter_preview_tree`.
        *   **1.C.5 (Preview Section - Selection):** Implemented `_select_all_sequences` and `_select_all_files` to call `TreeManager` methods and update UI.
        *   **1.C.5 (Preview Section - Batch Edit Dialog):** `BatchEditDialogPyQt5` implemented. Integrated into `app_gui_pyqt5.py` by adding `_open_batch_edit_dialog` and `_handle_applied_batch_changes`. The `_handle_applied_batch_changes` method now contains logic to apply changes and calls new (assumed) `TreeManager` methods for item updates and potential tree rebuilds.
    *   **Notes:** Main application window and foundational logic. Info display in preview section is pending. `TreeManager` needs new methods to support batch edit updates.

2.  **PyQt5 File:** `python/gui_components/progress_panel_pyqt5.py` (and new `status_manager.py`)
    *   **Tkinter Counterpart:** `python/gui_components/progress_panel.py`
    *   **Analysis Location:** (Issue 1.C.4 in `ISSUES.md`)
    *   **Status:** `StatusManager` (`python/gui_components/status_manager.py`) has been created and integrated with `ScanManager`. It handles status messages and progress bar updates for scan and copy operations. `ProgressPanelPyQt5` is the UI component that `StatusManager` will update.
    *   **TODO:** Ensure `ProgressPanelPyQt5` correctly displays updates from `StatusManager`.
    *   **Notes:** Provides feedback on ongoing operations.

3.  **PyQt5 File:** `python/gui_components/tree_manager_pyqt5.py` (Partially Implemented)
    *   **Tkinter Counterpart:** `python/gui_components/tree_manager.py`
    *   **Analysis Location:** (Implicitly part of Issue 1.C.5, 1.C.2, 1.C.3 in `ISSUES.md`)
    *   **Status:** 
        *   Core methods for batch editing support (`update_item_properties_and_refresh_display`, `rebuild_preview_tree_from_current_data`) are implemented.
        *   `populate_preview_tree` has been significantly reworked: 
            *   Uses a master data list (`self.master_item_data_list`).
            *   Calls `GuiNormalizerAdapter.get_item_display_details` for each item to get column text, tooltips, and icon names.
            *   Implements error handling: if `get_item_display_details` fails for an item, a placeholder error item is added to the tree.
            *   Sets item icons by calling `self.app.widget_factory.get_icon(icon_name)`. This assumes `WidgetFactoryPyQt5` has a `get_icon` method and can resolve icon names to `QIcon` objects (likely via `ThemeManagerPyQt5`).
            *   Current implementation assumes sequences are single entries in the input `item_data_list` and adds all items as top-level tree items.
        *   Sorting and filtering methods (`sort_preview_tree`, `filter_preview_tree`) are updated.
    *   **TODO:** 
        *   The crucial **sequence grouping logic** within `populate_preview_tree` is still a major pending item if sequences need to be expandable with child file items. This would require `GuiNormalizerAdapter` to provide hierarchical data and `populate_preview_tree` to build parent/child `QTreeWidgetItem` structures accordingly.
        *   Ensure `WidgetFactoryPyQt5.get_icon()` and the underlying icon/theme management are fully implemented and robust.
    *   **Notes:** Manages the preview tree. Handles population, sorting, filtering, and item updates. Heavily reliant on `GuiNormalizerAdapter` for item data and `WidgetFactoryPyQt5` for icons.

4.  **PyQt5 File:** `python/gui_normalizer_adapter.py` (Significantly Enhanced)
    *   **Tkinter Counterpart:** `python/gui_normalizer_adapter.py` (though the PyQt5 version is more advanced now)
    *   **Analysis Location:** (Implicitly part of many issues, core to functionality)
    *   **Status:** 
        *   Initialized logging.
        *   Implemented `get_item_display_details` crucial for `TreeManager`. This includes a helper `_format_size_for_display` for human-readable file/sequence sizes and logic for icon determination based on item type and extension.
        *   Improved error handling in `scan_and_normalize_structure` for empty scan results.
        *   Added `get_available_tasks_for_profile` to fetch task names from `patterns.json`.
        *   Added placeholder `get_available_assets_for_profile`.
        *   Added `get_path_preview` to predict destination paths upon changes in the batch edit dialog. This method now calls `MappingGenerator.generate_path_from_proposal_data` for path predictions.
    *   **TODO:** Review if `get_available_assets_for_profile` needs a more concrete implementation based on project needs.
    *   **Notes:** Adapts the core normalization logic for the GUI, providing necessary data transformations and lookups.

## III. Core Logic Components (Potentially needing minor adjustments for PyQt5 data flow)

6.  **Python File:** `python/mapping.py` (`MappingGenerator` class) (Enhanced)
    *   **Analysis Location:** (Core to normalization logic)
    *   **Status:** 
        *   Refactored pattern loading in `__init__` and `reload_patterns` for consistency and robustness, loading all pattern types (shot, task, version, resolution, asset, stage) as instance attributes.
        *   Implemented the new `generate_path_from_proposal_data` method. This method is called by `GuiNormalizerAdapter.get_path_preview` and uses `mapping_utils.generate_simple_target_path` to predict destination paths for both files and sequences (with sequences showing a directory preview).
    *   **TODO:** Consider if `generate_path_from_proposal_data` needs more sophisticated handling for sequence previews beyond the current directory-level preview.
    *   **Notes:** Generates mapping proposals. The new path preview method is key for the batch edit dialog.

## Severity: HIGH (Significant Features & Application Stability)

5.  **PyQt5 File:** `python/gui_components/widget_factory_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/widget_factory.py`
    *   **Analysis Location:** `ISSUES.md` (Section 2, approx. line 50)
    *   **Notes:** Central to UI element creation. Many UI components in `app_gui_pyqt5.py` depend on its full implementation.

6.  **PyQt5 File:** `python/gui_components/settings_window_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/settings_window.py`
    *   **Analysis Location:** `ISSUES.md` (Section 3, approx. line 100), `ISSUES_2.md` (Issue 5.G.2 for Profile Management Tab, line 97)
    *   **Notes:** Application settings are crucial. The "Profile Management" tab is a placeholder and needs to integrate with the advanced `ProfilesEditorWindowPyQt5`.

7.  **PyQt5 File:** `python/gui_components/json_editors/profiles_editor_window_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/json_editors/ProfilesEditorWindow.py`
    *   **Analysis Location:** `ISSUES_2.md` (Section 5, line 7)
    *   **Notes:** Advanced editor for profiles. Requires integration with the main settings window and implementation of data cleaning logic from the Tkinter version (Issue 5.B.2).

8.  **PyQt5 File:** `python/gui_components/file_operations_manager_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/file_operations_manager.py`
    *   **Analysis Location:** `ISSUES_3.md` (Section 13, line 213)
    *   **Notes:** Manages file copy/move operations. Current PyQt5 version is a stub. Worker logic, low-level operations, and progress signaling are critical.

9.  **PyQt5 File:** `python/gui_components/status_manager_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/status_manager.py`
    *   **Analysis Location:** `ISSUES_3.md` (Section 11, line 6)
    *   **Notes:** Manages status messages, progress bar updates, and logging. Most methods are stubs and need implementation with PyQt5 UI elements.

10. **PyQt5 File:** `python/gui_components/theme_manager_pyqt5.py` (Created & Enhanced)
    *   **Tkinter Counterpart:** `python/gui_components/theme_manager.py`
    *   **Analysis Location:** `ISSUES_3.md` (Section 12, line 120 - detailed plan) & `ISSUES_2.md` (Section 12, line 701 - initial mention)
    *   **Status:** Initial version created and `icon_mapping` populated.
        *   `__init__`: Sets up `base_icons_dir` relative to the project root. Initializes `icon_mapping` dictionary to map logical icon names to filenames (e.g., 'folder' to 'folder_open_16.png', 'error' to 'RotoPaint.png', etc.). The mapping has been populated with choices from the existing `icons/` directory. Includes a `_validate_icon_mappings` call to check for missing icon files and log warnings, remapping to a fallback if necessary.
        *   `get_icon_path(icon_name)`: Returns the absolute path to an icon file based on the logical name and `icon_mapping`. Includes fallbacks for unmapped names or missing files.
        *   Placeholder methods for QSS stylesheet loading (`get_current_theme_stylesheet`) and theme switching (`set_theme`) are present.
    *   **TODO:**
        *   Implement QSS file loading and application for different themes (e.g., 'dark', 'light').
        *   Review and refine `icon_mapping` if current choices are not optimal.
        *   Ensure all icon files listed in `icon_mapping` actually exist in the `icons/` directory or are correctly remapped by `_validate_icon_mappings`.
        *   Integrate theme switching with UI controls in `SettingsWindowPyQt5`.
    *   **Notes:** New file created for managing icon paths and QSS-based themes. `WidgetFactoryPyQt5` relies on this for icon retrieval. The `icon_mapping` has been updated with specific icon choices.

11. **PyQt5 File:** `python/normalizer.py` (and components `scanner.py`, `mapping.py`)
    *   **Tkinter Counterpart:** (Same, as it\'s backend logic)
    *   **Analysis Location:** `ISSUES_3.md` (Section 15, line 334 - Integration Aspects)
    *   **Notes:** Core backend logic. Focus on ensuring UI agnosticism, a robust progress callback mechanism for the adapter, and comprehensive error handling.

## Severity: MEDIUM (Important Supporting Features & Refinements)

12. **PyQt5 File:** `python/gui_components/json_editors/patterns_editor_window_pyqt5.py`
    *   **Tkinter Counterpart:** `python/gui_components/json_editors/PatternsEditorWindow.py`
    *   **Analysis Location:** `ISSUES.md` (Section 4, approx. line 150, also referred in `ISSUES_2.md` Section 4)
    *   **Notes:** Editor for `patterns.json`. Requires implementation of data loading/saving, UI interactions, and validation.

13. **PyQt5 File:** `python/config_manager.py` (Role and PyQt5 integration)
    *   **Tkinter Counterpart:** `python/config_manager.py` (if present and used similarly)
    *   **Analysis Location:** `ISSUES_2.md` (Section 13, line 741)
    *   **Notes:** Role in PyQt5 needs clarification. Focus on robust path determination (potentially using `QStandardPaths`) for configuration files.

14. **PyQt5 File:** `python/gui_components/batch_edit_dialog_pyqt5.py` (Implemented)
    *   **Tkinter Counterpart:** `python/gui_components/batch_edit_dialog.py`
    *   **Analysis Location:** (Implicitly part of Issue 1.C.5 in `ISSUES.md`)
    *   **Notes:** Component for batch editing properties of selected items. Relies on `GuiNormalizerAdapter` for dropdown values and path previews. Fully implemented and integrated into `app_gui_pyqt5.py`.

## Severity: LOW (Minor Enhancements & Code Hygiene)

15. **PyQt5 File:** `python/utils.py`
    *   **Tkinter Counterpart:** `python/utils.py`
    *   **Analysis Location:** `ISSUES.md` (General analysis, no specific section/line number from provided logs)
    *   **Notes:** Review for any Tkinter-specific utilities that are no longer needed or can be replaced. Consider moving the custom `StringVar(QObject)` class here for better modularity if it was analyzed as part of `utils.py`.
