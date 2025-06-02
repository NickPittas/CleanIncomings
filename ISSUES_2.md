# PyQt5 Conversion: Issues and Discrepancies Log (Part 2)

This document continues tracking for the PyQt5 conversion of CleanIncomings.

---

### 5. GUI Components: `python/gui_components/json_editors/profiles_editor_window_pyqt5.py` vs `python/gui_components/json_editors/profiles_editor_window.py`

*   **Note:** The PyQt5 version (`profiles_editor_window_pyqt5.py`) is a significantly more advanced and feature-rich editor compared to the Tkinter version (`profiles_editor_window.py`). The Tkinter version appears to be a simpler tab-based editor relying on a `ProfileTab` class, while the PyQt5 version is a standalone, complex dialog with a dedicated UI for managing profiles and their rules.

#### A. Core Functionality and UI Structure
*   **Issue 5.A.1: UI Framework and Window Management**
    *   **Context:** Transition from Tkinter/CustomTkinter to PyQt5.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Uses `ctk.CTkToplevel` for the window. Manages tabs for each profile using a `ProfileTab` helper class.
        *   **PyQt5:** Uses `QDialog`. Features a two-pane layout (profile list on the left, profile details/rules on the right) using `QSplitter`. Includes a dedicated `FolderRuleDialog` for editing individual rules.
    *   **Enhancement (PyQt5):** The PyQt5 version provides a much more comprehensive and user-friendly interface for profile management.
    *   **Required Action:** None. The PyQt5 design is a significant improvement.
    *   **Priority:** N/A (Enhancement)
    *   **Status:** Resolved

*   **Issue 5.A.2: Profile Representation and Editing**
    *   **Context:** How profiles and their folder rules are displayed and edited.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Relies on `ProfileTab` to display and manage the rules for a single profile. The main window manages multiple `ProfileTab` instances.
        *   **PyQt5:**
            *   Displays a list of all profiles in a `QListWidget`.
            *   When a profile is selected, its folder rules are displayed in a `QTreeWidget` with columns for Priority, Folder Rule, Patterns, and Actions.
            *   Provides buttons for adding, duplicating, renaming, and deleting profiles.
            *   Provides buttons for adding, editing, deleting, and reordering (move up/down) folder rules for the selected profile.
            *   Uses a separate `FolderRuleDialog` for a structured way to edit the `folderRule` string, `priority`, and associated `patterns` (via checkboxes).
    *   **Required Action:** None. The PyQt5 approach is far more detailed and user-friendly.
    *   **Priority:** N/A (Enhancement)
    *   **Status:** Resolved

#### B. Data Handling (Loading, Saving, In-UI Changes)
*   **Issue 5.B.1: Data Loading (`profiles.json`)**
    *   **Context:** Loading profile configurations.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Uses a shared utility `load_json_file`. Also loads `patterns.json` for reference within `ProfileTab`.
        *   **PyQt5:** Loads `profiles.json` directly within its `load_profiles` method. Includes default profile data if the file is missing or loading fails. Provides user feedback via `QMessageBox` on load errors.
    *   **Required Action:** The PyQt5 direct loading is acceptable for a dedicated editor. Ensure default profile data is sensible.
    *   **Priority:** Low
    *   **Status:** Resolved

*   **Issue 5.B.2: Data Saving (`profiles.json`)**
    *   **Context:** Saving changes back to `profiles.json`.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Uses a shared utility `save_json_file` and `clean_profiles_data` before saving. Has an `on_save_callback`.
        *   **PyQt5:** Saves `self.profiles_data` (which is updated in-memory by UI operations) directly to `profiles.json` using `json.dump`. Emits a `profiles_changed` signal and calls an `on_save_callback` if provided. Provides user feedback via `QMessageBox`.
    *   **Missing Feature (PyQt5):** The PyQt5 version does not appear to use an equivalent of Tkinter's `clean_profiles_data` before saving. This could be a regression if that utility performed important cleaning (e.g., removing empty rules, ensuring type correctness, sorting by priority).
    *   **Required Action:** Investigate what `clean_profiles_data` did in the Tkinter version and implement equivalent data cleaning in the PyQt5 `save_profiles` method if necessary.
    *   **Priority:** Medium (for data cleaning)
    *   **Status:** Open

*   **Issue 5.B.3: In-Memory Data Management**
    *   **Context:** How changes made in the UI are reflected in the data to be saved.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `ProfileTab` instances likely modify a shared `self.profiles_data` dictionary passed from the main editor window.
        *   **PyQt5:** UI actions (add/edit/delete profile, add/edit/delete/move rule) directly modify `self.profiles_data` dictionary.
    *   **Required Action:** Ensure all UI operations correctly and consistently update `self.profiles_data` to reflect the user's intent before saving.
    *   **Priority:** Medium
    *   **Status:** Open (Requires thorough testing of all edit operations)

#### C. Profile Management Operations (Add, Duplicate, Rename, Delete)
*   **Issue 5.C.1: Profile Operations UI and Logic**
    *   **Context:** User actions for managing the list of profiles.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Has an "Add Profile" button. Deletion and renaming are likely handled within each `ProfileTab` or via context menus/buttons not immediately visible in `ProfilesEditorWindow` itself.
        *   **PyQt5:** Provides dedicated buttons for "Add Profile", "Duplicate Profile", "Rename Profile", and "Delete Profile". Uses `QInputDialog` for naming new/renamed profiles. Includes confirmation dialogs for deletion and checks for duplicate names or deleting the last profile.
    *   **Required Action:** The PyQt5 implementation is comprehensive. Test all profile operations for robustness and correct data updates.
    *   **Priority:** Low (Testing)
    *   **Status:** Resolved (Functionality present, pending testing)

#### D. Folder Rule Management (Add, Edit, Delete, Reorder)
*   **Issue 5.D.1: Folder Rule Operations UI and Logic**
    *   **Context:** User actions for managing folder rules within a selected profile.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Likely handled within the `ProfileTab` class, details not visible in `ProfilesEditorWindow`.
        *   **PyQt5:** Provides buttons for "Add Rule", "Edit Rule", "Delete Rule", "Move Up", "Move Down". Uses `FolderRuleDialog` for adding/editing. Updates rule priorities automatically when reordering.
    *   **Required Action:** The PyQt5 implementation is comprehensive. Test all rule operations, including priority updates and interaction with `FolderRuleDialog`.
    *   **Priority:** Medium (Testing and ensuring data integrity)
    *   **Status:** Open

#### E. `FolderRuleDialog` (New in PyQt5)
*   **Issue 5.E.1: Rule Editing Interface**
    *   **Context:** Dialog for creating and editing individual folder rules.
    *   **PyQt5:** Provides fields for `folderRule` (string), `priority` (string, converted to int), and checkboxes for selecting applicable `patterns` (e.g., "shotPatterns", "taskPatterns"). Includes help text for template variables.
    *   **Discrepancy/Issue:** This is a new, dedicated UI component that significantly improves rule editing compared to potentially direct JSON editing or simpler forms in Tkinter.
    *   **Required Action:**
        *   Ensure priority is handled as an integer correctly.
        *   Verify that the list of available pattern checkboxes is comprehensive and matches the system's capabilities.
        *   Test data loading into and retrieval from the dialog.
    *   **Priority:** Low (Testing)
    *   **Status:** Resolved (Functionality present, pending testing)

#### F. Error Handling and User Feedback
*   **Issue 5.F.1: User Messages and Confirmations**
    *   **Context:** Informing the user and asking for confirmation.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Uses `tkinter.messagebox`.
        *   **PyQt5:** Uses `QMessageBox` for errors, warnings, info, and confirmations. Uses `QInputDialog` for text input.
    *   **Required Action:** Ensure messages are clear and appropriate for each situation.
    *   **Priority:** Low
    *   **Status:** Resolved

#### G. Integration with Main Application / Settings
*   **Issue 5.G.1: Invocation and Signal/Callback**
    *   **Context:** How this editor is opened and how it notifies changes.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Instantiated with `config_dir` and an `on_save_callback`.
        *   **PyQt5:** Instantiated with `parent`, `config_dir`, and an `on_save_callback`. Emits `profiles_changed` signal upon successful save.
    *   **Required Action:** Ensure the main application (`app_gui_pyqt5.py`) or `SettingsWindowPyQt5` correctly instantiates this editor and connects to the `profiles_changed` signal if live updates are needed after saving profiles.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 5.G.2: (Moved from ISSUES.md - Issue 3.S.3) Placeholder for Profile Management Tab in `SettingsWindowPyQt5`**
    *   **Context:** The "Profile Management" tab in `SettingsWindowPyQt5` is currently a placeholder.
    *   **Discrepancy/Issue:** Core functionality for user-friendly profile management (list, add, edit, delete) is missing from the main settings window if this advanced editor is not used or is meant to be launched from there.
    *   **Required Action:** Decide the integration strategy:
        1.  Replace the placeholder tab in `SettingsWindowPyQt5` with a button to launch this `ProfilesEditorWindow`.
        2.  Alternatively, if a simpler, embedded profile editor is desired within `SettingsWindowPyQt5`, that would need to be developed, potentially reusing parts of `ProfilesEditorWindow` logic if feasible.
        Given the complexity and completeness of `ProfilesEditorWindowPyQt5`, launching it as a separate dialog is likely the best approach.
    *   **Priority:** High
    *   **Status:** Open

---

### 6. GUI Components: `python/gui_components/progress_panel_pyqt5.py` vs (`python/gui_components/progress_panel.py` and `python/gui_components/file_operations_progress.py`)

*   **Note:** The PyQt5 version (`progress_panel_pyqt5.py`) is currently a very basic widget. The Tkinter application had two distinct and more advanced progress panels: `progress_panel.py` for multi-stage task progress (like scanning) and `file_operations_progress.py` for detailed file transfer progress.

#### A. Core Functionality and UI Structure
*   **Issue 6.A.1: Feature Discrepancy - Multi-Stage Progress (`progress_panel.py`)**
    *   **Context:** The Tkinter `progress_panel.py` provided a sophisticated multi-stage progress display for operations like scanning. It showed distinct stages (e.g., Initialization, File Collection, Sequence Detection, Mapping, Final Processing) with icons, status text, and individual progress bars for relevant stages. It also included an overall progress bar.
    *   **Discrepancy/Issue (PyQt5):** `progress_panel_pyqt5.py` is a simple `QWidget` with one `QProgressBar`, one `QLabel` for status, and one `QLabel` for details. It lacks the concept of multiple stages, individual stage tracking, icons, or the rich UI of the Tkinter version.
    *   **Required Action:** Re-design and implement a PyQt5 equivalent of the multi-stage `ProgressPanel`. This will likely involve:
        *   A main widget (perhaps a `QDialog` or a custom `QWidget`).
        *   A way to define and manage multiple stages (name, icon, has_progress_bar).
        *   UI elements for each stage (icon label, title label, progress bar if applicable, details label).
        *   An overall progress bar.
        *   Methods to `start_stage`, `update_stage_progress`, `complete_stage`, `error_stage`, `reset`.
        *   Integration with `StatusManagerPyQt5` to receive progress updates for scanning/mapping operations.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 6.A.2: Feature Discrepancy - File Operations Progress (`file_operations_progress.py`)**
    *   **Context:** The Tkinter `file_operations_progress.py` provided a detailed window for tracking file copy/move operations. It showed:
        *   Overall batch progress (files completed/total, speed, ETA).
        *   A scrollable list of active individual file transfers (max 10 shown), each with its own name, progress bar, speed, and ETA.
        *   Controls like "Pause All", "Cancel All", "Hide".
    *   **Discrepancy/Issue (PyQt5):** The current `progress_panel_pyqt5.py` is not designed for this level of detail or for managing multiple concurrent file operations visually.
    *   **Required Action:** Design and implement a PyQt5 equivalent of the `FileOperationsProgressWindow`. This will likely involve:
        *   A `QDialog` or `QWidget` for the progress display.
        *   Overall summary section (progress bar, stats label for count, speed, ETA).
        *   A scrollable area (e.g., `QScrollArea` with a `QVBoxLayout`) to display individual file transfer widgets.
        *   A custom widget for each file transfer (showing name, progress bar, status/speed/ETA).
        *   Data structures to manage active transfers and their states.
        *   Methods to `start_operation_batch`, `add_transfer`, `update_transfer_progress`, `complete_transfer`.
        *   Placeholder controls for pause/cancel (actual implementation would be in `FileOperationsManager`).
        *   Integration with `FileOperationsManager` to receive updates on file transfers.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 6.A.3: UI Framework and Window Management**
    *   **Context:** Tkinter versions used `ctk.CTkToplevel` for popup windows.
    *   **Discrepancy/Issue (PyQt5):** The new progress panels should likely be `QDialog` instances (modal or non-modal as appropriate) or custom `QWidget`s that can be embedded or shown as popups.
    *   **Required Action:** Decide on the appropriate Qt base class and window behavior for the new progress panels.
    *   **Priority:** Medium
    *   **Status:** Open

#### B. Data Handling and UI Updates
*   **Issue 6.B.1: Rate Limiting and Error Handling in UI Updates (Tkinter `progress_panel.py`)**
    *   **Context:** The Tkinter `progress_panel.py` had logic for rate-limiting UI updates (`_can_update`, `_delayed_update`) and handling errors during updates (`_safe_update_display`, `update_errors`).
    *   **Discrepancy/Issue (PyQt5):** The simple `progress_panel_pyqt5.py` has no such considerations.
    *   **Required Action:** When implementing the new PyQt5 progress panels, incorporate robust UI update mechanisms:
        *   Use `QTimer` for delayed updates if rate limiting is needed.
        *   Ensure updates are thread-safe if progress signals come from worker threads (e.g., by emitting signals that are connected to slots in the UI thread).
        *   Include try-except blocks around UI update calls to prevent crashes due to unexpected data or widget states.
    *   **Priority:** Medium
    *   **Status:** Open

#### C. Integration with Managers
*   **Issue 6.C.1: Connecting to `StatusManagerPyQt5` and `FileOperationsManager`**
    *   **Context:** The Tkinter progress panels were driven by their respective managers.
    *   **Discrepancy/Issue (PyQt5):** The new PyQt5 progress panels will need to be instantiated and controlled by `StatusManagerPyQt5` (for scan/task progress) and `FileOperationsManager` (for file transfer progress).
    *   **Required Action:** Define clear interfaces (methods and signals) for the new progress panels so that the managers can easily update them. The managers will call methods like `update_progress`, `add_transfer`, etc., on the panel instances.
    *   **Priority:** High
    *   **Status:** Open

---

### 7. GUI Components: `python/gui_components/vlc_player_window_pyqt5.py` vs `python/gui_components/vlc_player_window.py`

*   **Note:** The PyQt5 version (`vlc_player_window_pyqt5.py`) was not found in the workspace. The analysis is based on the existing Tkinter version (`vlc_player_window.py`) and general expectations for a PyQt5 port.

#### A. Core Functionality and UI Structure (Tkinter `vlc_player_window.py`)
*   **Window Management:** Uses `ctk.CTkToplevel`.
*   **VLC Integration:**
    *   Initializes a VLC instance and media player.
    *   Sets the window handle (`winfo_id()`) for video display in a `ctk.CTkFrame`.
    *   Handles VLC events for time changes, position changes, end of media, play, pause, stop.
*   **UI Controls:**
    *   Video display frame.
    *   Media info label (filename, size, FPS, resolution).
    *   Seek slider with current time and total time labels.
    *   Control buttons with icons: Play/Pause, Stop, Frame Step Forward/Backward, Zoom In/Out, Reset Zoom.
*   **Features:**
    *   Loads and plays media specified by path.
    *   Basic playback controls (play, pause, stop, seek).
    *   Frame stepping.
    *   Video zoom functionality (mouse wheel and keyboard shortcuts Ctrl+Plus/Minus/0).
    *   Displays media information.
    *   Resource cleanup on closing.

#### B. Expected PyQt5 Implementation (`vlc_player_window_pyqt5.py` - To Be Created/Found)

*   **Issue 7.B.1: File Existence and Basic Structure**
    *   **Context:** The file `python/gui_components/vlc_player_window_pyqt5.py` is missing.
    *   **Discrepancy/Issue:** A core component for media playback is not yet ported or is misnamed/misplaced.
    *   **Required Action:**
        1.  Locate the PyQt5 VLC player window file if it exists under a different name or path.
        2.  If it doesn't exist, create `vlc_player_window_pyqt5.py`.
        3.  The new class should inherit from `QDialog` or `QWidget`.
        4.  It will need to initialize a VLC instance and media player, similar to the Tkinter version.
    *   **Priority:** Critical
    *   **Status:** Open

*   **Issue 7.B.2: Video Embedding in PyQt5**
    *   **Context:** Displaying VLC video output within a Qt widget.
    *   **Discrepancy/Issue:** Tkinter used `media_player.set_hwnd(video_frame.winfo_id())`. PyQt5 will require `media_player.set_hwnd(int(video_widget.winId()))` (on Windows) or `media_player.set_xwindow(int(video_widget.winId()))` (on Linux) where `video_widget` is a `QWidget` (often a `QFrame`).
    *   **Required Action:** Implement video embedding using the appropriate `winId()` of a dedicated `QWidget` for video display.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 7.B.3: UI Control Implementation**
    *   **Context:** Recreating the player controls using Qt widgets.
    *   **Discrepancy/Issue:** All UI elements (labels, slider, buttons) need to be created using `QLabel`, `QSlider`, `QPushButton`, etc., and laid out using Qt layouts (`QVBoxLayout`, `QHBoxLayout`).
    *   **Required Action:**
        *   Re-implement the media info display, seek bar, time labels, and control buttons.
        *   Load and apply icons to buttons (e.g., using `QIcon`). The icon loading mechanism from `widget_factory_pyqt5.py` could be leveraged or adapted.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 7.B.4: Event Handling**
    *   **Context:** Connecting VLC events to PyQt5 slots and UI updates.
    *   **Discrepancy/Issue:** VLC events (`MediaPlayerTimeChanged`, `MediaPlayerEndReached`, etc.) need to be attached to callback methods (slots in PyQt5 terms) that update the UI (slider position, button states, time labels).
    *   **Required Action:** Implement event handling for all relevant VLC events and connect them to methods that update the PyQt5 UI elements. Ensure thread safety if VLC events are emitted from a different thread (use Qt's signal/slot mechanism to pass data to the main UI thread).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 7.B.5: Feature Parity - Playback, Frame Stepping, Zoom**
    *   **Context:** Ensuring all functionalities from the Tkinter version are present.
    *   **Discrepancy/Issue:** Logic for play/pause, stop, seek, frame stepping (`media_player.set_time()`), and zoom (`media_player.video_set_scale()`) needs to be ported.
    *   **Required Action:**
        *   Implement methods for all playback controls.
        *   Implement zoom functionality, including mouse wheel events (`wheelEvent` on the video widget or window) and keyboard shortcuts (override `keyPressEvent`).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 7.B.6: Resource Management**
    *   **Context:** Releasing VLC resources when the window is closed.
    *   **Discrepancy/Issue:** The `_on_closing` method logic (stopping and releasing the media player and VLC instance) needs to be implemented in the PyQt5 window's `closeEvent` handler.
    *   **Required Action:** Implement proper resource cleanup in the `closeEvent` method of the PyQt5 VLC player window.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 7.B.7: Icon Loading**
    *   **Context:** The Tkinter version had its own `_load_icons` method.
    *   **Discrepancy/Issue:** The PyQt5 version should ideally use the centralized icon management from `WidgetFactoryPyQt5` or a similar shared mechanism if applicable, or implement its own robust icon loading.
    *   **Required Action:** Determine the best approach for icon loading and implement it. Ensure paths to icons are correct.
    *   **Priority:** Medium
    *   **Status:** Open

---

### 8. GUI Components: `python/gui_components/tree_manager_pyqt5.py` vs `python/gui_components/tree_manager.py`

#### A. Core Responsibilities and Initialization
*   **Issue 8.A.1: Initialization (`__init__`)**
    *   **Context:** Both classes initialize `app_instance`, `current_sort_column`, `sort_reverse`, `current_filter`, `selected_source_folder`, and `original_data`.
    *   **Discrepancy/Issue:** Largely consistent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

#### B. Source Tree Population (`populate_source_tree`)
*   **Issue 8.B.1: Method Signature and Logic**
    *   **Context:** Populating the source folder structure tree.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `populate_source_tree(self, items: List[Dict[str, Any]], base_path: str)`. Cleared tree using `self.app.source_tree.get_children()` and `delete()`. Sorted items (folders first). Had a nested recursive helper `insert_items_recursively` that handled icons from `ThemeManager` and formatted size. Skipped files. Used `iid=path`.
        *   **PyQt5:** `populate_source_tree(self, tree_data: List[Dict[str, Any]], base_path: str)`. Clears tree using `self.app.source_tree.clear()`. Creates a root item for `base_path`. Calls `_populate_tree_recursive`.
    *   **PyQt5 `_populate_tree_recursive(self, parent_item: QTreeWidgetItem, children: List[Dict[str, Any]])`:**
        *   Sets text for columns: Name, Type, Size.
        *   Stores full `child_data` using `child_item.setData(0, Qt.UserRole, child_data)`.
        *   Recursively calls itself for children.
    *   **Differences & Potential Issues (PyQt5):**
        *   The PyQt5 version's `populate_source_tree` expects `tree_data` which seems to be pre-structured for recursion, while Tkinter took a flat list `items` and built hierarchy. This implies the data source (likely `ScanManager`) might need to provide data differently.
        *   Icon handling from `ThemeManager` is missing in the PyQt5 `_populate_tree_recursive`. Tkinter version used `self.app.theme_manager.get_icon_text("folder_closed")`.
        *   The Tkinter version explicitly sorted items to show folders first. PyQt5's `_populate_tree_recursive` iterates as-is; sorting should happen before calling or within the data source.
        *   Tkinter version used the item's `path` as its `iid` in the tree. PyQt5 version doesn't explicitly set an `iid` in `_populate_tree_recursive` but relies on `QTreeWidgetItem` identity. `setData(0, Qt.UserRole, child_data)` is good for associating data.
        *   Tkinter version skipped files in the source tree. PyQt5 `_populate_tree_recursive` adds whatever `child_data` it receives. The `tree_data` structure given to `populate_source_tree` must already be filtered if files are to be excluded.
    *   **Required Action:**
        *   Clarify the expected structure of `tree_data` for `populate_source_tree` in PyQt5 and ensure `ScanManager` provides it correctly.
        *   Implement icon handling in `_populate_tree_recursive` using `ThemeManagerPyQt5` (if available and integrated) or `WidgetFactoryPyQt5.get_icon()`.
        *   Ensure sorting (folders first, then by name) is handled either in the data source or before calling `_populate_tree_recursive`.
        *   Confirm if files should be excluded from the source tree in the PyQt5 version, and if so, where this filtering occurs.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 8.B.2: Source Tree Selection Handling (`on_source_tree_selection`)**
    *   **Context:** Handling selection in the source tree to filter the preview tree.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `on_source_tree_selection(self, event=None)`. Got selection using `self.app.source_tree.selection()`. The `iid` (which was the path) was used for `set_source_folder_filter`.
        *   **PyQt5:** This method is missing in `tree_manager_pyqt5.py`. The source tree selection signal (`self.app.source_tree.itemSelectionChanged.connect(self.tree_manager.on_source_tree_selection_changed)`) would need to be connected in `app_gui_pyqt5.py`, and a corresponding slot like `on_source_tree_selection_changed(self)` implemented in `TreeManagerPyQt5`. This slot would need to get the selected item's path (likely from `item.data(0, Qt.UserRole)['path']`) to call `set_source_folder_filter`.
    *   **Required Action:**
        *   Implement `on_source_tree_selection_changed(self)` in `TreeManagerPyQt5`.
        *   This method should retrieve the selected `QTreeWidgetItem`, get its associated path data, and call `self.set_source_folder_filter(path)`.
        *   Ensure the connection is made in `app_gui_pyqt5.py`.
    *   **Priority:** High
    *   **Status:** Open

#### C. Preview Tree Population (`populate_preview_tree`)
*   **Issue 8.C.1: Method Signature and Item Creation**
    *   **Context:** Populating the preview tree with normalized file/sequence proposals.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `populate_preview_tree(self, normalized_file_list: List[Dict[str, Any]], source_path_base: str)`. Stored `normalized_file_list` as `self.original_data`. Called `_populate_preview_tree_internal`.
        *   **PyQt5:** `populate_preview_tree(self, proposals: List[Dict[str, Any]], base_path: str)`. Stores `proposals` as `self.original_data`. Clears tree. Iterates `proposals` to create `QTreeWidgetItem`s.
            *   Sets checkbox state: `item.setCheckState(0, Qt.Unchecked)`. Column 0 is for checkbox.
            *   Sets text for columns 1-5: Filename, Task, Asset, Dest Path, Matched Tags.
            *   Stores full proposal data: `item.setData(0, Qt.UserRole, proposal)`.
            *   Also stores an `item_id` (e.g., "item_0") in `self.app.preview_tree_item_data_map` and on the item itself (`item.setData(1, Qt.UserRole, item_id)`). This `item_id` mapping seems redundant if `Qt.UserRole` on column 0 already holds the full data.
    *   **Tkinter `_populate_preview_tree_internal(self, data: List[Dict[str, Any]])`:**
        *   Cleared tree and `self.app.preview_tree_item_data_map`.
        *   Iterated data, extracted filename, task, asset, new_path, tags.
        *   Used `_get_item_icon` for an icon string, prepended to filename.
        *   Formatted task and asset display with icons from `ThemeManager`.
        *   Used `item_id = item_data.get('id', original_path)` for `iid`.
        *   Applied tags for styling based on status (error, manual, unmatched).
        *   Inserted item with `text="☐"` (checkbox visual cue) and values. Stored `item_data` in `self.app.preview_tree_item_data_map`.
    *   **Differences & Potential Issues (PyQt5):**
        *   **Iconography:** PyQt5 version currently does not include icons for items in the preview tree (e.g., sequence icon, file type icon) nor for task/asset fields, unlike the Tkinter version which used `_get_item_icon` and `ThemeManager`.
        *   **Styling for Status:** Tkinter version applied tags (`'error'`, `'manual'`) for styling rows based on status. PyQt5 version does not show this. `QTreeWidgetItem` can be styled (e.g., `setForeground`, `setBackground`).
        *   **Checkbox Column:** PyQt5 correctly uses column 0 for a checkable state. Tkinter used `text="☐"` as a visual cue and likely managed selection state separately.
        *   **`preview_tree_item_data_map`:** PyQt5's use of an index-based `item_id` (e.g. "item_0", "item_1") for the map key and also storing it on `item.setData(1, Qt.UserRole, item_id)` seems overly complex. Storing the full `proposal` on `item.setData(0, Qt.UserRole, proposal)` is good. The map might not be strictly necessary if item data can always be retrieved from the `QTreeWidgetItem` itself. If the map is kept, using a unique ID from the `proposal` data (if available) would be more robust than an index.
    *   **Required Action:**
        *   Implement item icon display in the PyQt5 preview tree (column 1: Filename) using a similar logic to Tkinter's `_get_item_icon` and `ThemeManagerPyQt5` or `WidgetFactoryPyQt5.get_icon()`.
        *   Implement row styling (e.g., text color) based on item status (error, manual) in PyQt5.
        *   Re-evaluate the necessity and implementation of `self.app.preview_tree_item_data_map` in PyQt5. If kept, use a more robust key.
        *   Ensure `self.update_selection_stats()` is called after populating.
    *   **Priority:** Medium
    *   **Status:** Open

#### D. Sorting and Filtering (`_refresh_preview_tree`, `_apply_filter`, `_apply_sort`, `set_sort_order`, `set_filter`)
*   **Issue 8.D.1: Core Logic**
    *   **Context:** Refreshing the preview tree based on current sort/filter settings.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `_refresh_preview_tree` called `_filter_data` then `_sort_data` on `self.original_data`, then `_populate_preview_tree_internal`. `_sort_data` and `_filter_data` had detailed logic for different columns and filter types (all, sequences, files) and source folder filtering.
        *   **PyQt5:** `_refresh_preview_tree` calls `_apply_filter` then `_apply_sort` on `self.original_data`, then calls `self.populate_preview_tree` (which clears and re-adds all items).
            *   `_apply_filter`: Handles "all", "sequences", "files". Does *not* currently include the source folder filtering logic that Tkinter's `_filter_data` had.
            *   `_apply_sort`: Uses a `sort_key_map` dictionary to get lambda functions for sorting. This is a clean approach.
        *   `set_sort_order` and `set_filter` methods are similar in both, triggering `_refresh_preview_tree`.
    *   **Missing Feature (PyQt5):** Source folder-based filtering is not implemented in `_apply_filter`. Tkinter's `_filter_data` had:
        ```python
        if self.selected_source_folder:
            # ... logic to filter by item's source_path starting with self.selected_source_folder ...
        ```
    *   **Required Action:**
        *   Implement source folder filtering in `TreeManagerPyQt5._apply_filter` based on `self.selected_source_folder`. This is crucial for the source tree selection to affect the preview tree.
        *   Verify all sort keys in `_apply_sort` match the intended columns and data structure of proposals.
    *   **Priority:** High (for missing folder filter), Low (for sort key verification)
    *   **Status:** Open

#### E. Item Selection (`get_selected_items`, `select_all_items`, `clear_selection`, `update_selection_stats`, `on_tree_item_selection_changed`)
*   **Issue 8.E.1: Getting Selected Items**
    *   **Context:** Retrieving data for items selected (checked) in the preview tree.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `get_selected_items()` iterated `self.app.preview_tree.selection()` (which are tree item IDs) and used `self.app.preview_tree_item_data_map` to get the actual data.
        *   **PyQt5:** `get_selected_items()` iterates all top-level items in the `preview_tree`, checks `item.checkState(0) == Qt.Checked`, and retrieves data using `item.data(0, Qt.UserRole)`. This is correct for checkbox-based selection.
    *   **Required Action:** None. PyQt5 approach is appropriate for its checkbox model.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 8.E.2: Select All / Clear Selection**
    *   **Context:** Selecting all items of a type or clearing all selections.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `select_all_sequences()`, `select_all_files()`, `clear_selection()` manipulated `self.app.preview_tree.selection_add()` / `selection_remove()`.
        *   **PyQt5:** `select_all_items(self, item_type: str = "all")` and `clear_selection()` iterate tree items and use `item.setCheckState(0, Qt.Checked/Unchecked)`. `select_all_items` filters by `proposal_data.get('type')`. Both call `update_selection_stats()`.
    *   **Required Action:** None. PyQt5 approach is correct for its checkbox model.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 8.E.3: Updating Selection Stats and Action Button States**
    *   **Context:** Updating UI labels with selection counts and enabling/disabling action buttons.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** `update_action_button_states()` and `get_selection_stats()`. Stats included total, sequences, files, auto_mapped, manual_required.
        *   **PyQt5:** `update_selection_stats()` updates a label with `Selected: X of Y items`. `on_tree_item_selection_changed()` (intended to be connected to `preview_tree.itemSelectionChanged` or similar) calls `update_selection_stats()` and enables/disables copy, move, batch edit buttons based on `len(self.get_selected_items()) > 0`.
    *   **Missing Feature (PyQt5):** The detailed selection stats (sequences, files, auto_mapped, manual_required) from Tkinter's `get_selection_stats` are not replicated. The current PyQt5 `update_selection_stats` is simpler.
    *   **Required Action:**
        *   Decide if the detailed selection statistics are required in the PyQt5 version. If so, implement logic similar to Tkinter's `get_selection_stats` and update the `selection_stats_label` accordingly.
        *   Ensure `on_tree_item_selection_changed` is correctly connected to the `preview_tree`'s selection/check state change signal in `app_gui_pyqt5.py`. For checkboxes, this would typically be `itemChanged` signal, filtered for check state changes.
    *   **Priority:** Medium (for detailed stats if needed, and signal connection)
    *   **Status:** Open

#### F. Miscellaneous
*   **Issue 8.F.1: Tkinter-Specific Methods Not Ported (Correctly)**
    *   **Context:** Tkinter `TreeManager` had `sort_by_column` (for header click sorting) and `update_action_button_states` (tied to Tkinter button states).
    *   **Discrepancy/Issue:** These are handled differently in PyQt5. Header click sorting is typically done by connecting to `QHeaderView.sectionClicked`. Button state updates are in `on_tree_item_selection_changed`.
    *   **Required Action:** None. These are framework-specific adaptations.
    *   **Priority:** N/A
    *   **Status:** Resolved

*   **Issue 8.F.2: Debug Prints**
    *   **Context:** Both versions contain `print("[TREE_MANAGER_DEBUG] ...")` statements.
    *   **Discrepancy/Issue:** Useful for debugging but should ideally be replaced by a proper logging mechanism for release versions.
    *   **Required Action:** Consider integrating with a logging framework (e.g., Python's `logging` module) and removing or conditionalizing debug prints.
    *   **Priority:** Low
    *   **Status:** Open

---

### 9. Core Logic: `python/gui_components/scan_manager.py` vs `python/gui_components/scan_manager_tkinter_backup.py`

*   **Note:** The ScanManager is responsible for initiating scans, managing the scanning process (often in a separate thread), and handling the results to update the UI.

#### A. Initialization (`__init__`)
*   **Issue 9.A.1: Basic Attributes**
    *   **Context:** Both initialize `self.app`, `self.result_queue`, and `self.scan_thread`.
    *   **Discrepancy/Issue:** Consistent.
    *   **Required Action:** None.
    *   **Priority:** N/A
    *   **Status:** Resolved

#### B. Scan Initiation (`on_scan_button_click` / `refresh_scan_data`)
*   **Issue 9.B.1: Input Gathering and Validation**
    *   **Context:** Both methods retrieve `source_path`, `profile_name`, and `destination_root` from the app instance.
    *   **Discrepancy/Issue (PyQt5 `scan_manager.py`):**
        *   The PyQt5 version has placeholders for validation messages (e.g., `if not source_path: # Add message box`). Tkinter version used `self.app.status_label.configure(text=...)` and returned.
        *   Tkinter version checked `if not self.app.normalizer: self.app.status_label.configure(text="Normalizer not initialized."); return`. PyQt5 version has a placeholder.
    *   **Required Action (PyQt5):**
        *   Implement proper user feedback for missing inputs (source path, profile, destination root) using `QMessageBox.warning` or similar, then return if invalid.
        *   Implement the check for `self.app.normalizer` and provide user feedback if it's not initialized.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 9.B.2: Progress Indication and UI State**
    *   **Context:** Starting progress indication and disabling UI elements during scan.
    *   **Discrepancy/Issue:**
        *   **Tkinter:** Called `self.app.status_manager.start_scan_progress()`.
        *   **PyQt5:** Calls `self.app.status_manager.start_scan_progress()` and `self.app.refresh_btn.setEnabled(False)`.
    *   **Required Action:** Ensure all relevant UI elements (e.g., scan button itself, settings buttons) are appropriately disabled in the PyQt5 version during a scan and re-enabled afterwards. The `refresh_btn` is handled; check others.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 9.B.3: Threading and Queue**
    *   **Context:** Both versions use a `threading.Thread` to run the `_scan_worker` and a `queue.Queue` for results.
    *   **Discrepancy/Issue (PyQt5 `scan_manager.py`):**
        *   The PyQt5 version correctly initializes `self.result_queue = Queue()`.
        *   It starts the `threading.Thread` targeting `_scan_worker`.
        *   It calls `self._check_scan_queue()` which is intended to use a `QTimer` (as per typical Qt patterns, though `QTimer` import and usage is not shown in the provided snippet of `scan_manager.py` but is implied by `from PyQt5.QtCore import QTimer`).
        *   The `threading` module is not imported in the provided snippet of `scan_manager.py`.
    *   **Required Action (PyQt5):**
        *   Ensure `threading` is imported in `python/gui_components/scan_manager.py`.
        *   Verify the implementation of `_check_scan_queue` uses a `QTimer` to periodically check the `self.result_queue` without blocking the GUI, and that this timer is started correctly.
    *   **Priority:** Medium
    *   **Status:** Open

#### C. Scan Worker (`_scan_worker`)
*   **Issue 9.C.1: Core Scan Logic**
    *   **Context:** This method performs the actual scanning and normalization by calling `self.app.normalizer.scan_and_normalize_structure`.
    *   **Discrepancy/Issue (PyQt5 `scan_manager.py`):**
        *   The `_scan_worker` method is defined but its content is missing in the provided snippet.
        *   **Tkinter `_scan_worker`:** Called `self.app.normalizer.scan_and_normalize_structure` with `source_path`, `profile_name`, `destination_root`, and a `status_callback=self.update_scan_status`. It put the result or an error dictionary into `self.result_queue`.
    *   **Required Action (PyQt5):**
        *   Implement the body of `_scan_worker` in `python/gui_components/scan_manager.py`.
        *   It should call `self.app.normalizer.scan_and_normalize_structure(source_path, profile_name, destination_root, status_callback=self.update_scan_status)`. Note: The `status_callback` mechanism for `GuiNormalizerAdapter` in PyQt5 should use signals (see Issue 13.B.2). If `scan_and_normalize_structure` is adapted to emit signals directly, the callback might not be needed here, or `update_scan_status` might need to emit a signal.
        *   Place the result (or an error structure) into `self.result_queue`.
        *   Include `try-except` block to catch exceptions during the scan and put an error dictionary in the queue.
    *   **Priority:** High
    *   **Status:** Open

#### D. Queue Checking and Result Processing (`_check_scan_queue`)
*   **Issue 9.D.1: Retrieving and Processing Results**
    *   **Context:** This method, periodically called (e.g., by `QTimer` in PyQt5), checks the `result_queue` for data from the `_scan_worker` thread.
    *   **Discrepancy/Issue (PyQt5 `scan_manager.py`):**
        *   The `_check_scan_queue` method is defined but its content is missing in the provided snippet.
        *   **Tkinter `_check_scan_queue`:** Used `self.app.after(100, self._check_scan_queue)` for polling. Tried to get from `self.result_queue` with `block=False`. If data received:
            *   Called `self.app.status_manager.finish_scan_progress()`.
            *   Re-enabled scan button.
            *   If result was an error, showed it in status label and logged it.
            *   If successful, called `self.app.tree_manager.populate_source_tree` and `self.app.tree_manager.populate_preview_tree`.
            *   Updated status label.
    *   **Required Action (PyQt5):**
        *   Implement the body of `_check_scan_queue` in `python/gui_components/scan_manager.py`.
        *   It should use a `QTimer` (e.g., `self.scan_check_timer = QTimer(); self.scan_check_timer.timeout.connect(self._process_queue_results); self.scan_check_timer.start(100)`).
        *   Inside the timer's connected slot (`_process_queue_results`):
            *   Try to get data from `self.result_queue` (non-blocking).
            *   If data is present:
                *   Stop the timer or ensure it doesn't fire unnecessarily after completion/error.
                *   Call `self.app.status_manager.finish_scan_progress()`.
                *   Re-enable UI elements (e.g., `self.app.refresh_btn.setEnabled(True)`).
                *   If the result is an error, display it using `QMessageBox.critical` or update a status label, and log it.
                *   If successful, unpack `proposals` and `source_tree_data` from the result.
                *   Call `self.app.tree_manager.populate_source_tree(source_tree_data, source_path)`.
                *   Call `self.app.tree_manager.populate_preview_tree(proposals, source_path)`.
                *   Update status label (e.g., `self.app.status_label.setText(...)`).
            *   If no data, the timer will call it again.
    *   **Priority:** High
    *   **Status:** Open

#### E. Scan Status Update (`update_scan_status`)
*   **Issue 9.E.1: Callback for Normalizer**
    *   **Context:** This method is intended as a callback for `scan_and_normalize_structure` to provide real-time updates on which file/folder is being processed.
    *   **Discrepancy/Issue (PyQt5 `scan_manager.py`):**
        *   The `update_scan_status` method is defined but its content is missing.
        *   **Tkinter `update_scan_status`:** Updated `self.app.status_manager.update_scan_details(f"Scanning: {current_path}")`.
    *   **Required Action (PyQt5):**
        *   Implement the body of `update_scan_status`.
        *   It should call `self.app.status_manager.update_scan_details(f"Scanning: {current_path}")` or a similar method in `StatusManagerPyQt5`.
        *   **Important:** If this method is called directly from the worker thread (`_scan_worker` via `normalizer`), any UI updates within `StatusManagerPyQt5` must be thread-safe (e.g., by emitting a signal to the main thread).
    *   **Priority:** Medium
    *   **Status:** Open

#### F. Missing Imports and Placeholders
*   **Issue 9.F.1: Imports and Completeness**
    *   **Context:** The provided `python/gui_components/scan_manager.py` snippet is incomplete.
    *   **Discrepancy/Issue:** Missing `import threading`. The methods `_scan_worker`, `_check_scan_queue`, and `update_scan_status` are empty. Placeholders for error messages exist.
    *   **Required Action:** Complete the implementation of these methods as detailed above. Add necessary imports (`threading`, `QMessageBox` if used directly, etc.).
    *   **Priority:** High
    *   **Status:** Open

---

### 10. Core Logic: `python/gui_components/settings_manager_pyqt5.py` vs `python/gui_components/settings_manager_tkinter_backup.py`

*   **Note:** The SettingsManager is responsible for loading, saving, and applying application settings, including UI state like window geometry, pane positions, and selected values, as well as operational parameters.

#### A. Initialization (`__init__`)
*   **Issue 10.A.1: Basic Attributes**
    *   **Context:** Both initialize `self.app` (the main application instance) and `self.settings_file` (path to `user_settings.json`).
    *   **Discrepancy/Issue:** Consistent. The method for determining `settings_file` path (`Path(__file__).parent.parent.parent / "user_settings.json"`) assumes a specific directory structure relative to the `settings_manager.py` file. This might need to be more robust if the application is packaged or run from different locations (see Issue 15.B.2 regarding `ConfigManager` and `QStandardPaths`).
    *   **Required Action:** For now, this is consistent. Consider centralizing config path determination if a `ConfigManager` is fully implemented.
    *   **Priority:** Low
    *   **Status:** Resolved (for consistency, path robustness is a separate concern)

#### B. Loading Settings (`load_settings`)
*   **Issue 10.B.1: File Reading and Defaults**
    *   **Context:** Loading settings from `user_settings.json`.
    *   **Discrepancy/Issue (PyQt5 `settings_manager_pyqt5.py`):**
        *   The `load_settings` method is a stub (empty).
        *   **Tkinter `settings_manager_tkinter_backup.py`:**
            *   Checked if `settings_file` exists. If not, returned `_merge_with_defaults({})`.
            *   If exists, read JSON, handled `json.JSONDecodeError` by returning `_merge_with_defaults({})` and logging an error.
            *   Called `_merge_with_defaults(loaded_settings)`.
    *   **Required Action (PyQt5):**
        *   Implement `load_settings` in `settings_manager_pyqt5.py`.
        *   It should attempt to read `self.settings_file`.
        *   Handle potential `FileNotFoundError` and `json.JSONDecodeError` (or equivalent for the JSON library used, likely `json`).
        *   In case of error or if the file doesn't exist, it should return `self._merge_with_defaults({})`.
        *   If successful, it should return `self._merge_with_defaults(loaded_json_data)`.
        *   Ensure `json` module is imported.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 10.B.2: Merging with Defaults (`_merge_with_defaults`)
    *   **Context:** Ensuring that all necessary settings keys are present, using defaults if some are missing from the loaded file.
    *   **Discrepancy/Issue (PyQt5 `settings_manager_pyqt5.py`):**
        *   The `_merge_with_defaults` method is a stub.
        *   **Tkinter `settings_manager_tkinter_backup.py`:**
            *   Defined `default_settings` dictionary with keys like `theme`, `window_geometry`, `pane_positions`, `selected_profile`, `log_panel_collapsed`, `max_threads`, `process_timeout`.
            *   Iterated `default_settings`, if a key was not in `loaded_settings`, it was added from defaults.
    *   **Required Action (PyQt5):**
        *   Implement `_merge_with_defaults` in `settings_manager_pyqt5.py`.
        *   Define a `default_settings` dictionary appropriate for the PyQt5 version. This should include:
            *   `theme`: Default theme name (e.g., "default" or a specific QSS theme name).
            *   `window_geometry`: May need to store `pos().x()`, `pos().y()`, `size().width()`, `size().height()`.
            *   `splitter_sizes` (for `QSplitter` instead of Tkinter pane positions).
            *   `selected_profile`: Default profile name.
            *   `log_panel_collapsed`: Boolean.
            *   `max_threads`, `process_timeout`: If still relevant.
            *   Any other PyQt5 specific settings.
        *   Merge `loaded_settings` with these defaults, prioritizing loaded values but ensuring all default keys are present.
    *   **Priority:** High
    *   **Status:** Open

#### C. Saving Settings (`save_settings`, `save_current_state`)
*   **Issue 10.C.1: Writing to File (`save_settings`)**
    *   **Context:** Saving the provided settings dictionary to `user_settings.json`.
    *   **Discrepancy/Issue (PyQt5 `settings_manager_pyqt5.py`):**
        *   The `save_settings` method is a stub.
        *   **Tkinter `settings_manager_tkinter_backup.py`:**
            *   Opened `settings_file` in write mode.
            *   Used `json.dump(settings, f, indent=4)`.
            *   Handled `IOError` and logged an error.
    *   **Required Action (PyQt5):**
        *   Implement `save_settings` in `settings_manager_pyqt5.py`.
        *   It should write the `settings` dictionary to `self.settings_file` as JSON (e.g., using `json.dump` with `indent=4`).
        *   Handle potential `IOError` or other file writing exceptions.
        *   Ensure `json` module is imported.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 10.C.2: Saving Current Application State (`save_current_state`)**
    *   **Context:** Gathering the current UI state and other relevant settings from the application and then saving them.
    *   **Discrepancy/Issue (PyQt5 `settings_manager_pyqt5.py`):**
        *   The `save_current_state` method is a stub.
        *   **Tkinter `settings_manager_tkinter_backup.py`:**
            *   Called `self.app.settings_manager.get_current_ui_state()` (which seems like a circular call, likely meant `self.get_current_ui_state()`).
            *   Retrieved `max_threads`, `process_timeout` from `self.app` (if they exist there).
            *   Called `self.save_settings(current_settings)`.
        *   **Tkinter `get_current_ui_state()`:** Gathered `window_geometry`, `pane_positions` (from sashpos), `selected_profile`, `log_panel_collapsed`.
    *   **Required Action (PyQt5):**
        *   Implement `save_current_state` in `settings_manager_pyqt5.py`.
        *   It should gather current settings. This will involve creating a helper like `get_current_ui_state_pyqt5()` or integrating logic directly:
            *   `window_geometry`: `self.app.geometry()` (returns `QRect`, so store `x, y, width, height`).
            *   `splitter_sizes`: `self.app.main_splitter.sizes()` (if `main_splitter` is the name of the main `QSplitter`). Similarly for other splitters.
            *   `selected_profile`: `self.app.profile_combo.currentText()` (if `profile_combo` is the name).
            *   `log_panel_collapsed`: A boolean state, possibly from `self.app.log_dock_widget.isVisible()` or a custom flag.
            *   `theme`: `self.app.theme_manager.current_theme_name` (if `ThemeManager` stores this).
            *   Other settings like `max_threads`, `process_timeout` if they are managed by the app.
        *   Call `self.save_settings(gathered_settings)`.
    *   **Priority:** High
    *   **Status:** Open

#### D. Restoring UI State (`restore_ui_state` and helpers)
*   **Issue 10.D.1: Main Restore Logic (`restore_ui_state`)**
    *   **Context:** Applying loaded settings to the application's UI elements.
    *   **Discrepancy/Issue (PyQt5 `settings_manager_pyqt5.py`):**
        *   The `restore_ui_state` method is a stub.
        *   **Tkinter `settings_manager_tkinter_backup.py`:**
            *   Restored `window_geometry` using `self.app.geometry()`.
            *   Called helper methods: `_restore_profile_selection`, `_restore_pane_positions`, `_restore_log_panel_state`.
            *   Called `_apply_thread_settings`.
            *   Applied theme using `self.app.theme_manager.apply_theme()`.
    *   **Required Action (PyQt5):**
        *   Implement `restore_ui_state` in `settings_manager_pyqt5.py`.
        *   Restore window geometry: `self.app.setGeometry(x, y, width, height)` from saved settings.
        *   Call helper methods (to be implemented, see below): `_restore_profile_selection_pyqt5`, `_restore_pane_positions_pyqt5` (for splitters), `_restore_log_panel_state_pyqt5`.
        *   Call `_apply_thread_settings_pyqt5` (if applicable).
        *   Apply theme: `self.app.theme_manager.apply_theme(settings.get('theme'))` (or similar, depending on `ThemeManagerPyQt5` API).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 10.D.2: Helper - Restore Profile Selection (`_restore_profile_selection`)**
    *   **Discrepancy/Issue (PyQt5):** Stub method.
    *   **Tkinter:** Set `self.app.selected_profile_name.set(selected_profile)`. Updated profile details display.
    *   **Required Action (PyQt5):** Implement `_restore_profile_selection`. Find index of `selected_profile` in `self.app.profile_combo` and set `setCurrentIndex(index)`. Trigger update of profile details if necessary.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 10.D.3: Helper - Restore Pane/Splitter Positions (`_restore_pane_positions`)**
    *   **Discrepancy/Issue (PyQt5):** Stub method.
    *   **Tkinter:** Used `self.app.main_pane.sashpos(0, pane_positions.get('main_horizontal'))` etc.
    *   **Required Action (PyQt5):** Implement `_restore_pane_positions`. Use `self.app.main_splitter.setSizes(list_of_sizes)` for `QSplitter` elements, using values from `ui_state.get('splitter_sizes')`.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 10.D.4: Helper - Restore Log Panel State (`_restore_log_panel_state`)**
    *   **Discrepancy/Issue (PyQt5):** Stub method.
    *   **Tkinter:** Called `self.app.toggle_log_panel(force_show=not collapsed)`.
    *   **Required Action (PyQt5):** Implement `_restore_log_panel_state`. If using a dock widget: `self.app.log_dock_widget.setVisible(not collapsed)`. If custom toggle, call that.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 10.D.5: Helper - Apply Thread Settings (`_apply_thread_settings`)**
    *   **Discrepancy/Issue (PyQt5):** Stub method.
    *   **Tkinter:** Set `self.app.max_threads` and `self.app.process_timeout` from settings.
    *   **Required Action (PyQt5):** Implement `_apply_thread_settings` if these settings are still relevant and managed by the main app. Update `self.app.max_threads` etc.
    *   **Priority:** Low (if settings are still used)
    *   **Status:** Open

#### E. Generic Get/Update Setting (PyQt5 specific)
*   **Issue 10.E.1: `get_setting` and `update_setting`**
    *   **Context:** The PyQt5 version introduces `get_setting(self, section: str, key: str, default=None)` and `update_setting(self, section: str, key: str, value)`.
    *   **Discrepancy/Issue:** These are stubs. They imply a more structured settings dictionary (e.g., `settings['ui']['theme']` or `settings['processing']['max_threads']`).
    *   **Required Action (PyQt5):**
        *   Decide on the structure for `self.app.settings` (e.g., nested dictionaries).
        *   Implement `get_setting`: Load settings if not already loaded. Navigate the nested structure to retrieve `self.app.settings[section][key]`, returning `default` if not found.
        *   Implement `update_setting`: Load settings if not already loaded. Update `self.app.settings[section][key] = value`. Then call `self.save_settings(self.app.settings)` to persist the change immediately or mark settings as dirty to be saved on exit.
    *   **Priority:** Medium
    *   **Status:** Open

#### F. Tkinter-Specific Relics
*   **Issue 10.F.1: `save_ui_state` (Tkinter)**
    *   **Context:** The Tkinter version had `save_ui_state(self, key: str, value: Any)` which directly modified `self.app.settings['ui_state']` and called `save_settings`. This is somewhat superseded by the more structured `update_setting` in PyQt5 if adopted.
    *   **Required Action:** This specific method is unlikely to be needed if `update_setting` and `save_current_state` are well-implemented in PyQt5.
    *   **Priority:** N/A (Covered by PyQt5 design)
    *   **Status:** Resolved

---

### 12. Core Logic: `python/gui_components/theme_manager.py` (and `theme_manager_pyqt5.py`) vs Original

*   **Note:** Manages UI themes/styles. The PyQt5 version will handle QSS stylesheets instead of Tkinter theme settings.

#### A. Core Responsibilities (Expected for PyQt5)
*   Loading available themes (e.g., from a directory of QSS files or predefined themes).
*   Applying a selected theme (QSS stylesheet) to the application.
*   Providing a list of available themes to UI components (e.g., `SettingsWindowPyQt5`).
*   Potentially managing icon sets or colors associated with themes.
*   Loading and providing icons.

#### B. PyQt5 Adaptation Considerations and Potential Issues

*   **Issue 12.B.1: File Existence and Naming**
    *   **Context:** `app_gui_pyqt5.py` imports `ThemeManager` from `python.theme_manager` and also `apply_nuke_theme` from `python.themes.nuke_theme`. This suggests `theme_manager.py` might have been adapted, or a new `ThemeManagerPyQt5` is expected.
    *   **Discrepancy/Issue:** The exact structure for PyQt5 theme management needs clarification. `apply_nuke_theme(app)` is called directly in `app_gui_pyqt5.py`'s main block.
    *   **Required Action:**
        *   Determine if `ThemeManager` class is still the central point for theme logic or if it's a simpler utility now.
        *   If `ThemeManager` is used, ensure it's adapted for QSS. If not, the logic in `apply_nuke_theme` and any other theme files needs to be reviewed.
        *   The `SettingsWindowPyQt5` (Issue 3.S.4) needs to interact with a theme management system to list and apply themes.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.2: QSS Loading and Application**
    *   **Context:** Applying themes using `app.setStyleSheet()`.
    *   **Discrepancy/Issue:** Logic for finding, reading, and applying QSS files.
    *   **Required Action:** Ensure the theme manager (or equivalent functions like `apply_nuke_theme`) correctly loads QSS files and applies them globally to the `QApplication` instance. Handle potential errors like missing QSS files.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.3: Icon Management (Revisited from WidgetFactory)**
    *   **Context:** The Tkinter `ThemeManager` had `get_icon_image` and `load_icons`. `WidgetFactoryPyQt5` has its own `_load_icons` and `get_icon`.
    *   **Discrepancy/Issue:** Potential duplication or unclear responsibility for icon loading.
    *   **Required Action:** Consolidate icon loading logic. Ideally, one manager (either `ThemeManagerPyQt5` or `WidgetFactoryPyQt5`, or a dedicated `IconManager`) should be responsible for loading and caching all icons. Other components should request icons from this central manager. This avoids issues with relative paths and ensures consistency.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.4: Dynamic Theme Switching**
    *   **Context:** Allowing users to change themes at runtime via `SettingsWindowPyQt5`.
    *   **Discrepancy/Issue:** The theme manager needs to support re-applying a new QSS stylesheet to the running application.
    *   **Required Action:** Ensure the theme manager can clear any existing global stylesheet and apply a new one when a theme is changed in settings. This should trigger a visual update of the application.
    *   **Priority:** Medium
    *   **Status:** Open

---

### 13. Core Logic: `python/config_manager.py` vs Original

*   **Note:** This manager might be responsible for handling paths to configuration files (`patterns.json`, `profiles.json`, `user_settings.json`) and potentially loading/saving them if not handled by `SettingsManager` or individual editors.

#### A. Core Responsibilities (Potential)
*   Determining paths to various configuration files (e.g., in a user directory or application directory).
*   Providing these paths to other components.
*   Optionally, centralizing the loading/saving of these JSON configuration files if this responsibility is not within `SettingsManager` or the specific JSON editors.

#### B. PyQt5 Adaptation Considerations and Potential Issues

*   **Issue 13.B.1: Existence and Role Clarification**
    *   **Context:** `app_gui_pyqt5.py` has `_determine_config_path` to find the `config` directory. `SettingsWindowPyQt5` and JSON editors seem to construct paths to `patterns.json` and `profiles.json` themselves using this base config path.
    *   **Discrepancy/Issue:** The necessity of a dedicated `ConfigManager` class in the PyQt5 version is unclear if its primary role (path determination) is already handled in `app_gui_pyqt5.py` and file I/O is done by editors or `SettingsManager`.
    *   **Required Action:**
        *   Review if a `ConfigManager` class exists and is used in the PyQt5 version.
        *   If it exists, clarify its exact responsibilities. Is it just a path provider, or does it also handle I/O?
        *   If its role is minimal, consider consolidating its functionality into `SettingsManager` or `app_gui_pyqt5.py` to simplify the architecture.
        *   If it *is* intended to be the central I/O handler for configs (as per Issue 3.S.1 for `SettingsWindow`), then its interface needs to be robust.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 13.B.2: Configuration File Locations**
    *   **Context:** Ensuring configuration files are stored in appropriate user-specific or application-specific locations, especially for a packaged application.
    *   **Discrepancy/Issue:** Hardcoded relative paths might not work well when the application is frozen/packaged.
    *   **Required Action:** If `ConfigManager` is responsible for paths, ensure it uses platform-agnostic methods to determine user data directories (e.g., using `QStandardPaths` in PyQt5 or `appdirs` library) for storing user-modifiable configurations like `user_settings.json`, `profiles.json`. Default/template configurations can be bundled with the app.
    *   **Priority:** Medium
    *   **Status:** Open

---

### 14. Utility Files: `python/utils.py` vs Original

*   **Note:** This file typically contains miscellaneous helper functions used across the application.

#### A. Core Responsibilities (Expected)
*   Hosting utility functions that don't belong to a specific manager or component but are reused.
*   Examples: file system helpers, string manipulation, data conversion, etc.

#### B. PyQt5 Adaptation Considerations and Potential Issues

*   **Issue 14.B.1: Review for PyQt5 Specific Replacements**
    *   **Context:** Some Tkinter-specific utilities might have PyQt5 equivalents or might no longer be needed.
    *   **Discrepancy/Issue:** For example, utilities for Tkinter geometry or color manipulation would be irrelevant.
    *   **Required Action:** Review all functions in `utils.py`:
        *   Identify any functions that were specific to Tkinter and are no longer applicable.
        *   Determine if any utility functions can be replaced by standard Python features or PyQt5 built-in functionalities (e.g., `QDir`, `QFile`, `QStandardPaths` for file system operations).
        *   Ensure remaining utilities are still relevant and used correctly in the PyQt5 codebase.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 14.B.2: New PyQt5-Specific Utilities**
    *   **Context:** New utilities might have been added for PyQt5.
    *   **Discrepancy/Issue:** For example, helpers for QSS, `QColor` manipulation, or custom widget interactions.
    *   **Required Action:** If new utilities specific to PyQt5 have been added to `utils.py`, review them for correctness and necessity. Consider if they belong in `utils.py` or perhaps in a more specific PyQt5 utility module or within `WidgetFactoryPyQt5` if widget-related.
    *   **Priority:** Low
    *   **Status:** Open

*   **Issue 14.B.3: `StringVar` Custom Class**
    *   **Context:** `app_gui_pyqt5.py` defines a custom `StringVar(QObject)` class for compatibility.
    *   **Discrepancy/Issue:** This is a significant utility. It's currently defined within `app_gui_pyqt5.py`.
    *   **Required Action:** Consider moving the `StringVar(QObject)` class from `app_gui_pyqt5.py` to `python/utils.py` or a dedicated `python/qt_utils.py` if it's intended to be a general-purpose Qt compatibility utility for this project or future projects. This improves modularity.
    *   **Priority:** Low (Refactoring suggestion)
    *   **Status:** Open

---
