# Multi-Stage Progress Panel Guide

## Overview

The Clean Incomings application features a sophisticated multi-stage progress panel, providing users with detailed visual feedback during potentially long-running operations like scanning and file processing. This panel, implemented in `python/gui_components/progress_panel.py`, replaces simpler progress indicators with a comprehensive display that breaks down operations into distinct phases.

## Features

### Visual Elements
- **Stage-Specific Icons**: Each stage dynamically displays an icon reflecting its current state: `○` (Pending), `🔄` (In Progress), `✓` (Completed), `✗` (Error).
- **Color-Coded Status**: Icons and descriptive text change color to intuitively convey the stage status (e.g., gray for pending, blue for in-progress, green for success, red for error).
- **Individual Stage Progress Bars**: Where applicable, some stages may feature their own progress bars to show completion of sub-tasks within that stage.
- **Detailed Information Display**: Each stage can display real-time, context-specific details such as file counts, current file being processed, operation speed, or error messages.
- **Overall Progress Bar**: A master progress bar at the bottom of the panel (or in the main status bar) reflects the overall completion percentage across all stages.

### Monitored Stages

The progress panel is primarily designed to track the following stages during a typical **scan operation**: (File operations might use a simplified version or a different set of stages).

1.  **Queued**: Operation is waiting to start.
2.  **Validation**: Initial checks (e.g., source/destination paths exist, profile selected, settings are valid).
3.  **Scanning Files**: Traversing the source directory, discovering files and folders.
4.  **Generating Mappings**: Applying normalization rules from `patterns.json` and the selected profile in `profiles.json` to generate target paths.
5.  **Processing Results**: Preparing the scanned and mapped data for display in the GUI (e.g., populating tree views).
6.  **Complete**: All operations finished successfully.
7.  **Error**: An error occurred in one of the stages, halting the process.

## Usage

### Integration in the Main Application (`app_gui.py`)

When a user initiates an operation like "Refresh/Scan":
1.  The `ScanManager` (or `FileOperationsManager`) signals the `StatusManager` to begin progress tracking.
2.  The `StatusManager` updates the `ProgressPanel` instance (created by `WidgetFactory` and part of the main GUI layout).
3.  As the operation moves through its phases (e.g., Validation -> Scanning Files -> Generating Mappings), the respective manager notifies the `StatusManager`.
4.  The `StatusManager` updates the corresponding stage in the `ProgressPanel` with the new status, icon, color, details, and progress.

### Example Flow for a Scan:
-   **Queued**: Scan is initiated.
-   **Validation Stage**: Quick check of inputs. UI shows "Validation 🔄".
-   **Scanning Files Stage**: Real-time file discovery. UI shows "Scanning Files 🔄", details like "Found: 123 files", current directory.
-   **Generating Mappings Stage**: Applying rules. UI shows "Generating Mappings 🔄", details like "Mapped: 50/123 files".
-   **Processing Results Stage**: Preparing for display. UI shows "Processing Results 🔄".
-   **Complete Stage**: All done. UI shows "Complete ✓", all stages green.

### Error Handling
If any stage encounters an error:
-   The failed stage is marked with a red `✗` icon.
-   Specific error details are displayed within that stage's information area.
-   The overall progress may halt or indicate failure.
-   The user can clearly identify at which point the operation failed.

## Benefits

### For Users:
-   **Enhanced Transparency**: Clear visibility into what the application is doing during operations.
-   **Improved Time Awareness**: Better understanding of progress and remaining work.
-   **Clear Error Context**: Quick identification of the point of failure and the reason.
-   **Modern User Experience**: Provides a polished and professional feel to the application.

### For Developers:
-   **Modular Design**: The `ProgressPanel` is a self-contained component.
-   **Centralized Logic**: `StatusManager` handles the state updates, simplifying integration for other managers.
-   **Thread-Safe Updates**: GUI updates from worker threads are properly scheduled via the `StatusManager` to avoid threading issues.
-   **Maintainability**: Easier to modify or extend progress reporting for new or existing operations.

## Technical Implementation Details

The system involves several key components working together:

1.  **`ProgressPanel` (`python/gui_components/progress_panel.py`)**: The `customtkinter` component responsible for rendering the visual elements of the multi-stage display.
2.  **`StatusManager` (`python/gui_components/status_manager.py`)**: Acts as the intermediary, receiving progress updates from worker managers and translating them into UI updates for the `ProgressPanel` and other status elements (like the main progress bar or log).
3.  **`ScanManager` / `FileOperationsManager`**: These managers are responsible for performing the actual work in background threads and periodically reporting their progress (current stage, percentage, details) to the `StatusManager`.
4.  **`WidgetFactory` (`python/gui_components/widget_factory.py`)**: Responsible for creating and integrating the `ProgressPanel` instance into the main application layout.

### Key Methods in `StatusManager` for Progress Control:

```python
# Example methods (actual names might vary slightly):

# To initialize or reset the progress panel for a new scan:
status_manager.start_scan_progress(total_items_expected) # Or similar initialization

# To update a specific stage:
status_manager.update_stage_status(stage_name="Scanning Files", status="in_progress", message="Processing item X...")
status_manager.update_stage_progress(stage_name="Scanning Files", current_value=Y, total_value=Z)

# To mark a stage as complete or failed:
status_manager.complete_stage(stage_name="Validation", success=True)
status_manager.complete_stage(stage_name="Generating Mappings", success=False, error_message="Profile not found.")

# To finalize the overall progress:
status_manager.finish_overall_progress(success=True, final_message="Scan complete.")
status_manager.finish_overall_progress(success=False, final_message="Scan failed.")
```

## Aesthetic Design Considerations

The `ProgressPanel` is designed with:
-   **Clarity**: Easy-to-understand icons and text.
-   **Consistency**: Uniform appearance for all stages.
-   **Responsiveness**: Updates in near real-time to reflect ongoing work.
-   **Theming**: Adheres to the application's current theme (light/dark mode, color scheme) managed by `ThemeManager`.

This guide should provide a comprehensive understanding of the multi-stage progress panel's functionality, integration, and benefits within the Clean Incomings application.