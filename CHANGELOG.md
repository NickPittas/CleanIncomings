# Changelog

All notable changes to the CleanIncomings project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Complete PyQt5 UI Conversion**: Full migration from tkinter/customtkinter to PyQt5
  - New PyQt5-based main application (`app_gui_pyqt5.py`)
  - Nuke-style dark theme with professional appearance
  - HiDPI display support with proper scaling
  - Modular and resizable UI components

- **Enhanced Widget Factory**: New PyQt5 widget factory (`widget_factory_pyqt5.py`)
  - Reusable UI component creation methods
  - Icon caching and management system
  - Compact and accent button styles
  - Tree widget compatibility methods
  - Support for various widget types (buttons, labels, trees, etc.)

- **PyQt5-Compatible Core Components**:
  - `scan_manager.py` - Updated for PyQt5 tree widgets
  - `status_manager_pyqt5.py` - Progress tracking and status updates
  - `settings_manager_pyqt5.py` - UI state persistence with PyQt5 geometry
  - `tree_manager_pyqt5.py` - Tree widget management and operations

- **Advanced UI Features**:
  - Settings window with tabbed interface
  - JSON pattern editor with syntax highlighting
  - Profile management dialog
  - Resizable splitter panels
  - Compact button layouts for better space utilization
  - Professional icon integration from Nuke icon set

- **Improved User Experience**:
  - Responsive layouts that adapt to different screen sizes
  - Better visual hierarchy with proper typography
  - Enhanced accessibility with tooltips and clear labeling
  - Smooth drag-and-drop operations
  - Real-time status updates during operations

- **SettingsWindow**: Created `settings_window_pyqt5.py`
- **JsonPatternEditor**: Created `json_pattern_editor_pyqt5.py`
- **ProfileEditor**: Created `profile_editor_pyqt5.py`
- **ProgressPanel**: Created `progress_panel_pyqt5.py`
- **VlcPlayerWindow**: Created `vlc_player_pyqt5.py`

### Changed
- **UI Framework Migration**: Complete transition from tkinter to PyQt5
- **Theme System**: Replaced customtkinter styling with comprehensive PyQt5 stylesheets
- **Component Architecture**: Improved modularity and separation of concerns
- **Layout Management**: Enhanced responsive design with proper DPI scaling
- **Icon System**: Centralized icon management with caching for better performance
- **SettingsWindow**: Implemented full functionality for `settings_window_pyqt5.py`, including tab creation, settings loading/saving, and action buttons.

### Technical Improvements
- **Code Quality**: Adherence to PEP 8 standards and coding best practices
- **File Structure**: Maintained <500 lines per file, one class per module
- **Error Handling**: Robust error handling with specific exception types
- **Compatibility**: Maintained backward compatibility with existing functionality
- **Performance**: Optimized UI updates and reduced resource usage

### Fixed
- **Geometry Restoration**: Fixed window position and size persistence
- **Tree Widget Operations**: Corrected PyQt5 tree widget method calls
- **Import Dependencies**: Resolved import conflicts between tkinter and PyQt5
- **HiDPI Scaling**: Fixed display issues on high-resolution monitors
- **Threading**: Improved thread-safe UI updates for scan operations
- **widget_factory_pyqt5.py**: Completed the `add_tree_item` method.

### Developer Notes
- All tkinter references have been replaced with PyQt5 equivalents
- Widget factory provides abstraction layer for consistent UI creation
- Settings manager handles PyQt5-specific geometry serialization
- Tree managers use PyQt5 QTreeWidget API instead of tkinter Treeview
- Status manager provides thread-safe progress updates

### Migration Guide
- Old tkinter application: `python app_gui.py`
- New PyQt5 application: `python app_gui_pyqt5.py`
- All functionality preserved with enhanced UI experience
- Settings and profiles automatically migrate to new format

### Compatibility
- **Python**: 3.8+
- **PyQt5**: 5.15+
- **Operating Systems**: Windows (HiDPI support), macOS, Linux
- **Dependencies**: See requirements.txt for complete list

### Known Issues
- VLC player integration needs PyQt5 adaptation (planned for next release)
- Some advanced features require additional PyQt5 components
- Performance optimization ongoing for large file sets

---

## Previous Versions

### [1.0.0] - Initial Release
- Initial tkinter-based GUI implementation
- Core file normalization functionality
- Basic pattern matching and organization
- Profile management system
- Multi-threaded scanning and operations

---

**Note**: This changelog reflects the major PyQt5 conversion effort. For detailed commit history and smaller changes, please refer to the Git repository.
