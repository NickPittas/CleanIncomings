# CleanIncomings: Folder Normalization Utility

## Overview

CleanIncomings is a Python-based desktop application designed to scan, normalize, and organize incoming files and folders, particularly tailored for VFX and creative project workflows. It provides a graphical user interface built with `tkinter` and `customtkinter` for intuitive operation. The application allows users to define normalization rules through profiles and pattern configurations, ensuring consistent project structures.

## Features

*   **GUI Interface**: Modern and user-friendly interface built with `customtkinter`.
*   **Modular Design**: The application is broken down into several manageable components for better maintainability and scalability:
    *   **Status Management** ([`StatusManager`](g:\My Drive\python\CleanIncomings\python\gui_components\status_manager.py)): Handles UI updates for status, progress, and logging.
    *   **Theme Management** ([`ThemeManager`](g:\My Drive\python\CleanIncomings\python\gui_components\theme_manager.py)): Manages application appearance (light/dark modes) and custom color themes.
    *   **File Operations** ([`FileOperationsManager`](g:\My Drive\python\CleanIncomings\python\gui_components\file_operations_manager.py)): Manages copy and move operations for files and sequences.
    *   **Tree View Management** ([`TreeManager`](g:\My Drive\python\CleanIncomings\python\gui_components\tree_manager.py)): Populates and manages source and preview tree views.
    *   **Scan Management** ([`ScanManager`](g:\My Drive\python\CleanIncomings\python\gui_components\scan_manager.py)): Handles folder scanning operations and result processing.
    *   **Widget Factory** ([`WidgetFactory`](g:\My Drive\python\CleanIncomings\python\gui_components\widget_factory.py)): Centralized creation and layout of all GUI widgets.
    *   **Settings Management** ([`SettingsManager`](g:\My Drive\python\CleanIncomings\python\gui_components\settings_manager.py)): Loads and saves user settings and UI state.
*   **Configurable Normalization**:
    *   Uses [`config/profiles.json`](g:\My Drive\python\CleanIncomings\config\profiles.json) to define different normalization profiles.
    *   Relies on [`config/patterns.json`](g:\My Drive\python\CleanIncomings\config\patterns.json) for regex and keyword patterns used in file/folder name parsing.
*   **Asynchronous Operations**: Scanning and file operations are performed in background threads to keep the UI responsive.
*   **Detailed Progress Reporting**: Multi-stage progress panels ([`ProgressPanel`](g:\My Drive\python\CleanIncomings\python\gui_components\progress_panel.py), [`FileOperationsProgressPanel`](g:\My Drive\python\CleanIncomings\python\gui_components\file_operations_progress.py)) provide feedback during lengthy operations.
*   **Sequence Handling**: Specialized logic for identifying and processing image sequences.
*   **Persistent Settings**: User preferences and UI state are saved in [`user_settings.json`](g:\My Drive\python\CleanIncomings\user_settings.json).

## Technology Stack

*   **Language**: Python
*   **GUI**: `tkinter`, `customtkinter`
*   **Core Logic**: Custom Python modules for scanning ([`scanner.py`](g:\My Drive\python\CleanIncomings\python\scanner.py)), mapping ([`mapping.py`](g:\My Drive\python\CleanIncomings\python\mapping.py)), and GUI adaptation ([`gui_normalizer_adapter.py`](g:\My Drive\python\CleanIncomings\python\gui_normalizer_adapter.py)).
*   **Packaging**: PyInstaller (see [`CleanIncomings.spec`](g:\My Drive\python\CleanIncomings\CleanIncomings.spec) and [`app_gui.spec`](g:\My Drive\python\CleanIncomings\app_gui.spec)).

## Project Structure

The application is organized into several key directories:

*   **`python/`**: Contains the core backend logic and GUI components.
    *   `gui_components/`: Modules for different parts of the GUI.
    *   `mapping_utils/`: Helper modules for the normalization mapping logic.
    *   `file_operations_utils/`: Utilities for file copy/move operations.
*   **`config/`**: Holds configuration files like `patterns.json` and `profiles.json`.
*   **`themes/`**: Custom themes for `customtkinter` (e.g., [`custom_blue.json`](g:\My Drive\python\CleanIncomings\themes\custom_blue.json)).
*   **`icons/`**: UI icons.

For a detailed file map and dependencies, please refer to [MAP.md](g:\My Drive\python\CleanIncomings\MAP.md).

## Configuration

Normalization behavior is primarily controlled by two JSON files:

*   **[`config/patterns.json`](g:\My Drive\python\CleanIncomings\config\patterns.json)**: Defines regex patterns and keywords for identifying various parts of filenames (e.g., shot codes, task names, versions, resolutions).
*   **[`config/profiles.json`](g:\My Drive\python\CleanIncomings\config\profiles.json)**: Contains different profiles that specify how files should be organized. Each profile can define target folder structures based on the keywords matched by `patterns.json`.

User-specific settings, such as the last used folders or UI theme, are stored in [`user_settings.json`](g:\My Drive\python\CleanIncomings\user_settings.json) at the project root.

## Getting Started

### Prerequisites

*   Python 3.x
*   `pip` for installing dependencies

### Installation

1.  Clone the repository:
    ```sh
    git clone <repository-url>
    cd CleanIncomings
    ```
2.  Install Python dependencies:
    ```sh
    pip install -r python/requirements.txt
    ```
    (Note: `python/requirements.txt` is listed in [MAP.md](g:\My Drive\python\CleanIncomings\MAP.md) as the dependency file for python modules.)

### Running the Application

Execute the main GUI script:

```sh
python app_gui.py
```

## Testing

The project aims for high test coverage for core logic.
*   Property-based tests for normalization logic using Hypothesis.
*   Unit tests for individual modules.
*   Component tests for UI interactions (mocking IPC/DB where applicable, though this app is primarily local filesystem based).
*   E2E tests simulating user workflows.

(Refer to specific test files and testing guidelines within the project for detailed commands, if available.)

## Coding Standards & Contribution

*   **Python**: Adherence to PEP8, formatted with `black`, linted with `flake8`.
*   **File Structure**: Max 500 lines per file, one class/module per file (ideally < 100 lines per class).
*   **Configuration Driven**: Normalization logic is driven by configuration files, avoiding hardcoded patterns.
*   **Modularity**: Code is organized into logical, reusable components.

For detailed coding standards, AI assistant rules, and contribution guidelines, please see [.github/copilot-instructions.md](g:\My Drive\python\CleanIncomings\.github\copilot-instructions.md).
Refer to [IMPORTANT.md](g:\My Drive\python\CleanIncomings\IMPORTANT.md) for critical guidelines on mapping and normalization logic.
Path generation rules are detailed in [PATH_GENERATION_RULES.md](g:\My Drive\python\CleanIncomings\PATH_GENERATION_RULES.md).