# PyQt5 Conversion: Issues and Discrepancies Log

This document tracks the differences, missing functionalities, and necessary changes to ensure the PyQt5 version of CleanIncomings achieves full feature parity with the original Tkinter application.

## Phase 1: Identification of Changed/New Files for PyQt5 Conversion

The following files are central to the PyQt5 conversion and will be systematically compared against their original Tkinter counterparts or analyzed for complete functionality.

### Main Application:
1.  **New:** `app_gui_pyqt5.py`
    *   **Original:** `app_gui.py` (and `app_gui_tkinter_backup.py`)
    *   **Status:** Initial analysis complete; open issues logged.

### GUI Components (under `python/gui_components/`):
2.  **New:** `python/gui_components/widget_factory_pyqt5.py`
    *   **Original:** `python/gui_components/widget_factory.py`
    *   **Status:** Initial analysis complete; open issues logged.
3.  **New:** `python/gui_components/settings_window_pyqt5.py`
    *   **Original:** `python/gui_components/settings_window.py`
    *   **Status:** Initial analysis complete; open issues logged.
4.  **New:** `python/gui_components/json_pattern_editor_pyqt5.py`
    *   **Original:** `python/gui_components/json_pattern_editor.py`
    *   **Status:** Pending Analysis.
5.  **New:** `python/gui_components/profile_editor_pyqt5.py`
    *   **Original:** `python/gui_components/profile_editor.py`
    *   **Status:** Pending Analysis.
6.  **New:** `python/gui_components/progress_panel_pyqt5.py`
    *   **Original:** `python/gui_components/progress_panel.py` (and `python/gui_components/file_operations_progress.py`)
    *   **Status:** Pending Analysis.
7.  **New:** `python/gui_components/vlc_player_window_pyqt5.py` (or similar for media playback)
    *   **Original:** `python/gui_components/vlc_player_window.py`
    *   **Status:** Pending Analysis.
8.  **New:** `python/gui_components/tree_manager_pyqt5.py`
    *   **Original:** `python/gui_components/tree_manager.py`
    *   **Status:** Pending Analysis.

### Core Logic / Managers (under `python/`):
These files likely underwent modifications or have new adapters/versions. Each needs to be checked for how it integrates with the PyQt5 UI and backend logic.

9.  **`python/scan_manager.py`**
    *   **Status:** Pending Analysis (focus on PyQt5 integration).
10. **`python/settings_manager.py`** (and potentially `settings_manager_pyqt5.py`)
    *   **Original:** `python/settings_manager.py`
    *   **Status:** Pending Analysis (focus on PyQt5 integration).
11. **`python/status_manager.py`** (and potentially `status_manager_pyqt5.py`)
    *   **Original:** `python/status_manager.py`
    *   **Status:** Pending Analysis (focus on PyQt5 integration).
12. **`python/file_operations_manager.py`**
    *   **Status:** Pending Analysis (focus on PyQt5 integration).
13. **`python/normalizer.py`** and **`python/gui_normalizer_adapter.py`**
    *   **Status:** Pending Analysis (focus on adapter for PyQt5 UI).
14. **`python/theme_manager.py`** (and potentially `theme_manager_pyqt5.py`)
    *   **Original:** `python/theme_manager.py`
    *   **Status:** Pending Analysis (focus on PyQt5 stylesheet management).
15. **`python/config_manager.py`**
    *   **Status:** Pending Analysis (focus on interaction with PyQt5 settings components).
16. **Utility Files:** `python/utils.py`
    *   **Status:** Pending Analysis (review for PyQt5 specific changes/additions).

## Phase 2: Detailed File-by-File Comparison and Issue Logging

### 1. Main Application: `app_gui_pyqt5.py` vs `app_gui.py`

#### A. Global Scope and Imports

*   **Issue 1.A.1: VLC Path Configuration and Import**
    *   **Context:** Both files handle VLC path setup (`get_application_path`, `libvlc_dir`, `os.add_dll_directory`, `VLC_PLUGIN_PATH`) and `import vlc` globally.
    *   **Discrepancy/Issue:**
        *   The original Tkinter version had a `try-except AttributeError` for `os.add_dll_directory` for compatibility with older Python versions. `app_gui_pyqt5.py` has similar logic but its robustness across environments (frozen app vs. dev) needs confirmation.
    *   **Required Action:**
        *   Verify `os.add_dll_directory` fallback/warning is correctly handled or still relevant in the PyQt5 context.
        *   Confirm `VLC_PLUGIN_PATH` setting is effective for PyQt5.
        *   Ensure `_vlc_module_imported_successfully` flag accurately reflects import status and is used consistently.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.A.2: Modular Component Imports**
    *   **Context:** Importing manager classes and UI components.
    *   **Discrepancy/Issue:**
        *   `app_gui_pyqt5.py` imports PyQt5-specific versions (e.g., `StatusManagerPyQt5`).
        *   `VLCPlayerWindow` import is commented out: `# from python.gui_components.vlc_player_window import VLCPlayerWindow  # Skip for now`. This needs to be `vlc_player_window_pyqt5.py`.
        *   The `ThemeManager` import `from python.gui_components.theme_manager import ThemeManager` might need to point to a `theme_manager_pyqt5.py` if PyQt5-specific theme logic (stylesheets, QPalette) is extensive beyond the current `apply_nuke_theme`.
    *   **Required Action:**
        *   Ensure all managers have their correct PyQt5 counterparts imported (e.g., `StatusManagerPyQt5`, `TreeManagerPyQt5`, etc.).
        *   Update the commented `VLCPlayerWindow` import to `from python/gui_components/vlc_player_window_pyqt5 import VLCPlayerWindowPyQt5` (assuming class name) and plan its integration.
        *   Evaluate if a dedicated `theme_manager_pyqt5.py` is necessary or if `ThemeManager` can be adapted.
    *   **Priority:** Medium
    *   **Status:** Open

#### B. `CleanIncomingsApp.__init__` Method

*   **Issue 1.B.1: Class Inheritance**
    *   **Original:** `class CleanIncomingsApp(ctk.CTk):`
    *   **PyQt5:** `class CleanIncomingsApp(QMainWindow):`
    *   **Discrepancy/Issue:** Correct change for PyQt5.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 1.B.2: Initialization of Instance Variables**
    *   **Context:** Setting up various instance attributes.
    *   **Discrepancy/Issue:**
        *   Generally consistent (e.g., `preview_tree_item_data_map`, `active_transfers`, `setWindowTitle`, `setGeometry`).
        *   `current_corner_radius` changed from 10 (Tkinter) to 6 (PyQt5) - likely a stylistic choice.
        *   Custom `StringVar(QObject)` in PyQt5 is a good compatibility layer for `selected_source_folder`, `selected_destination_folder`, `selected_profile_name`, `ffplay_path_var`.
    *   **Required Action:**
        *   Verify all managers and components that previously relied on `tk.StringVar` traces are now correctly using the `valueChanged` signal of the custom `StringVar` or have been adapted to a more direct PyQt5 signal/slot mechanism if appropriate.
        *   Ensure all necessary instance variables from the original `__init__` are present or accounted for.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.B.3: Configuration Directory Path (`_determine_config_path`)**
    *   **Context:** Method to find the `config` directory.
    *   **Discrepancy/Issue:** Logic appears identical and directly ported.
    *   **Required Action:** Confirm it works correctly in various execution contexts for PyQt5 (dev, potential frozen app).
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 1.B.4: Normalizer Initialization (`_initialize_normalizer`)**
    *   **Context:** Setting up `GuiNormalizerAdapter`.
    *   **Discrepancy/Issue:**
        *   The `try-except` block in `app_gui_pyqt5.py`'s `_initialize_normalizer` method was flawed (bare `except`, misplaced `print`). The original Tkinter version had `except Exception as e:`.
    *   **Required Action:**
        *   Ensure the `try-except` block in `app_gui_pyqt5.py` correctly catches `Exception as e` and that error handling logic (e.g., `QMessageBox.warning`, logging, resetting `profile_names`) is within the `except` block.
        *   The `self.normalizer.progress_callback.connect(self.update_progress_from_normalizer)` line from `app_gui_pyqt5.py` is good for progress updates.
    *   **Priority:** High
    *   **Status:** Open (Pending verification of fix)

*   **Issue 1.B.5: Component Initialization (`_initialize_components`)**
    *   **Context:** Initializing manager classes.
    *   **Discrepancy/Issue:**
        *   PyQt5 version initializes PyQt5-suffixed managers (e.g., `StatusManagerPyQt5`, `WidgetFactoryPyQt5`).
        *   `VLCPlayerWindow` instantiation is commented out.
        *   Calls `_setup_compatibility_layer()`. This method in `app_gui_pyqt5.py` provides `geometry()` and `after()` compatibility, and connects `selected_profile_name.valueChanged`.
        *   Loads settings via `self.settings_manager.load_settings()` and initializes `ffplay_path_var` using the custom `StringVar.set()`.
    *   **Required Action:**
        *   Review `_setup_compatibility_layer()`:
            *   The `geometry` compatibility method is for `SettingsManager` to save/restore window state. Ensure this is the best approach or if PyQt5's `saveGeometry`/`restoreGeometry` on `QMainWindow` should be used directly by `SettingsManager`.
            *   The `after` method (wrapping `QTimer.singleShot`) is a good compatibility shim.
            *   The `selected_profile_name.valueChanged.connect(self._handle_profile_change)` is appropriate.
        *   Ensure `SettingsManager.load_settings()` in PyQt5 correctly loads all necessary settings.
        *   Verify all managers from the original are initialized with their PyQt5 counterparts or their absence is intentional (e.g., `VLCPlayerWindow`).
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.B.6: Main UI Creation Call**
    *   **Original:** `self.widget_factory.create_widgets()`, `self.theme_manager.setup_treeview_style()`
    *   **PyQt5:** `self._create_ui()`
    *   **Discrepancy/Issue:** `_create_ui` in PyQt5 handles widget creation (delegating to `WidgetFactoryPyQt5` and direct creation) and theme application (`apply_nuke_theme`). This is a logical change.
    *   **Required Action:** None for the call itself. Detailed review of `_create_ui` follows.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 1.B.7: Profile Configuration Call (`_configure_profiles`)**
    *   **Context:** Called at the end of `__init__`.
    *   **Discrepancy/Issue:** Consistent call timing.
    *   **Required Action:** Verify the implementation of `_configure_profiles` itself for PyQt5 compatibility (see method-specific analysis).
    *   **Priority:** Low (for call consistency)
    *   **Status:** Open

*   **Issue 1.B.8: Window Close Event**
    *   **Original:** `self.protocol("WM_DELETE_WINDOW", self._on_closing)`
    *   **PyQt5:** `QMainWindow` uses `closeEvent(self, event)` method override. `app_gui_pyqt5.py` implements this.
    *   **Discrepancy/Issue:** Correct adaptation to PyQt5's event model.
    *   **Required Action:** Verify `_on_closing` logic is correctly ported to `closeEvent` (see method-specific analysis).
    *   **Priority:** N/A
    *   **Status:** Resolved

#### C. UI Creation Methods (`_create_ui`, `_create_top_control_frame`, `_create_main_layout`, etc.)

*   **Issue 1.C.1: `_create_ui`**
    *   **Context:** Main method to set up the UI structure.
    *   **Original:** UI built primarily by `WidgetFactory` methods called in `__init__`.
    *   **PyQt5:** `_create_ui` sets up `QMainWindow`, central widget, main layout, calls sub-methods for top controls, main layout, status bar, and applies theme.
    *   **Discrepancy/Issue:** PyQt5 approach is more structured with dedicated UI building methods.
    *   **Required Action:** Detailed review of sub-methods. Ensure status bar is correctly initialized and `self.status_label` is added to it.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.C.2: `_create_top_control_frame`**
    *   **Context:** Creates the top panel with profile selector, folder inputs, scan, and settings buttons.
    *   **Original:** Widgets created by `WidgetFactory` (e.g., `profile_combobox`, `source_folder_button`, `destination_folder_button`, `scan_button`, `settings_button`) and laid out using Tkinter frames and `grid`/`pack`.
    *   **PyQt5:** Uses `QFrame`, `QVBoxLayout`, `QHBoxLayout`. Widgets like `profile_combobox`, `refresh_btn`, `settings_btn`, `source_folder_entry`, `dest_folder_entry` are created. Buttons for folder selection use `widget_factory.create_compact_button`.
    *   **Discrepancy/Issue:**
        *   Layout is different (two rows in PyQt5).
        *   Tkinter used `CTkOptionMenu` for profiles, PyQt5 uses `QComboBox`.
        *   Tkinter had separate labels and buttons for folder selection; PyQt5 has a label, a compact button, and a `QLineEdit`.
        *   Connections: `refresh_btn` connected to `scan_manager.refresh_scan_data`. Settings button to `_open_settings_window`. Folder buttons to `_select_source_folder`/`_select_destination_folder`. Folder entries to `selected_source_folder.set`/`selected_destination_folder.set`.
    *   **Required Action:**
        *   Verify all original controls are present or have equivalents.
        *   Ensure functionality of folder selection (button + line edit) is intuitive and updates the `StringVar`-like objects correctly.
        *   Confirm `scan_manager.refresh_scan_data` is the correct method to call.
        *   Check if `widget_factory.create_accent_button` and `create_compact_button` produce desired styling.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.C.3: `_create_main_layout`**
    *   **Context:** Sets up the main resizable areas (source tree and preview/actions).
    *   **Original:** Likely used `CTkFrame` and `pack` or `grid` with `expand=True`, `fill='both'`. A PanedWindow equivalent might have been used if resizable.
    *   **PyQt5:** Uses `QSplitter(Qt.Horizontal)` for resizable panels. Calls `_create_source_tree_section` and `_create_preview_section`. Sets initial splitter sizes.
    *   **Discrepancy/Issue:** `QSplitter` is a good choice for resizable panels.
    *   **Required Action:** Verify sub-methods correctly populate the splitter panes.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 1.C.4: `_create_source_tree_section`**
    *   **Context:** Left panel displaying source folder structure.
    *   **Original:** `source_treeview` created by `WidgetFactory`. Might have had a "Show All" button or similar controls.
    *   **PyQt5:** Uses `widget_factory.create_group_box("Source Folder Structure")`. Adds a header with title and `show_all_btn` (`widget_factory.create_compact_button`). `source_tree` created by `widget_factory.create_source_tree()`.
    *   **Discrepancy/Issue:**
        *   `show_all_btn` connected to `_show_all_sequences` (placeholder in `app_gui_pyqt5.py`).
    *   **Required Action:**
        *   Implement `_show_all_sequences` to interact with `TreeManagerPyQt5` or `ScanManager` to refresh/filter the source tree.
        *   Ensure `widget_factory.create_source_tree()` creates a `QTreeWidget` with appropriate columns and settings.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.C.5: `_create_preview_section`**
    *   **Context:** Right panel for previewing normalized files and actions.
    *   **Original:** `preview_treeview` created by `WidgetFactory`. Had controls for sort, filter, selection, and action buttons (copy/move).
    *   **PyQt5:** Uses `widget_factory.create_group_box("Preview & Actions")`.
        *   Header: Sort `QComboBox` (`sort_menu`), sort direction `QPushButton` (`sort_direction_btn`), filter `QComboBox` (`filter_combo`), selection buttons (`Select Sequences`, `Select Files`, `Clear`), `batch_edit_btn`.
        *   `selection_stats_label`.
        *   `preview_tree` from `widget_factory.create_preview_tree()`.
        *   Action buttons: `copy_selected_btn`, `move_selected_btn`.
        *   Placeholder "Info display".
    *   **Discrepancy/Issue:**
        *   Many controls are similar in concept.
        *   Connections: `sort_menu` to `_on_sort_change`, `sort_direction_btn` to `_toggle_sort_direction`, `filter_combo` to `_on_filter_change`. Selection buttons to `_select_all_sequences`, `_select_all_files`, `_clear_selection`. `batch_edit_btn` to `_open_batch_edit_dialog`. `preview_tree.itemSelectionChanged` to `_on_tree_selection_change`. Copy/Move buttons to `file_operations_manager.on_copy_selected_click`/`on_move_selected_click`.
        *   Placeholders: `_on_sort_change`, `_toggle_sort_direction` (basic toggle implemented), `_on_filter_change`, `_select_all_sequences`, `_select_all_files` are placeholders or have basic print statements. `_open_batch_edit_dialog` shows a `QMessageBox`.
        *   "Info display" is a placeholder `QFrame`.
    *   **Required Action:**
        *   Implement full logic for sort, filter, and selection methods to interact with `TreeManagerPyQt5` and update the `preview_tree`.
        *   Implement `_open_batch_edit_dialog` to show a functional batch editing dialog.
        *   Implement the "Info display" to show details of the selected item in the `preview_tree`.
        *   Ensure `file_operations_manager` methods are correctly connected and functional.
        *   Verify `_on_tree_selection_change` correctly updates button states and `selection_stats_label`.
    *   **Priority:** High (core functionality)
    *   **Status:** Open

#### D. Event Handler Methods and Other Functionality

*   **Issue 1.D.1: `_configure_profiles`**
    *   **Context:** Populates the profile combobox.
    *   **Original:** Configured `CTkOptionMenu` values. Handled cases for no profiles, normalizer error. Restored saved profile selection.
    *   **PyQt5:** Clears and adds items to `profile_combobox` (`QComboBox`). Similar logic for handling no profiles, normalizer error, and restoring saved profile. Connects `profile_combobox.currentTextChanged.connect(self._on_profile_changed)`.
    *   **Discrepancy/Issue:** Logic is largely similar. PyQt5 uses `setCurrentText` for selection.
    *   **Required Action:** Test thoroughly, especially profile loading and saved state restoration. Ensure `_on_profile_changed` correctly updates `self.selected_profile_name`.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.D.2: `_handle_profile_change` and `_on_profile_changed`**
    *   **Context:** Handling profile changes from `StringVar` and `QComboBox` respectively.
    *   **PyQt5:** `_handle_profile_change` updates `QComboBox` from `StringVar`. `_on_profile_changed` updates `StringVar` from `QComboBox` and prints.
    *   **Discrepancy/Issue:** Seems like a correct two-way binding approach.
    *   **Required Action:** Verify this synchronization works without issues (e.g., infinite loops, though unlikely with distinct signals).
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 1.D.3: Folder Selection (`_select_source_folder`, `_select_destination_folder`)**
    *   **Context:** Opening folder dialogs.
    *   **Original:** Used `filedialog.askdirectory`.
    *   **PyQt5:** Uses `QFileDialog.getExistingDirectory`. Updates `StringVar`-like objects and `QLineEdit` text. Updates status label.
    *   **Discrepancy/Issue:** Correct adaptation.
    *   **Required Action:** Test functionality.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 1.D.4: `_open_settings_window`**
    *   **Context:** Launching the settings window.
    *   **Original:** Created and showed `SettingsWindow` (Tkinter version).
    *   **PyQt5:** Imports `SettingsWindow` from `settings_window_pyqt5.py`. Instantiates it, connects `settings_changed` signal to `_on_settings_changed`, and shows it. Includes `try-except ImportError`.
    *   **Discrepancy/Issue:** Correct adaptation.
    *   **Required Action:** Ensure `SettingsWindowPyQt5` is fully functional and the `settings_changed` signal mechanism works.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.D.5: `_on_settings_changed`**
    *   **Context:** Slot for when settings are updated in the settings window.
    *   **PyQt5:** Reloads settings via `self.settings_manager.load_settings()`, updates status label.
    *   **Discrepancy/Issue:** Seems appropriate.
    *   **Required Action:** Verify that all relevant UI elements or behaviors that depend on settings are refreshed/updated after this.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.D.6: Placeholder Action Methods**
    *   **Context:** `_show_all_sequences`, `_on_sort_change`, `_toggle_sort_direction` (partially implemented), `_on_filter_change`, `_select_all_sequences`, `_select_all_files`, `_open_batch_edit_dialog`.
    *   **PyQt5:** Most of these currently print to console or show a basic message box.
    *   **Discrepancy/Issue:** Core functionality missing.
    *   **Required Action:** Implement the logic for these methods to interact with `TreeManagerPyQt5`, `ScanManager`, `FileOperationsManager`, and update the UI accordingly.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 1.D.7: `_clear_selection`**
    *   **PyQt5:** Calls `self.preview_tree.clearSelection()` and `self._on_tree_selection_change()`.
    *   **Discrepancy/Issue:** Appears correct.
    *   **Required Action:** Test.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 1.D.8: `_on_tree_selection_change`**
    *   **Context:** Handles selection changes in the `preview_tree`.
    *   **Original:** Updated button states and selection info label.
    *   **PyQt5:** Gets selected items, enables/disables `copy_selected_btn`, `move_selected_btn`, `batch_edit_btn`. Updates `selection_stats_label`.
    *   **Discrepancy/Issue:** Similar logic.
    *   **Required Action:** Test thoroughly. Ensure `preview_tree_item_data_map` (or equivalent in PyQt5 `TreeManagerPyQt5`) is used if detailed info about selected items is needed for enabling buttons (e.g., distinguish files from sequences for batch edit).
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.D.9: Media Player Handlers (`play_with_ffplay_handler`, `play_with_mpv_handler`)**
    *   **Context:** Launching external media players.
    *   **Original:** Complex logic involving `MediaPlayerUtils`, checking `ffplay_path_var`, distinguishing single files vs. sequences, and preparing sequence data.
    *   **PyQt5:** Methods are present and largely ported.
        *   `ffplay_path_var.get()` is used.
        *   `os.path.isfile` check is present.
        *   Sequence detection logic: In PyQt5, the part `selected_items = self.preview_tree.selectedItems()` and getting `selected_item_data` needs to be correctly implemented to fetch data associated with `QTreeWidgetItem`s (likely via `TreeManagerPyQt5`). The current placeholder `selected_item_data = None` in `play_with_ffplay_handler` for sequences will prevent rich sequence playback.
        *   Calls to `self.media_player_utils` methods seem consistent.
    *   **Discrepancy/Issue:** The primary issue is fetching detailed item data (especially sequence info) from the `QTreeWidget` selection in PyQt5.
    *   **Required Action:**
        *   Implement proper fetching of item data (type, sequence_info, etc.) from `self.preview_tree.selectedItems()` by likely querying data stored on the items or via `TreeManagerPyQt5`.
        *   Test both single file and sequence playback thoroughly for ffplay and MPV.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 1.D.10: `closeEvent` (was `_on_closing` in Tkinter)**
    *   **Context:** Saving settings on application close.
    *   **Original:** `self.settings_manager.save_current_state()`, then `self.destroy()`.
    *   **PyQt5:** `self.settings_manager.save_current_state()`, then `event.accept()`.
    *   **Discrepancy/Issue:** Correct adaptation.
    *   **Required Action:** Test settings saving on close.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 1.D.11: `update_progress_from_normalizer`**
    *   **Context:** Slot for normalizer progress.
    *   **PyQt5:** `self.status_manager.update_progress(value, text)`
    *   **Discrepancy/Issue:** This method exists in `app_gui_pyqt5.py`. It needs to be connected to a signal from `GuiNormalizerAdapter`. The adapter's `progress_callback` signal is connected in `_initialize_normalizer`.
    *   **Required Action:** Ensure `StatusManagerPyQt5.update_progress` correctly updates a progress bar or status message in the UI.
    *   **Priority:** Medium
    *   **Status:** Open

#### E. Main Execution Block (`if __name__ == '__main__':`)

*   **Original:** `app = CleanIncomingsApp()`, `app.mainloop()`.
*   **PyQt5:**
    *   `QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)`
    *   `QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)`
    *   `app = QApplication(sys.argv)`
    *   `apply_nuke_theme(app)` (This applies theme to the application globally)
    *   `window = CleanIncomingsApp()`
    *   `window.show()`
    *   `sys.exit(app.exec_())`
*   **Discrepancy/Issue:** Correct setup for a PyQt5 application. High DPI settings are good. Global theme application is also fine.
*   **Required Action:** None.
*   **Priority:** N/A
*   **Status:** Resolved

---

### 2. GUI Components: `python/gui_components/widget_factory_pyqt5.py` vs `python/gui_components/widget_factory.py`

#### A. Class Structure and Initialization (`__init__`)

*   **Issue 2.A.1: Imports**
    *   **Original (`widget_factory.py`):** Imports `tkinter`, `ttk`, `customtkinter`, `ProgressPanel`, `FileOperationsProgressPanel`, `VLCPlayerWindow`.
    *   **PyQt5 (`widget_factory_pyqt5.py`):** Imports various `PyQt5.QtWidgets`, `PyQt5.QtCore`, `PyQt5.QtGui`. Does not import other custom components directly as its role is more foundational widget creation.
    *   **Discrepancy/Issue:** Appropriate changes for PyQt5. The PyQt5 factory focuses on creating basic Qt widgets, not complex composite components like `ProgressPanel` which would be separate classes.
    *   **Required Action:** None. This is a structural difference due to framework change.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.A.2: `__init__(self, app_instance)`**
    *   **Original:** Stores `app_instance`.
    *   **PyQt5:** Stores `app_instance`. Initializes `icon_cache` and calls `_load_icons()`.
    *   **Discrepancy/Issue:** PyQt5 version adds icon caching, which is a good enhancement for performance and management.
    *   **Required Action:** Ensure `_load_icons()` correctly finds the `icons` directory relative to the project structure.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.A.3: `_load_icons()` and `get_icon()` (New in PyQt5)**
    *   **Context:** Methods for loading and retrieving `QIcon` objects.
    *   **PyQt5:** `_load_icons` defines a dictionary of icon names to filenames and loads them from an `icons` directory. `get_icon` retrieves a cached icon.
    *   **Discrepancy/Issue:** This is a new, beneficial feature for PyQt5.
    *   **Required Action:**
        *   Verify the path to the `icons` directory: `os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "icons")`. This assumes `widget_factory_pyqt5.py` is in `python/gui_components/`.
        *   Ensure all necessary icons are listed in `icon_files` and present in the `icons` directory.
        *   Consider adding more icons if used elsewhere (e.g., for message boxes, specific actions).
    *   **Priority:** Medium
    *   **Status:** Open

#### B. Main Widget Creation Method (`create_widgets`)

*   **Issue 2.B.1: `create_widgets(self)`**
    *   **Original:** Main method that called sub-methods to create all major UI sections (`_create_top_control_frame`, `_create_main_resizable_layout`, etc.) and configured app grid.
    *   **PyQt5:** Contains a `pass` statement. Comments indicate that in PyQt5, widgets are created in the main app's `_create_ui` method and this method is for compatibility.
    *   **Discrepancy/Issue:** This is a significant structural change. The original `WidgetFactory` was responsible for orchestrating the creation of the entire UI. The PyQt5 `WidgetFactoryPyQt5` is more of a utility class providing helper methods to create individual styled widgets, and the main app (`CleanIncomingsApp`) handles the layout and composition.
    *   **Required Action:** This is a design choice. Confirm that all UI elements previously created by the Tkinter `WidgetFactory` are now correctly created and managed within `CleanIncomingsApp._create_ui` and its sub-methods, potentially using helper methods from `WidgetFactoryPyQt5`.
    *   **Priority:** N/A (Design difference)
    *   **Status:** Resolved (by architectural change)

#### C. Specific Widget Creation Helper Methods

*   **Issue 2.C.1: Icon Path Helper (`get_icon_path` - New in PyQt5)**
    *   **Context:** Helper to find icon files, trying various name patterns.
    *   **PyQt5:** Takes `icon_name` and `size`, constructs variations, and checks for existence in the `icons` directory.
    *   **Discrepancy/Issue:** Useful utility. Complements `_load_icons` for cases where direct path might be needed or for icons not pre-cached (though `_load_icons` seems to be the primary mechanism now).
    *   **Required Action:** Ensure consistency with `_load_icons`. If all icons are pre-cached, this might be less used or could be an internal helper for `_load_icons` if dynamic loading was intended.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.2: `create_icon_button` (New in PyQt5, but similar to Tkinter's implicit icon usage)**
    *   **Context:** Creates a `QPushButton` with text and an optional icon.
    *   **PyQt5:** Takes `parent`, `text`, `icon_name`, `callback`, and `**kwargs` (for `width`, `height`, `object_name`). Uses `get_icon_path` to set icon.
    *   **Discrepancy/Issue:** This is a generic button creation method. The original Tkinter factory often configured icons directly on `ctk.CTkButton` using `image=self.app.theme_manager.get_icon_image(...)`.
    *   **Required Action:** Determine if this generic `create_icon_button` is actively used or if the more specific `create_accent_button` and `create_compact_button` (which use the `icon_cache`) are preferred. If used, ensure `get_icon_path` logic is robust.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 2.C.3: `create_accent_button`, `create_compact_button` (New in PyQt5)**
    *   **Context:** Create styled `QPushButton` instances.
    *   **PyQt5:** `create_accent_button` and `create_compact_button` set object names ("accent", "compact") for styling via QSS. They use `get_icon` (from cache) and support tooltips, min/max widths.
    *   **Discrepancy/Issue:** These are good additions for consistent styling, replacing the manual configuration of `ctk.CTkButton` properties.
    *   **Required Action:** Verify that the object names "accent" and "compact" are correctly targeted in the QSS theme file (`apply_nuke_theme`). Ensure icons are displayed correctly.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.4: `create_header_label` (New in PyQt5)**
    *   **Context:** Creates a `QLabel` styled as a header.
    *   **PyQt5:** Sets object name "header", point size 14, bold.
    *   **Discrepancy/Issue:** Good for consistent header styling.
    *   **Required Action:** Verify QSS styling for `QLabel#header` if any specific styling beyond font is intended.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.5: `create_group_box` (New in PyQt5)**
    *   **Context:** Creates a `QGroupBox` with a specified layout.
    *   **PyQt5:** Takes `title` and `layout_type` (vertical, horizontal, grid). Sets margins and spacing.
    *   **Discrepancy/Issue:** Useful for organizing UI sections, replacing `ctk.CTkFrame` used as a container with a title.
    *   **Required Action:** Ensure this is used effectively in `app_gui_pyqt5.py` to structure the UI.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.6: `create_tree_widget` (Generic Tree - PyQt5) vs. Specific Trees (Tkinter)**
    *   **Original:** Created `source_tree` and `preview_tree` directly within `WidgetFactory` methods (`_create_source_tree_section`, `_create_preview_section`) with specific configurations.
    *   **PyQt5 (`create_tree_widget`):** A generic `QTreeWidget` creator. Takes `parent`, `columns`, `first_column_width`, `column_widths`, `multi_select`.
    *   **Discrepancy/Issue:** The generic `create_tree_widget` is less used. Instead, `widget_factory_pyqt5.py` has `create_source_tree()` and `create_preview_tree()` which are more specific and align better with the original's direct creation approach.
    *   **Required Action:** The generic `create_tree_widget` might be redundant if `create_source_tree` and `create_preview_tree` cover all needs. Evaluate its necessity.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.7: `create_source_tree` and `create_preview_tree` (Specific Trees - PyQt5)**
    *   **Context:** Create the main application tree views.
    *   **PyQt5:** These methods create `QTreeWidget` instances with predefined columns, header resize modes, and column widths. They also add compatibility methods (`get_children`, `delete`) to the tree instances.
    *   **Discrepancy/Issue:**
        *   **Columns:** `create_source_tree` columns: "Name", "Type", "Size". Original Tkinter source tree had similar implicit columns.
        *   `create_preview_tree` columns: "☐", "File/Sequence Name", "Task", "Asset", "New Destination Path", "Matched Tags". Original Tkinter preview tree had: "filename", "task", "asset", "new_path", "tags", with checkbox implicitly part of item data.
        *   **Compatibility Methods:** Adding `get_children` and `delete` directly to tree instances is a way to maintain some API similarity with Tkinter's `Treeview.get_children()` and `Treeview.delete()`. This is primarily for the `TreeManager` if it expects these methods.
    *   **Required Action:**
        *   Verify column names, order, and resize modes match functional requirements and provide a good user experience.
        *   Confirm that `TreeManagerPyQt5` correctly uses these trees and their compatibility methods if needed, or if it has been adapted to use standard `QTreeWidget` API.
        *   The checkbox column "☐" in `preview_tree` needs a mechanism to display and interact with actual checkboxes (e.g., using `QTreeWidgetItem.setCheckState` or a delegate).
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 2.C.8: Tree Helper Methods (`clear_tree_widget`, `add_tree_item`, `get_tree_selection`, `set_tree_selection` - PyQt5)**
    *   **Context:** Utility functions for manipulating `QTreeWidget`.
    *   **PyQt5:**
        *   `clear_tree_widget`: Calls `tree_widget.clear()`.
        *   `add_tree_item`: Creates `QTreeWidgetItem` and sets text for multiple columns from a `values` dictionary. The column mapping (0 to 5 for name, status, path, type, size, date_modified) is generic and might not align with the specific columns of `source_tree` or `preview_tree` if this method is intended for them.
        *   `get_tree_selection`: Returns `tree_widget.selectedItems()`.
        *   `set_tree_selection`: Clears selection and selects specified items.
    *   **Discrepancy/Issue:**
        *   `add_tree_item` is problematic. The fixed indexing `item.setText(0, ...)` `item.setText(1, ...)` etc., assumes a specific column order and count (6 columns). This will not work correctly for `source_tree` (3 columns) or `preview_tree` (6 columns but different meanings, e.g., column 0 is checkbox).
        *   The original Tkinter `TreeManager` handled item creation with specific data mapping.
    *   **Required Action:**
        *   Refactor `add_tree_item`. It should either:
            *   Be made more generic (e.g., take a list of strings for column texts).
            *   Be removed if `TreeManagerPyQt5` handles item creation and population directly using `QTreeWidgetItem` API, which is more flexible and type-safe.
            *   Specialized versions for `source_tree` and `preview_tree` should be created if a factory method is desired.
        *   `clear_tree_widget`, `get_tree_selection`, `set_tree_selection` are generally fine utilities.
    *   **Priority:** High (for `add_tree_item`)
    *   **Status:** Open

*   **Issue 2.C.9: `create_resizable_layout` (PyQt5) vs. `PanedWindow` (Tkinter)**
    *   **Original:** Used `ttk.PanedWindow` for resizable layouts, configured in `_create_main_resizable_layout`.
    *   **PyQt5:** `create_resizable_layout` creates a `QSplitter`.
    *   **Discrepancy/Issue:** `QSplitter` is the correct PyQt5 equivalent. This method is used in `app_gui_pyqt5.py`'s `_create_main_layout`.
    *   **Required Action:** None. Correct usage.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.C.10: `create_frame` (PyQt5) vs. `ctk.CTkFrame` (Tkinter)**
    *   **Original:** `ctk.CTkFrame` was used extensively for layout and grouping.
    *   **PyQt5:** `create_frame` creates a basic `QFrame`. Can set `object_name`.
    *   **Discrepancy/Issue:** `QFrame` is a basic container. For titled groups, `create_group_box` is preferred. This generic `create_frame` is fine for simple non-styled containers.
    *   **Required Action:** Ensure it's used appropriately where a simple `QFrame` is needed, and `QGroupBox` is used for titled sections.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 2.C.11: `create_label` (PyQt5) vs. `ctk.CTkLabel` (Tkinter)**
    *   **Original:** `ctk.CTkLabel` supported text, image, compound, font.
    *   **PyQt5:** `create_label` creates `QLabel`. Supports `text_content`, `parent`, `icon_name`, `bold`, `font_size`, `object_name`. The icon part uses `label.setPixmap(icon.pixmap(QSize(16, 16)))`. The comment correctly notes that a true "compound left" effect like CTkLabel needs a more complex setup.
    *   **Discrepancy/Issue:** Basic label creation is fine. The compound icon/text is a known limitation of simple `QLabel` usage if direct CTkLabel equivalence is desired.
    *   **Required Action:** For labels needing icons next to text (compound effect), `app_gui_pyqt5.py` should use a `QHBoxLayout` with a `QLabel` for the icon and another `QLabel` for text, or a custom widget if this pattern is frequent.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 2.C.12: `create_line_edit` (PyQt5) vs. `ctk.CTkEntry` (Tkinter)**
    *   **Original:** `ctk.CTkEntry` used for text input.
    *   **PyQt5:** `create_line_edit` creates `QLineEdit`. Supports `placeholder`, `object_name`.
    *   **Discrepancy/Issue:** Correct equivalent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.C.13: `create_combo_box` (PyQt5) vs. `ctk.CTkComboBox` / `ctk.CTkOptionMenu` (Tkinter)**
    *   **Original:** `ctk.CTkComboBox` or `ctk.CTkOptionMenu` used for dropdowns.
    *   **PyQt5:** `create_combo_box` creates `QComboBox`. Supports `items`, `width`, `object_name`.
    *   **Discrepancy/Issue:** Correct equivalent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.C.14: `create_text_edit` (PyQt5) vs. `ctk.CTkTextbox` (Tkinter)**
    *   **Original:** `ctk.CTkTextbox` used for multi-line text areas (e.g., log display).
    *   **PyQt5:** `create_text_edit` creates `QTextEdit`. Supports `read_only`, `object_name`.
    *   **Discrepancy/Issue:** Correct equivalent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.C.15: `create_progress_bar` (PyQt5) vs. `ctk.CTkProgressBar` (Tkinter)**
    *   **Original:** `ctk.CTkProgressBar` used.
    *   **PyQt5:** `create_progress_bar` creates `QProgressBar`. Supports `minimum`, `maximum`, `object_name`.
    *   **Discrepancy/Issue:** Correct equivalent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 2.C.16: `create_checkbox` (PyQt5) vs. `ctk.CTkCheckBox` (Tkinter)**
    *   **Original:** `ctk.CTkCheckBox` used.
    *   **PyQt5:** `create_checkbox` creates `QCheckBox`. Supports `text`, `object_name`.
    *   **Discrepancy/Issue:** Correct equivalent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

#### D. Compatibility Methods (Tkinter-style operations)

*   **Issue 2.D.1: `configure_widget`, `pack_widget`, `grid_widget` (New in PyQt5 for compatibility)**
    *   **Context:** These methods attempt to provide a Tkinter-like API for widget configuration and layout.
    *   **PyQt5:**
        *   `configure_widget`: Tries to set text, enabled state, or items (for combobox-like widgets).
        *   `pack_widget`: Adds widget to layout using `addWidget` or `addLayout`.
        *   `grid_widget`: Adds widget to layout using `addWidget` (doesn't actually use grid parameters like row/column).
    *   **Discrepancy/Issue:**
        *   These are shims. While they might help in a very direct porting phase, relying on them long-term is not ideal as PyQt5 has its own layout and widget property system.
        *   `grid_widget` is misleading as it doesn't use grid features.
        *   The main application `app_gui_pyqt5.py` seems to be using direct PyQt5 layout methods (`QHBoxLayout`, `QVBoxLayout`, `addWidget`, etc.) and widget property setters, which is the correct approach.
    *   **Required Action:**
        *   Identify if these compatibility methods are actually used anywhere. If `app_gui_pyqt5.py` and other components are using native PyQt5 APIs, these compatibility methods can be deprecated or removed to avoid confusion and encourage idiomatic PyQt5 code.
        *   If they are used, ensure their limited functionality is understood and doesn't cause issues.
    *   **Priority:** Medium
    *   **Status:** Open

#### E. Missing Original WidgetFactory Methods

Many methods from the original `WidgetFactory` were responsible for creating entire sections of the UI (e.g., `_create_top_control_frame`, `_create_main_resizable_layout`, `_create_source_tree_section`, `_create_preview_section`, `_create_progress_panel_section`, `_create_bottom_sections`).

*   **Issue 2.E.1: Absence of High-Level UI Section Creation Methods**
    *   **Discrepancy/Issue:** As noted in 2.B.1, these have been moved to `CleanIncomingsApp` in the PyQt5 version. This is an architectural shift.
    *   **Required Action:** This is by design. The analysis of these UI sections is covered under `app_gui_pyqt5.py` (Issues 1.C.x).
    *   **Priority:** N/A
    *   **Status:** Resolved (by architectural change)

#### F. Tkinter-Specific Helper Methods (Not Ported - Correctly)

The original `WidgetFactory` had methods like `_select_source_folder`, `_select_destination_folder`, `_validate_folder_entries`, `_open_settings_window`, `_on_sort_change`, `_toggle_sort_direction`, `_on_filter_change`, `_on_column_click`, `_show_all_sequences`, `_select_all_sequences`, `_select_all_files`, `_clear_selection`, `_on_tree_selection_change`, `_show_context_menu`, `_on_source_tree_open`, `_on_source_tree_close`, `_create_progress_panel_section`, `_create_bottom_sections`, `_create_log_display_section`, `_create_status_bar_section`.

*   **Issue 2.F.1: Absence of Event Handlers and UI Logic Methods**
    *   **Discrepancy/Issue:** These methods contained UI logic and event handling, which are correctly placed within the main application class (`CleanIncomingsApp`) in an MVC-like pattern, rather than in a widget factory.
    *   **Required Action:** None for `WidgetFactoryPyQt5`. Their presence and correctness are analyzed as part of `app_gui_pyqt5.py`.
    *   **Priority:** N/A
    *   **Status:** Resolved (by architectural change)

---

### 3. GUI Components: `python/gui_components/settings_window_pyqt5.py` (Standalone Analysis)

*   **Note:** The original Tkinter file `python/gui_components/settings_window.py` was not accessible for direct comparison. This analysis is based on the PyQt5 file alone.

#### A. Overall Structure and Purpose
*   **`SettingsWindow(QDialog)`:** Provides a tabbed interface for application settings: General, Appearance, Normalization Rules, Profile Management (placeholder), and Advanced.
*   **Interaction:** Uses an injected `settings_manager` for most settings but handles `patterns.json` and `profiles.json` I/O directly.
*   **Signal:** Emits `settings_changed` when settings are applied/saved.

#### B. Key Functionality by Tab
*   **General Settings:** Default source/destination folders, scan on startup, max concurrent operations.
*   **Appearance Settings:** UI theme (placeholder items), font size, widget corner radius.
*   **Normalization Rules:** Direct `QTextEdit` for `patterns.json` and `profiles.json`.
*   **Profile Management:** Placeholder label, indicating future development needed.
*   **Advanced Settings:** Debug logging, temporary file path.

#### C. Settings Persistence
*   Most settings are loaded/saved via the `settings_manager`.
*   `patterns.json` and `profiles.json` are read/written directly by `SettingsWindow`.

#### D. Standalone Test (`if __name__ == '__main__':`)
*   Includes a `MockSettingsManager` and setup for isolated testing, which is good practice.

#### E. Potential Issues and Areas for Improvement

*   **Issue 3.S.1: Direct JSON File Handling in UI Class**
    *   **Context:** `SettingsWindow` directly reads and writes `patterns.json` and `profiles.json`.
    *   **Discrepancy/Issue:** Mixes UI responsibilities with data persistence. The `SettingsManager` (or a dedicated `ConfigManager`) should ideally handle all configuration file I/O.
    *   **Required Action:** Refactor to move `patterns.json` and `profiles.json` I/O into the `SettingsManager` or a relevant configuration management class. `SettingsWindow` should then use the manager's methods to get/set this data.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 3.S.2: JSON Validation and Error Handling for Rule Editors**
    *   **Context:** `QTextEdit` for `patterns.json` and `profiles.json` allows free-form text. Saving writes this text directly.
    *   **Discrepancy/Issue:** Invalid JSON could be saved, potentially crashing the application later. Current error handling is basic.
    *   **Required Action:** Implement robust JSON validation (e.g., using `json.loads()` in a try-except) *before* saving. Provide specific feedback to the user if JSON is invalid. Consider if a more structured editor (e.g., `json_pattern_editor_pyqt5.py`) or dedicated UI is needed.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 3.S.3: Placeholder for Profile Management Tab**
    *   **Context:** The "Profile Management" tab is currently a placeholder.
    *   **Discrepancy/Issue:** Core functionality for user-friendly profile management (list, add, edit, delete) is missing.
    *   **Required Action:** Implement the Profile Management tab UI and logic, interacting with `SettingsManager` or `ConfigManager` for profile data. This might involve integrating `profile_editor_pyqt5.py`.
    *   **Priority:** High (assuming this was a feature in the original application)
    *   **Status:** Open

*   **Issue 3.S.4: Theme Management Integration**
    *   **Context:** The theme combobox in the "Appearance" tab has hardcoded placeholder items.
    *   **Discrepancy/Issue:** Does not integrate with a dynamic `ThemeManager`.
    *   **Required Action:** Populate the theme combobox with themes available from the application's `ThemeManager`. Ensure applying/saving a theme change correctly triggers the `ThemeManager` to update the application's appearance.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 3.S.5: Review Hardcoded Default Values and Ranges**
    *   **Context:** Some UI elements (e.g., spin boxes for font size, max operations) have hardcoded default values or input ranges.
    *   **Discrepancy/Issue:** May lead to inconsistencies if these values are defined or need to be managed elsewhere.
    *   **Required Action:** Ensure these defaults and ranges are sensible. If they are (or should be) defined as constants or defaults within the `SettingsManager` or a global application config, prefer using those definitions to maintain a single source of truth.
    *   **Priority:** Low
    *   **Status:** Open

---
