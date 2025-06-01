# Application File Map

This document outlines the file structure and dependencies of the CleanIncomings application, starting from `app_gui.py`.

## Application Entry Point

-   **`app_gui.py`**: Main application GUI module.
    -   **UI Libraries**: `tkinter`, `customtkinter`
    -   **Standard Libraries**: `json`, `os`, `typing`
    -   **Local GUI Components (from `python.gui_components`)**:
        -   `status_manager.StatusManager`
        -   `theme_manager.ThemeManager`
        -   `file_operations_manager.FileOperationsManager`
        -   `tree_manager.TreeManager`
        -   `widget_factory.WidgetFactory`
        -   `scan_manager.ScanManager`
        -   `settings_manager.SettingsManager`
    -   **Local Core Logic (from `python`)**:
        -   `gui_normalizer_adapter.GuiNormalizerAdapter`
    -   **Configuration Files**:
        -   `themes/custom_blue.json` (CustomTkinter theme)
        -   `config/` (General path, specific files loaded by `GuiNormalizerAdapter` and `SettingsManager`)
        -   Implicitly `user_settings.json` (via `SettingsManager`)
        -   Implicitly `config/profiles.json` (legacy, though `GuiNormalizerAdapter` is primary)

## Core Python Modules (`python/`)

-   **`gui_normalizer_adapter.py`**: Adapter between the GUI and the normalization logic.
    -   **Standard Libraries**: `json`, `os`, `sys`, `time`, `uuid`, `pathlib.Path`, `threading`, `typing`
    -   **Local Dependencies**:
        -   `python.scanner.FileSystemScanner`
        -   `python.mapping.MappingGenerator`
    -   **Configuration Files**:
        -   `config/patterns.json`
        -   `config/profiles.json`

-   **`scanner.py`**: Handles file system scanning and building a tree structure.
    -   **Standard Libraries**: `os`, `sys`, `subprocess`, `shutil`, `uuid`, `json`, `time`, `concurrent.futures`, `threading`, `pathlib.Path`, `typing`, `re`
    -   **Generated Files**: Creates progress files in `python/_progress/` (e.g., `progress_<batch_id>.json`)

-   **`mapping.py`**: Generates mapping proposals based on scanned files and profiles.
    -   **Standard Libraries**: `re`, `pathlib.Path`, `typing`
    -   **Local Dependencies (from `python.mapping_utils`)**:
        -   `init_patterns_from_profile`
        -   `generate_mappings`
        -   `group_image_sequences`
        -   `finalize_sequences`
        -   `is_network_path`
        -   `create_sequence_mapping`
        -   `create_simple_mapping`
        -   `generate_simple_target_path`
        -   `extract_sequence_info`
        -   `process_file_for_sequence`
        -   `config_loader` (from `mapping_utils`)
        -   `shot_extractor`, `task_extractor`, `version_extractor`, `resolution_extractor`, `asset_extractor`, `stage_extractor`
    -   **Configuration Files**: `config/patterns.json` (loaded via `mapping_utils.config_loader`)

-   **`config_loader.py`**: (Potentially older version, `mapping_utils.config_loader` seems more specific)
    -   **Standard Libraries**: `json`, `sys`, `typing`
    -   **Configuration Files**: Loads a config file (path provided).

-   **`requirements.txt`**: Lists Python package dependencies for the `python/` modules.
-   **`__init__.py`**: Makes `python/` a package.

## GUI Components (`python/gui_components/`)

-   **`status_manager.py`**: Manages status updates, progress, and logging in the GUI.
    -   **Standard Libraries**: `datetime`, `threading`, `tkinter`, `typing`, `re`, `time`
    -   **Local Dependencies**:
        -   `python.gui_components.progress_panel.StageStatus` (and by extension, `ProgressPanel`)

-   **`theme_manager.py`**: Handles appearance modes, color themes, and icon loading.
    -   **Libraries**: `tkinter`, `tkinter.ttk`, `customtkinter`, `typing`, `PIL.Image`, `PIL.ImageDraw`, `io`, `os`
    -   **Data Files**: Loads icons from `icons/*.png` (e.g., `folder_closed_24.png`).

-   **`file_operations_manager.py`**: Manages file copy/move operations.
    -   **Standard Libraries**: `os`, `threading`, `uuid`, `concurrent.futures`, `typing`
    -   **Local Dependencies**:
        -   `python.file_operations_utils.file_management` (functions like `copy_item`, `move_item`)

-   **`tree_manager.py`**: Manages tree views (source and preview) and their population.
    -   **Standard Libraries**: `os`, `tkinter`, `typing`, `pathlib.Path`, `uuid`

-   **`widget_factory.py`**: Creates and configures all GUI widgets.
    -   **Libraries**: `tkinter`, `tkinter.ttk`, `tkinter.filedialog`, `customtkinter`, `os`
    -   **Local Dependencies**:
        -   `python.gui_components.progress_panel.ProgressPanel`
        -   `python.gui_components.file_operations_progress.FileOperationsProgressPanel` (which is a CTkFrame, the window is `FileOperationsProgressWindow`)

-   **`scan_manager.py`**: Handles scanning operations and queue management for the GUI.
    -   **Standard Libraries**: `os`, `threading`, `traceback`, `tkinter`, `queue.Queue`, `typing`

-   **`settings_manager.py`**: Manages application settings and UI state persistence.
    -   **Standard Libraries**: `json`, `os`, `pathlib.Path`, `typing`, `concurrent.futures`
    -   **Configuration Files**: `user_settings.json` (located at the project root).

-   **`progress_panel.py`**: Defines `ProgressPanel` (a `CTkToplevel` window) for multi-stage scan progress.
    -   **Libraries**: `tkinter`, `customtkinter`, `typing`, `enum.Enum`, `time`

-   **`file_operations_progress.py`**: Defines `FileOperationsProgressWindow` (a `CTkToplevel`) and `FileOperationsProgressPanel` (a `CTkFrame`) for file operation progress.
    -   **Libraries**: `tkinter`, `customtkinter`, `typing`, `threading`, `time`

-   **`__init__.py`**: Makes `python/gui_components/` a package.

## Mapping Utilities (`python/mapping_utils/`)

This directory contains various helper modules for the `mapping.py` module. Most of these import standard libraries like `re`, `os`, `sys`, `typing`, `pathlib.Path`.

-   **`init_patterns_from_profile.py`**: Initializes patterns from `patterns.json`.
-   **`generate_mappings.py`**: Core logic for generating mappings from a file tree and profile.
-   **`group_image_sequences.py`**: Groups individual files into image sequences.
-   **`finalize_sequences.py`**: Final processing for identified sequences.
-   **`is_network_path.py`**: Checks if a path is a network path.
-   **`create_sequence_mapping.py`**: Creates mapping for a sequence.
    -   **Local Dependencies**: `.pattern_cache`, `.generate_simple_target_path`
-   **`create_simple_mapping.py`**: Creates mapping for a single file.
    -   **Local Dependencies**: `.pattern_cache`, `.generate_simple_target_path`
-   **`generate_simple_target_path.py`**: Constructs the target path based on rules and extracted parts.
-   **`extract_sequence_info.py`**: Extracts base name, frame, suffix from filenames.
-   **`process_file_for_sequence.py`**: Helper for sequence grouping.
-   **`config_loader.py`**: Loads JSON configuration files (specifically `patterns.json`).
-   **Extractor Modules**:
    -   `shot_extractor.py`
    -   `task_extractor.py`
    -   `version_extractor.py`
    -   `resolution_extractor.py`
    -   `asset_extractor.py`
    -   `stage_extractor.py`
    (These typically use `re` for pattern matching against filenames.)
-   **`pattern_cache.py`**: Caches results of pattern extraction to improve performance.
    -   **Standard Libraries**: `typing`, `functools.lru_cache`, `hashlib`
    -   **Local Dependencies**: Imports all the extractor modules (e.g., `.shot_extractor`).
-   **`normalize_patterns.py`**: Normalizes regex patterns.
-   **`__init__.py`**: Makes `python/mapping_utils/` a package.

## File Operations Utilities (`python/file_operations_utils/`)

-   **`file_management.py`**: Contains functions for copying and moving files and sequences, including platform-specific optimizations (robocopy, xcopy).
    -   **Standard Libraries**: `os`, `shutil`, `logging`, `threading`, `time`, `subprocess`, `sys`, `pathlib.Path`, `typing`
-   **`__init__.py`**: Makes `python/file_operations_utils/` a package.

## Configuration and Data Files

-   **`config/` (Directory)**:
    -   **`patterns.json`**: Defines regex patterns for shots, tasks, versions, resolutions, assets, stages. Used by `MappingGenerator` (via `mapping_utils.config_loader`).
    -   **`profiles.json`**: Defines normalization profiles, including folder structure rules and keywords. Used by `GuiNormalizerAdapter`.
-   **`themes/` (Directory)**:
    -   **`custom_blue.json`**: A CustomTkinter JSON theme file.
-   **`icons/` (Directory)**:
    -   Contains various `.png` files used as icons in the GUI (e.g., `folder_closed_24.png`, `file_24.png`). Loaded by `ThemeManager`.
-   **`user_settings.json`**: (Located at the project root) Stores user-specific UI state and settings. Managed by `SettingsManager`

## Temporary/Generated Files & Directories

-   **`python/_progress/` (Directory)**: Used by `FileSystemScanner` to store temporary JSON files tracking scan progress (e.g., `progress_<batch_id>.json`).

## External Libraries (主なもの)

-   **`customtkinter`**: For the modern GUI elements.
-   **`Pillow (PIL)`**: Used by `ThemeManager` for image manipulation (though primarily for loading icons in the current context).

## Markdown Files (User-mentioned, for context review by AI)

-   `README.md`
-   `TASKS.md`
-   `CURSOR_RULES.md`
-   `SETTINGS_PERFORMANCE_FIX.md`
-   `GRAPHICAL_JSON_EDITORS_SUMMARY.md`
-   `SMB_PERFORMANCE_GUIDE.md`
-   `SEQUENCE_OPTIMIZATION_COMPLETION_SUMMARY.md`
-   `SEQUENCE_OPTIMIZATION_TASKS.md`
-   `PATH_GENERATION_RULES.md`
-   `PROGRESS_PANEL_GUIDE.md`
-   `PROGRESS_ENHANCEMENT_SUMMARY.md`
-   `GUI_MODULARIZATION_SUMMARY.md`
-   `adapter_insights_and_testing.md`
-   `TASK_PLAN_TKINTER.md`
-   `TASKS_TO_DO.md`
-   `IMPORTANT.md`
-   `network.md`
-   `apprules.md` (referred to by user as `@apprules.md`)

This map provides an overview. Deeper analysis of each file would reveal more granular interactions. 