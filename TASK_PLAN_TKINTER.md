# Clean Incomings - Tkinter UI Development Plan

This document outlines the steps and features for rebuilding the Clean Incomings application UI using Python's Tkinter framework with the ttkbootstrap theme library.

## I. Core Application Setup
1.  **Initialize Main Application Window:**
    *   Create main `App` class inheriting from `tk.Tk` or using `tb.Window`.
    *   Set window title, initial size.
    *   Apply a `ttkbootstrap` theme (e.g., "litera", "minty", "superhero").
2.  **Install Dependencies:** Ensure `ttkbootstrap` is installed.

## II. Main UI Layout & Components
1.  **Top Control Frame:**
    *   Profile Selection: `tb.Combobox` (populated from `config/profiles.json`).
    *   Source Folder: `tb.Button` ("Select Source") + `tb.Label`/`tb.Entry` (read-only) for path.
    *   Destination Folder: `tb.Button` ("Select Destination") + `tb.Label`/`tb.Entry` (read-only) for path.
    *   Refresh Button: `tb.Button`.
    *   Settings Button: `tb.Button`.
2.  **Main Content Area (using `tb.PanedWindow` for resizable panes):**
    *   **Left Pane: Source Folder Structure View**
        *   `tb.Treeview` to display the directory tree of the selected source folder.
    *   **Right Pane: Preview & Information Area**
        *   **Filtering Controls Sub-Frame:**
            *   `tb.Label` ("Filter:").
            *   `tb.Combobox` or `tb.Radiobutton` set for "Show: All / Selected / Matched / Unmatched".
        *   **Preview Treeview (`tb.Treeview`):**
            *   Columns: Checkbox, File/Sequence Name, Matched Tags, Current Task (editable), Current Asset (editable), New Destination Path.
            *   Implement checkbox functionality for item selection.
        *   **Information Display Sub-Frame (`tb.Labelframe`):**
            *   Labels for: Source Path, Destination Path, Total Frames (for sequences), etc., based on Preview Treeview selection.
3.  **Action Button Frame:**
    *   Copy Button: `tb.Button` ("Copy Selected").
    *   Move Button: `tb.Button` ("Move Selected").
    *   Undo Button: `tb.Button` ("Undo Last Operation").
    *   Cancel Button: `tb.Button` ("Cancel Current Operation").
4.  **Bottom Status Frame:**
    *   Scan Progress Bar: `tb.Progressbar`.
    *   Copy/Move Progress Bar: `tb.Progressbar`.
    *   ETA Label: `tb.Label`.
    *   Current File/Operation Label: `tb.Label`.
    *   General Status Message Label: `tb.Label`.

## III. Core Functionality Implementation
1.  **Profile Loading:**
    *   Function to read `config/profiles.json` and populate the profile combobox.
2.  **Folder Selection Dialogs:**
    *   Implement `filedialog.askdirectory` for source and destination.
3.  **Scanning Logic Integration (`normalizer.py scan`):**
    *   Run scan in a separate thread to keep UI responsive.
    *   Populate Source Folder Treeview.
    *   Populate Preview Treeview with initial scan results.
    *   Implement progress updates (achieved via `status_callback` and `self.after()`).
4.  **Mapping Logic Integration (`normalizer.py map`):**
    *   Run mapping in a separate thread.
    *   Use selected profile and scanned data.
    *   Update Preview Treeview with destination paths and matched tags.
    *   Handle "unmatched" status.
5.  **Copy/Move Operations:**
    *   Implement file/folder copy and move logic (threaded).
    *   Update progress bars and status.
6.  **Progress Updates & ETA:**
    *   **Implemented:** A `status_callback` mechanism is used by worker threads (via `GuiNormalizerAdapter`) to send detailed progress updates to the main UI thread.
    *   **Details:**
        *   The callback passes a dictionary with `type` (e.g., `"scan"`, `"mapping_generation"`) and `data` (containing status, message, counts like `current_file_count`, `total_files`).
        *   The main UI thread (`app_gui.py`) uses `self.after(0, ...)` to process these updates, ensuring thread safety for UI modifications (status label, progress bar).
        *   This system has been specifically enhanced to provide granular feedback during the 'MAPPING GENERATION' phase, including progress of file collection, sequence processing, and single file mapping stages.
    *   Further refinement for ETA calculation could be a future step if needed.

## IV. Advanced Features & Interactivity
1.  **Preview Treeview Enhancements:**
    *   Checkbox selection logic for individual/batch operations.
    *   Batch editing for "unmatched" task/asset fields (e.g., via a dialog or direct Treeview edit).
2.  **Filtering Implementation:**
    *   Logic to filter the Preview Treeview based on selected criteria.
3.  **Undo Operation:**
    *   Design a system to log copy/move actions.
    *   Implement logic to revert the last logged action.
4.  **Cancel Operation:**
    *   Mechanism for the "Cancel" button to signal worker threads to halt.
5.  **Refresh Functionality:**
    *   Re-trigger scan and/or map based on current UI selections.
6.  **Settings Window (`tb.Toplevel`):**
    *   **Controls:**
        *   Thread count (`tb.Spinbox`/`tb.Entry`).
        *   Concurrent files per worker (`tb.Spinbox`/`tb.Entry`).
        *   Enable/disable multithreading (`tb.Checkbutton`).
    *   **Graphical JSON Editors (for `patterns.json`, `profiles.json`):**
        *   Phase 1: Button to open files in default system editor.
        *   Phase 2 (Optional): Develop a simplified graphical editor within the app.
7.  **Error Handling and User Feedback:**
    *   Display errors gracefully in the status bar or dialogs.

## V. Refinement and Packaging
1.  **Code Cleanup and Structuring.**
2.  **Testing across different scenarios.**
3.  **(Optional) Packaging with PyInstaller or similar.**
