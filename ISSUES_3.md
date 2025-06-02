# PyQt5 Conversion: Issues and Discrepancies Log (Part 3)

This document continues the log of issues and discrepancies found during the PyQt5 conversion, focusing on specific modules.

---

### 11. Core Logic: `python/gui_components/status_manager_pyqt5.py` vs `python/gui_components/status_manager.py` (Tkinter Backup)

*   **Note:** The StatusManager is responsible for updating status messages, progress bars, and potentially logging. The PyQt5 version is `status_manager_pyqt5.py` and the Tkinter version is `status_manager.py`.

#### A. Initialization (`__init__`)
*   **Issue 11.A.1: Basic Attributes**
    *   **Context:** Both initialize `self.app` (the main application instance).
    *   **Discrepancy/Issue (PyQt5 `status_manager_pyqt5.py`):**
        *   The `__init__` method is currently empty (pass).
        *   **Tkinter `status_manager.py`:** Initializes `self.app`, `self.progress_stages`, `self.current_stage_index`, `self.scan_progress_bar`, `self.scan_status_label`, `self.overall_progress_bar`, `self.overall_status_label`, `self.details_text_widget`, `self.last_ui_update_time`, `self.ui_update_pending`, `self.update_lock`.
    *   **Required Action (PyQt5):**
        *   In `status_manager_pyqt5.py`, the `__init__` should store `app_instance` as `self.app`.
        *   It needs references to the PyQt5 UI elements it will control (e.g., `self.app.status_label`, `self.app.progress_bar`, `self.app.details_text_edit`). These should be passed or assigned during app setup.
        *   Initialize any necessary state variables similar to Tkinter if the multi-stage progress or detailed logging is to be replicated (e.g., `self.current_scan_operation_label`, `self.current_scan_progress_bar`, `self.overall_progress_bar`, `self.log_text_edit`).
        *   Consider if rate limiting for UI updates (`last_ui_update_time`, `ui_update_pending`, `update_lock`) is needed and how to implement it with `QTimer` if so.
    *   **Priority:** High
    *   **Status:** Open

#### B. Setting Status Messages
*   **Issue 11.B.1: Simple Status Update (`set_status` / `set_status_message`)**
    *   **Context:** Updating a primary status label.
    *   **Discrepancy/Issue (PyQt5 `status_manager_pyqt5.py`):**
        *   Has `set_status(self, message: str)` which is a stub.
        *   **Tkinter `status_manager.py`:** `set_status_message(self, message: str, progress: Optional[float] = None)` updated `self.overall_status_label` and optionally `self.overall_progress_bar`.
    *   **Required Action (PyQt5):**
        *   Implement `set_status(self, message: str)` in `status_manager_pyqt5.py`.
        *   It should update the main status label: `self.app.status_bar_label.setText(message)` (assuming `status_bar_label` is the name of the `QLabel` in the status bar).
        *   Ensure this method is thread-safe if called from worker threads (e.g., by emitting a signal that `AppGuiPyQt5` connects to the label's `setText`).
    *   **Priority:** High
    *   **Status:** Open

#### C. Progress Management
*   **Issue 11.C.1: Scan Progress (`start_scan_progress`, `complete_validation_stage`, `finish_scan_progress`)**
    *   **Context:** Managing a multi-stage progress indication, primarily for the scanning operation.
    *   **Discrepancy/Issue (PyQt5 `status_manager_pyqt5.py`):**
        *   `start_scan_progress()`, `complete_validation_stage()`, `finish_scan_progress(self, success: bool, message: str = "")` are stubs.
        *   **Tkinter `status_manager.py`:** Had detailed logic for showing/hiding a progress panel, defining stages (`Validation`, `Scanning`, `Processing`), updating labels and progress bars for each stage, and an overall progress bar.
    *   **Required Action (PyQt5):**
        *   Decide on the UI for progress. If a dedicated progress panel/dialog is used, `StatusManagerPyQt5` will need to manage its visibility and widgets.
        *   Implement `start_scan_progress`: Show progress UI, set to initial state (e.g., "Validating...", progress 0%).
        *   Implement `complete_validation_stage`: Update status to "Scanning...", reset progress for scanning phase.
        *   Implement `finish_scan_progress`: Update status based on `success` and `message`. Hide progress UI or set to a completed state. Reset progress variables.
        *   These methods will interact with `QLabel` and `QProgressBar` widgets.
        *   Thread safety is crucial if these are called from different parts of the application or threads.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 11.C.2: Generic Progress Update (`update_progress`)**
    *   **Context:** A general method to update a progress bar and an associated message.
    *   **Discrepancy/Issue (PyQt5 `status_manager_pyqt5.py`):**
        *   `update_progress(self, percent: float, message: str = "")` is a stub.
        *   **Tkinter `status_manager.py`:** Did not have a direct equivalent; progress was tied to stages or specific operations.
    *   **Required Action (PyQt5):**
        *   Implement `update_progress`. This should update a specific `QProgressBar` (e.g., `self.app.operation_progress_bar.setValue(int(percent))`) and an optional associated `QLabel` (`self.app.operation_status_label.setText(message)`).
        *   This could be used for file copy progress or other single-phase operations.
    *   **Priority:** Medium
    *   **Status:** Open

#### D. Logging (`add_log_message`)
*   **Issue 11.D.1: Adding Messages to Log UI**
    *   **Context:** Displaying log messages in a UI element (e.g., `QTextEdit`).
    *   **Discrepancy/Issue (PyQt5 `status_manager_pyqt5.py`):**
        *   `add_log_message(self, message: str, level: str = "INFO")` is a stub.
        *   **Tkinter `status_manager.py`:** Appended messages to `self.details_text_widget` with a timestamp and level. Handled scrolling to the end. Had rate limiting (`_can_update_ui`, `_delayed_ui_update`) to prevent UI freezes from too many log messages.
    *   **Required Action (PyQt5):**
        *   Implement `add_log_message`.
        *   It should append the formatted message (timestamp, level, message) to `self.app.log_text_edit.appendPlainText(...)` (if `log_text_edit` is a `QPlainTextEdit` or `QTextEdit`).
        *   Implement thread-safe logging. If called from worker threads, it must emit a signal to the main thread to append text.
        *   Consider if rate-limiting is needed. If so, a `QTimer` could be used to batch updates or defer them slightly.
        *   Handle different log levels (e.g., different colors or icons) if desired, using HTML for `QTextEdit` or by other means.
    *   **Priority:** High
    *   **Status:** Open

#### E. File Transfer Info Update (PyQt5 Specific)
*   **Issue 11.E.1: `update_file_transfer_info`**
    *   **Context:** PyQt5 version has `update_file_transfer_info(self, file_name: str, speed_mbps: float, eta_str: str, percent: float)`. This is new compared to the Tkinter version.
    *   **Discrepancy/Issue:** This is a stub.
    *   **Required Action (PyQt5):**
        *   Implement this method to update relevant UI elements for file transfer progress.
        *   This might involve setting text on multiple `QLabel`s (e.g., for current file, speed, ETA) and updating a `QProgressBar` with `percent`.
        *   Example: `self.app.current_file_label.setText(file_name)`, `self.app.speed_label.setText(f"{speed_mbps:.2f} MB/s")`, `self.app.eta_label.setText(eta_str)`, `self.app.transfer_progress_bar.setValue(int(percent))`.
        *   Ensure thread safety if called from a file transfer worker thread.
    *   **Priority:** Medium (as it's a new feature for file operations)
    *   **Status:** Open

#### F. Tkinter-Specific Methods and Logic
*   **Issue 11.F.1: Tkinter UI Update Logic (`_can_update_ui`, `_delayed_ui_update`, `process_adapter_status`)**
    *   **Context:** Tkinter version had `_get_stage_status_enum`, `_can_update_ui`, `_delayed_ui_update` for managing UI updates and rate limiting, and `process_adapter_status` for handling status from `GuiNormalizerAdapter`.
    *   **Discrepancy/Issue:** These are Tkinter-specific implementations.
    *   **Required Action (PyQt5):**
        *   Rate limiting and delayed updates in PyQt5 should be achieved using `QTimer`.
        *   Status updates from adapters (like `GuiNormalizerAdapterPyQt5`) should ideally use Qt signals emitted by the adapter and connected to slots in `StatusManagerPyQt5` or `AppGuiPyQt5` which then call `StatusManagerPyQt5` methods.
        *   The `process_adapter_status` logic will need to be re-thought in terms of signal/slot connections.
    *   **Priority:** Medium (for redesigning adapter communication)
    *   **Status:** Open

#### G. Missing Imports and Placeholders
*   **Issue 11.G.1: Imports and Completeness**
    *   **Context:** The provided `status_manager_pyqt5.py` is a stub for most methods.
    *   **Discrepancy/Issue:** Methods are empty. It imports `QTimer` but doesn't use it in the stubs.
    *   **Required Action:** Complete the implementation of all methods as detailed above. Add necessary imports (e.g., `QDateTime` for timestamps if used, UI elements from `PyQt5.QtWidgets` if type hinting them, though direct access will be via `self.app`).
    *   **Priority:** High
    *   **Status:** Open

---

### 12. Core Logic: Theme Management (PyQt5 vs. Tkinter `theme_manager.py`)

*   **Note:** The Tkinter version is `python/gui_components/theme_manager.py`. A dedicated PyQt5 version, tentatively `theme_manager_pyqt5.py`, needs to be created. The Tkinter version provides detailed theming including appearance modes, VS Code-inspired color themes with panel variations, specific widget styling (especially for Treeview), and an icon management system.

#### A. Core Responsibilities (Derived from Tkinter version and PyQt5 needs):
*   **Appearance Mode Management:** Handle "Light", "Dark", and potentially "System" modes by applying different QSS or palettes.
*   **Color Theme Management:** Load and apply different color schemes (e.g., "blue", "dark_plus", custom themes). In PyQt5, themes would primarily be defined by QSS files or structured QSS strings.
*   **Widget Styling (via QSS):**
    *   Apply global styles to `QApplication.instance()`.
    *   Provide mechanisms for styling common Qt widgets (buttons, labels, frames, input fields, etc.).
    *   Replicate detailed styling for `QTreeView` (items, branches, header, alternating row colors, etc.) using QSS selectors like `QTreeView::item`, `QTreeView::branch`, `QHeaderView::section`.
    *   Style log display widgets (`QTextEdit` or `QPlainTextEdit`).
*   **Icon Management:**
    *   Load icons (e.g., from files or a Qt Resource System - `.qrc` file) and provide them as `QIcon` or `QPixmap` objects.
    *   Implement an icon caching mechanism if beneficial.
    *   Provide placeholder icons if actual icons are missing.
*   **Theme Definition and Loading:**
    *   Define a structure for themes (e.g., dictionaries mapping theme names to QSS content or paths to QSS files).
    *   Load theme definitions (e.g., from Python dictionaries, JSON files, or dedicated QSS files per theme).
*   **Dynamic Theme Application:** Allow the user to change themes and appearance modes at runtime, with the UI updating immediately.
*   **Integration with SettingsManagerPyQt5:** Persist and restore the user's selected theme and appearance mode.

#### B. PyQt5 Adaptation and Implementation Plan (`theme_manager_pyqt5.py` - New File):

*   **Issue 12.B.1: File Creation and Basic Structure**
    *   **Context:** The file `python/gui_components/theme_manager_pyqt5.py` needs to be created.
    *   **Required Action:** Create `ThemeManagerPyQt5` class. It will need an `__init__(self, app_instance)` method to store a reference to the main application (for accessing `SettingsManagerPyQt5` and applying styles) and potentially paths to theme/icon resources.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 12.B.2: QSS Definition and Management**
    *   **Context:** Themes will be primarily QSS-based.
    *   **Required Action:**
        *   Decide on QSS storage: separate `.qss` files per theme, or QSS strings embedded in Python/JSON.
        *   Implement methods to load and parse these QSS definitions.
        *   The `self.themes` dictionary structure from Tkinter version can be adapted to store QSS strings or paths.
        *   Panel variations imply the need for complex QSS selectors or multiple QSS sections per theme.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 12.B.3: Applying Stylesheets**
    *   **Context:** Applying the selected theme to the application.
    *   **Required Action:** Implement `apply_theme_to_app()` (or similar). This method will typically call `QApplication.instance().setStyleSheet(qss_string)`.
        *   Ensure that re-applying a stylesheet correctly updates the UI.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 12.B.4: Appearance Modes (Light/Dark/System)**
    *   **Context:** Replicating `customtkinter.set_appearance_mode()`.
    *   **Required Action:**
        *   Implement logic to switch between light and dark themes (which would be distinct QSS sets).
        *   For "System" mode, investigate querying OS settings (e.g., via `QApplication.palette()` or platform-specific APIs if necessary, or by using libraries that assist with this like `qt-material` or `pyqtdarktheme` if those are considered).
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.5: Icon System (`get_icon`)**
    *   **Context:** Replacing `CTkImage` with `QIcon`/`QPixmap`.
    *   **Required Action:**
        *   Implement `get_icon(self, icon_name: str, size: Optional[tuple[int, int]] = None) -> QIcon`.
        *   Load images (e.g., PNGs) into `QPixmap`, then create `QIcon` from `QPixmap`.
        *   Implement icon caching (`self.icon_cache`).
        *   Define `self.icon_path`.
        *   Implement `_create_placeholder_icon()` to return a default `QIcon` or generate one with `QPixmap` and `QPainter`.
        *   Adapt `_get_folder_icon_for_treeview()` for `QTreeView` if custom folder icons are still desired beyond standard QTreeView branch indicators.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 12.B.6: Specific Widget Styling (Treeview, etc.)**
    *   **Context:** The Tkinter version has very detailed styling for `ttk.Treeview`.
    *   **Required Action:** Translate these detailed style rules into comprehensive QSS for `QTreeView`, `QHeaderView`, and other complex widgets. This will be a significant part of the QSS definition for each theme.
        *   Example selectors: `QTreeView::item { color: red; }`, `QTreeView::item:selected { background-color: blue; }`, `QTreeView::branch:has-children:!has-siblings:closed`, `QHeaderView::section { background-color: gray; }`.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 12.B.7: Integration with SettingsManagerPyQt5**
    *   **Context:** Persisting theme choices.
    *   **Required Action:** Implement `_initialize_theme_settings()` to load `current_theme_name` and `current_appearance_mode` from `SettingsManagerPyQt5`.
        *   `update_theme_settings()` should save the current choices back using `SettingsManagerPyQt5`.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.8: Public API**
    *   **Context:** Providing methods to change themes.
    *   **Required Action:** Implement `set_appearance_mode(self, mode_name: str)` and `set_color_theme(self, theme_name: str)`. These should update internal state, save settings, and re-apply the theme to the application.
        *   Provide `get_current_theme_name()`, `get_current_appearance_mode()`, `get_available_themes()`, `get_available_appearance_modes()`.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 12.B.9: External Theme Libraries (Consideration)**
    *   **Context:** The Tkinter version uses `customtkinter` and custom themes. For PyQt5, there are external libraries.
    *   **Required Action:** Decide whether to build all QSS from scratch (to match VS Code-inspired themes closely) or leverage libraries like `qt-material`, `QDarkStyleSheet`, `pyqtdarktheme`, `qtvscodestyle`. If using libraries, `ThemeManagerPyQt5` would act as an abstraction layer over them.
        *   Given the custom nature of the Tkinter themes, a custom QSS approach is more likely to match, but more work.
    *   **Priority:** Low (Decision can be deferred, initial implementation can focus on custom QSS framework)
    *   **Status:** Open

---

### 13. Core Logic: `python/gui_components/file_operations_manager_pyqt5.py` vs `python/gui_components/file_operations_manager.py`

*   **Note:** Manages file copy/move operations. The PyQt5 version is a stub. Both rely on utilities from `python.file_operations_utils.file_management` (not provided, but assumed to contain `copy_item`, `move_item`, etc.). Integration with a detailed PyQt5 file operations progress panel (see Issue 6.A.2 in ISSUES_2.md) is critical.

#### A. Initialization (`__init__`)
*   **Issue 13.A.1: Basic Attributes**
    *   **Context:** Both initialize `self.app` (main application instance).
    *   **Discrepancy/Issue (PyQt5 `file_operations_manager_pyqt5.py` stub):
        *   The `__init__(self, app_instance)` is empty.
        *   **Tkinter `file_operations_manager.py`:** Stores `app_instance`.
    *   **Required Action (PyQt5):**
        *   In `file_operations_manager_pyqt5.py`, the `__init__` should store `app_instance` as `self.app`.
        *   It will need references to the `FileOperationsProgressWindow` (once developed) and potentially other UI elements if it directly updates status messages outside the progress window.
        *   Initialize attributes for managing operation queues, threads, and active transfers (e.g., `self.operation_queue`, `self.worker_thread`, `self.active_transfers_details`).
    *   **Priority:** High
    *   **Status:** Open

#### B. Starting Operations (UI Interaction)
*   **Issue 13.B.1: UI Triggers (`on_copy_selected_click`, `on_move_selected_click`)**
    *   **Context (PyQt5):** `on_copy_selected_click` and `on_move_selected_click` are stubs in the PyQt5 version. These would be connected to button clicks in `app_gui_pyqt5.py`.
    *   **Tkinter:** `copy_files` and `move_files` methods are called, which then call `_start_optimized_batch_operation`.
    *   **Required Action (PyQt5):**
        *   Implement `on_copy_selected_click` and `on_move_selected_click`.
        *   These methods should:
            1.  Get selected items from `self.app.tree_manager.get_selected_items()`.
            2.  Perform any necessary validation (e.g., items selected, destination path valid).
            3.  Call `self.start_file_operation(selected_items, "copy")` or `"move"` respectively.
            4.  Show the `FileOperationsProgressWindow`.
    *   **Priority:** High
    *   **Status:** Open

#### C. Core Operation Logic (`start_file_operation`, `_file_operation_worker`)
*   **Issue 13.C.1: `start_file_operation` (PyQt5)**
    *   **Context:** This method (stub in PyQt5) should prepare and initiate the background file operation.
    *   **Tkinter:** `_start_optimized_batch_operation` seems to be the equivalent, preparing items and then likely calling the core copy/move utilities directly (details depend on `file_management.py`).
    *   **Required Action (PyQt5):**
        *   Implement `start_file_operation(self, items: List[Dict[str, Any]], operation_type: str)`.
        *   It should:
            *   Clear any previous operation state.
            *   Prepare the list of operations/transfers.
            *   Initialize the `FileOperationsProgressWindow` with total counts/size.
            *   Create and start `self.worker_thread` targeting `self._file_operation_worker`, passing `items` and `operation_type`.
            *   Disable relevant UI elements in the main app.
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 13.C.2: `_file_operation_worker` (PyQt5)**
    *   **Context:** This method (stub in PyQt5) runs in a separate thread to perform the file operations.
    *   **Required Action (PyQt5):**
        *   Implement `_file_operation_worker(self, items: List[Dict[str, Any]], operation_type: str)`.
        *   Iterate through `items`:
            *   For each item, determine source and destination paths.
            *   Emit signals to `FileOperationsProgressWindow` to add the item to the display and indicate it's starting.
            *   Call the appropriate low-level file operation utility (e.g., `self._copy_item` or `self._move_item`, which in turn would use functions from `python.file_operations_utils.file_management`).
            *   The low-level utilities must provide progress feedback (e.g., bytes copied for a progress bar) via callbacks or by being designed for incremental processing.
            *   `_file_operation_worker` will need to convert these low-level progress updates into Qt signals for the `FileOperationsProgressWindow` (e.g., `file_progress_updated = pyqtSignal(str_item_id, int_percent, str_speed, str_eta)`).
            *   Handle errors for individual files and overall operation, emitting signals for UI updates.
            *   After all operations, emit a final signal for completion/failure.
        *   Ensure proper error handling (`try-except`) within the loop and for the overall worker.
    *   **Priority:** Critical
    *   **Status:** Open

*   **Issue 13.C.3: Low-Level Operations (`_copy_item`, `_move_item`)**
    *   **Context:** The PyQt5 stub has `_copy_item`. A `_move_item` would also be needed.
    *   **Required Action (PyQt5):**
        *   Implement `_copy_item(self, source_path: str, dest_path: str, item_data: Dict[str, Any]) -> bool`.
        *   Implement a similar `_move_item(...)`.
        *   These methods should call the actual file system functions from `python.file_operations_utils.file_management` (e.g., `copy_item`, `move_item`, `copy_sequence_batch`, `move_sequence_batch`).
        *   Crucially, these underlying functions from `file_management.py` need to support progress reporting (e.g., via a callback that `_copy_item` can use to emit signals). If they are blocking, true progress reporting per file will be difficult.
        *   Handle return values (success/failure) and exceptions from the file utilities.
    *   **Priority:** High
    *   **Status:** Open

#### D. Progress Reporting and UI Integration
*   **Issue 13.D.1: Signals for Progress**
    *   **Context:** Communicating progress from the worker thread to the `FileOperationsProgressWindow`.
    *   **Required Action (PyQt5):**
        *   Define necessary `pyqtSignal`s in `FileOperationsManager` (e.g., `batch_started = pyqtSignal(int_total_files, int_total_size)`, `file_added_to_queue = pyqtSignal(str_item_id, dict_item_details)`, `file_progress_updated = pyqtSignal(str_item_id, int_percent, str_speed, str_eta)`, `file_completed = pyqtSignal(str_item_id, bool_success, str_error_msg)`, `batch_completed = pyqtSignal(bool_success, str_summary_msg)`).
        *   The `FileOperationsProgressWindow` will connect its slots to these signals.
    *   **Priority:** High
    *   **Status:** Open

#### E. Tkinter Version Specifics
*   **Issue 13.E.1: `_find_common_prefix`**
    *   **Context:** Tkinter version has `_find_common_prefix`. Its use is unclear without seeing how `_start_optimized_batch_operation` uses it.
    *   **Required Action (PyQt5):** Determine if this logic is still needed for any optimization in the PyQt5 version. If so, port it.
    *   **Priority:** Low
    *   **Status:** Open

---

### 14. Core Logic: `python/gui_normalizer_adapter.py` (PyQt5 Adaptation)

*   **Note:** This module adapts the core normalization logic (from `scanner.py` and `mapping.py`) for GUI interaction. The existing file is `python/gui_normalizer_adapter.py`. A `GuiNormalizerAdapterPyQt5` class or adaptation is needed.

#### A. Core Functionality
*   **`__init__(self, config_dir_path: str)`:** Initializes `FileSystemScanner` and `MappingGenerator`.
*   **`get_profile_names(self) -> List[str]`:** Retrieves profile names.
*   **`scan_and_normalize_structure(...)`:** The main method that orchestrates scanning and mapping. Critically, it accepts a `status_callback`.

#### B. PyQt5 Adaptation (`GuiNormalizerAdapterPyQt5`)
*   **Issue 14.B.1: Class Definition**
    *   **Context:** Decide whether to modify `GuiNormalizerAdapter` to be PyQt5-aware (e.g., inherit `QObject` and add signals) or create a new `GuiNormalizerAdapterPyQt5`.
    *   **Recommendation:** Create `GuiNormalizerAdapterPyQt5(QObject)` to keep Qt-specifics separate, following the project's pattern.
    *   **Required Action:** Define `GuiNormalizerAdapterPyQt5(QObject)`.
        *   It will still initialize `FileSystemScanner` and `MappingGenerator` (or their potential future PyQt5-aware versions if deep integration is chosen).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 14.B.2: Progress Reporting via Signals**
    *   **Context:** The `status_callback` in `scan_and_normalize_structure` needs to be replaced or augmented by Qt signals for thread-safe UI updates.
    *   **Required Action (PyQt5):**
        *   Define a signal in `GuiNormalizerAdapterPyQt5`, e.g., `progress_updated = pyqtSignal(dict)` or more specific signals like `scan_progress = pyqtSignal(str_path, int_percent_overall)`, `mapping_progress = pyqtSignal(str_status)`. The `app_gui_pyqt5.py` (Issue 1.B.4) already expects `self.normalizer.progress_callback.connect(...)`, so `progress_callback` should be defined as a `pyqtSignal(int, str)` (value, text) or similar to match `update_progress_from_normalizer` slot.
        *   The `scan_and_normalize_structure` method in `GuiNormalizerAdapterPyQt5` will call the core `scanner` and `generator` methods.
        *   A new internal callback function (e.g., `_internal_status_handler`) can be passed to the core logic's `status_callback` argument. This internal handler will then emit the Qt signal(s) with the received data.
        *   Example: `def _internal_status_handler(self, status_data): self.progress_updated.emit(status_data)`.
    *   **Priority:** Critical
    *   **Status:** Open

*   **Issue 14.B.3: Threading of `scan_and_normalize_structure`**
    *   **Context:** The `scan_and_normalize_structure` operation is long-running and must not block the GUI.
    *   **Required Action (PyQt5):**
        *   The `ScanManager` (Issue 9.C.1 in ISSUES_2.md) is responsible for running the normalizer's scan method in a separate thread.
        *   `GuiNormalizerAdapterPyQt5.scan_and_normalize_structure` itself doesn't need to manage the thread, but it must be safe to be called from a non-GUI thread if `ScanManager` calls it directly from its worker.
        *   The signals emitted by the adapter will handle the thread-safe communication back to the GUI thread.
    *   **Priority:** N/A (Handled by `ScanManager`)
    *   **Status:** Resolved (by `ScanManager` architecture)

#### C. Interface with Core Logic (`scanner.py`, `mapping.py`)
*   **Issue 14.C.1: `status_callback` Granularity**
    *   **Context:** The data provided by the `status_callback` from `FileSystemScanner` and `MappingGenerator` must be sufficient for meaningful progress updates.
    *   **Required Action:** Review the `status_callback` mechanism in the (unavailable) `scanner.py` and `mapping.py`. Ensure it provides information like:
        *   Current file/directory being processed.
        *   Stage of operation (e.g., "collecting files", "analyzing sequences", "generating proposals").
        *   Percentage completion if calculable.
        *   This data will be packaged into the dictionary for the `progress_updated` signal.
    *   **Priority:** Medium (Depends on core logic capabilities)
    *   **Status:** Open

---

### 15. Core Logic: `python/normalizer.py` (and components `scanner.py`, `mapping.py`) (PyQt5 Integration)

*   **Note:** The actual `normalizer.py` file and its components (`scanner.py`, `mapping.py`) are not provided. This analysis is based on their usage by `python/gui_normalizer_adapter.py`.

#### A. Core Responsibilities (Inferred)
*   **`scanner.py` (`FileSystemScanner`):** Responsible for traversing the file system, identifying files and sequences, and collecting metadata. Expected to be a potentially long-running operation.
*   **`mapping.py` (`MappingGenerator`):** Responsible for loading profiles and patterns, and then applying normalization rules to the scanned file structure to generate proposals for new names/paths.
*   **`normalizer.py` (if it exists as a higher-level orchestrator):** Might combine scanning and mapping steps.

#### B. PyQt5 Integration Considerations
*   **Issue 15.B.1: Maintaining UI Agnosticism**
    *   **Context:** The core normalization logic should ideally remain independent of PyQt5 or any specific UI framework.
    *   **Required Action:** Ensure that `scanner.py` and `mapping.py` do not directly import PyQt5 modules. The `GuiNormalizerAdapterPyQt5` (Issue 14) should be the sole bridge.
    *   **Priority:** High
    *   **Status:** Open (Requires code review of actual files)

*   **Issue 15.B.2: Progress Reporting Mechanism (`status_callback`)**
    *   **Context:** As discussed in Issue 14.C.1, these modules need to provide progress updates, currently via a `status_callback`.
    *   **Required Action:** The existing `status_callback` mechanism is suitable for UI-agnostic progress reporting. `GuiNormalizerAdapterPyQt5` will convert these callback invocations into Qt signals.
        *   Ensure the callback provides detailed enough information (current path, operation stage, counts, errors) for rich progress display in the UI.
    *   **Priority:** Medium
    *   **Status:** Open (Requires code review of actual files)

*   **Issue 15.B.3: Error Handling and Reporting**
    *   **Context:** Errors occurring during scanning or mapping need to be propagated correctly.
    *   **Required Action:**
        *   The core logic should raise specific exceptions for different error conditions (e.g., `ProfileNotFoundError`, `PatternSyntaxError`, `IOError`).
        *   `GuiNormalizerAdapterPyQt5.scan_and_normalize_structure` should catch these exceptions and can either re-raise them (for `ScanManager` to handle) or emit an error signal.
        *   The `status_callback` can also be used to report non-fatal errors or warnings during processing.
    *   **Priority:** Medium
    *   **Status:** Open (Requires code review of actual files)

*   **Issue 15.B.4: Configurability (Thread Settings, etc.)**
    *   **Context:** `ScanManager` (Tkinter version) applied thread settings to `self.app.normalizer.scanner` (Issue 9.C.1 in ISSUES.md).
    *   **Required Action:** If the `FileSystemScanner` or other components have configurable parameters (e.g., number of threads for parallel processing if any, timeouts), ensure these can be set by `GuiNormalizerAdapterPyQt5` or `ScanManager` before starting an operation.
    *   **Priority:** Low
    *   **Status:** Open (Requires code review of actual files)

---

### 16. GUI Components: `python/gui_components/batch_edit_dialog_pyqt5.py` vs `python/gui_components/batch_edit_dialog.py`

*   **Note:** The Tkinter version is `python/gui_components/batch_edit_dialog.py`. A PyQt5 equivalent, `BatchEditDialogPyQt5`, needs to be created. This dialog allows batch modification of properties for selected items from the preview tree.

#### A. Core Functionality (from Tkinter `batch_edit_dialog.py`)
*   **UI:** A `ctk.CTkToplevel` dialog.
*   **Input:** Takes a list of `items` (dictionaries representing selected files/sequences) and an `on_apply_callback`.
*   **Fields:** Allows editing of Asset, Task, Resolution, Version, Stage, and destination paths (as per docstring). Each field likely has a checkbox to enable/disable its modification and an entry/combobox for the new value.
*   **Logic:**
    *   `create_field_row` suggests a structured way to build the form.
    *   `_get_dropdown_values` implies some fields might use comboboxes with dynamically fetched values.
    *   On apply, it would collect changes from enabled fields and invoke `on_apply_callback`.

#### B. PyQt5 Implementation (`BatchEditDialogPyQt5(QDialog)` - New File)

*   **Issue 16.B.1: File Creation and Basic Structure**
    *   **Context:** The file `python/gui_components/batch_edit_dialog_pyqt5.py` needs to be created.
    *   **Required Action:**
        *   Create the file and define `BatchEditDialogPyQt5(QDialog)`.
        *   The `__init__` should accept `parent`, `items: List[Dict[str, Any]]`, and `on_apply_callback: Callable`.
        *   Store these and set up the dialog (window title, modality if needed).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 16.B.2: UI Element Implementation**
    *   **Context:** Recreating the form with Qt widgets.
    *   **Required Action:**
        *   Use `QFormLayout` for a clean label-field structure.
        *   For each editable property (Asset, Task, etc.):
            *   A `QCheckBox` to enable/disable editing for that property.
            *   A `QLineEdit` for free-text properties (e.g., Version, Stage, parts of destination path).
            *   A `QComboBox` for properties with predefined choices (e.g., Task, Asset, Resolution if they come from a list).
        *   Populate `QComboBox` items using a PyQt5 equivalent of `_get_dropdown_values` (e.g., fetching from `Normalizer` or `ConfigManager`).
        *   Initialize field values: If all selected `items` share a common value for a property, display it. Otherwise, leave blank or show a placeholder (e.g., "<multiple values>").
        *   Add "Apply" and "Cancel" buttons (e.g., using `QDialogButtonBox`).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 16.B.3: Logic for Applying Changes**
    *   **Context:** When "Apply" is clicked.
    *   **Required Action:**
        *   Create a dictionary `changes_to_apply = {}`.
        *   For each property, if its corresponding `QCheckBox` is checked, get the value from the `QLineEdit`/`QComboBox` and add it to `changes_to_apply` (e.g., `changes_to_apply['task'] = self.task_combobox.currentText()`).
        *   If `changes_to_apply` is not empty, call `self.on_apply_callback(self.items, changes_to_apply)`.
        *   The `on_apply_callback` (likely a method in `AppGuiPyQt5` or `FileOperationsManager`) will then iterate through the original `items` and modify their data or trigger re-processing/re-mapping.
        *   Close the dialog (`self.accept()`).
    *   **Priority:** High
    *   **Status:** Open

*   **Issue 16.B.4: Destination Path Editing**
    *   **Context:** Editing destination paths can be complex (template variables, structure).
    *   **Required Action:**
        *   Determine how destination paths are represented and edited. It might be a single string or broken into components.
        *   If template variables are used (e.g., `{task}`, `{asset}`), the dialog should make this clear, or provide a structured way to edit path templates if that's the goal.
        *   The current Tkinter version's docstring just says "destination paths", implying it might be direct editing of the proposed final path or parts of it.
    *   **Priority:** Medium
    *   **Status:** Open

*   **Issue 16.B.5: Initial State of Fields**
    *   **Context:** How fields are populated when the dialog opens.
    *   **Required Action:**
        *   When the dialog opens, iterate through the `self.items`.
        *   For each editable property, if all items have the same value, set the corresponding `QLineEdit`/`QComboBox` to that value.
        *   If values differ, the `QLineEdit` could be blank or show a placeholder like "(Multiple Values)". `QComboBox` could be set to a blank item or a special "multiple values" item if added.
        *   Initially, all `QCheckBox`es for enabling edits should be unchecked.
    *   **Priority:** Medium
    *   **Status:** Open

---
