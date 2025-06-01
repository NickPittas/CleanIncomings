# PyQt5 Conversion Plan for CleanIncomings

## Overview
Converting the tkinter/customtkinter UI to a beautiful, minimal, dark PyQt5 interface inspired by Foundry Nuke.

## Files to Convert
Based on TKINTER_UI.md, the following files need conversion:

1. **app_gui.py** (main application)
2. **python/gui_components/widget_factory.py** (main widget factory)
3. **python/gui_components/vlc_player_window.py** (VLC player window)
4. **python/gui_components/progress_panel.py** (progress panel)
5. **python/gui_components/file_operations_progress.py** (file operations progress)
6. **python/gui_components/batch_edit_dialog.py** (batch edit dialog)
7. **python/gui_components/json_editors/PatternsEditorWindow.py** (patterns editor)
8. **python/gui_components/json_editors/ProfilesEditorWindow.py** (profiles editor)

## Complete UI Components Inventory

### Main Application (app_gui.py + widget_factory.py)

#### Top Control Frame
- **Profile Selection**: CTkLabel + CTkComboBox (readonly, 200px width)
- **Source Folder**: CTkButton ("Select Source") + CTkEntry (editable path)
- **Destination Folder**: CTkButton ("Select Destination") + CTkEntry (editable path) 
- **Action Buttons**: CTkButton ("Refresh/Scan", 150px) + CTkButton ("Settings", 130px)
- **Theme Controls**: CTkLabel ("Mode") + CTkOptionMenu + CTkLabel ("Theme") + CTkOptionMenu

#### Main Layout - Resizable Paned Windows
- **Main Vertical Pane**: ttk.PanedWindow (separates content from bottom)
- **Main Horizontal Pane**: ttk.PanedWindow (source tree + preview)

#### Source Tree Section
- **Header Frame**: CTkLabel ("Source Folder Structure") + CTkButton ("Show All", 90px)
- **Source Tree**: ttk.Treeview (columns: "type", "size")
  - Column #0: Name (150px min)
  - Column type: Type (80px, center)
  - Column size: Size (80px, right-aligned)

#### Preview Section  
- **Header Frame**: 
  - CTkLabel ("Preview & Actions")
  - Sort controls: CTkLabel ("Sort") + CTkOptionMenu (Filename/Task/Asset/Destination/Type, 100px) + CTkButton (sort direction toggle, 30px)
  - Filter controls: CTkLabel ("Filter") + CTkComboBox (All/Sequences/Files, 100px)
  - Selection buttons: CTkButton ("Select Sequences", 160px) + CTkButton ("Select Files", 130px) + CTkButton ("Clear", 90px)
  - CTkButton ("Batch Edit", 110px)

- **Stats Frame**: CTkLabel (selection statistics)

- **Preview Tree**: ttk.Treeview (columns: filename, task, asset, new_path, tags)
  - Column #0: Checkbox (40px, center)
  - Column filename: File/Sequence Name (200px min 150px)
  - Column task: Task (80px min 60px) - Editable
  - Column asset: Asset (80px min 60px) - Editable  
  - Column new_path: New Destination Path (350px min 200px, stretches)
  - Column tags: Matched Tags (150px min 100px)

- **Scrollbars**: Horizontal + Vertical scrollbars for preview tree

- **Action Buttons**: CTkButton ("Copy Selected") + CTkButton ("Move Selected")

- **Info Display**: CTkFrame with placeholder info (60px height)

#### Bottom Sections
- **Status Frame**: 
  - CTkLabel (main status message)
  - CTkLabel (transfer details - speed/ETA)

- **Log Frame** (Collapsible):
  - **Log Header**: CTkButton (toggle arrow, 30px) + CTkLabel ("Application Logs") + CTkButton ("Clear", 90px)
  - **Log Content**: CTkTextbox (word wrap, disabled state)

#### Progress Panels (Popup Windows)
- **ProgressPanel**: CTkToplevel (700x500px, topmost)
- **FileOperationsProgressPanel**: CTkToplevel (file operation progress)

### VLC Player Window (vlc_player_window.py)
- **Main Window**: CTkToplevel (800x650px)
- **Media Player Controls**: Play/pause/stop buttons, zoom controls
- **Video Display Area**: Embedded VLC player widget

### JSON Editors
- **PatternsEditorWindow**: CTkToplevel for editing patterns.json
- **ProfilesEditorWindow**: CTkToplevel for editing profiles.json
- **Batch Edit Dialog**: CTkToplevel for batch editing selected items

## PyQt5 Equivalents Mapping

| CustomTkinter Component | PyQt5 Equivalent | Notes |
|------------------------|------------------|--------|
| ctk.CTk | QMainWindow | Main application window |
| ctk.CTkToplevel | QDialog/QMainWindow | Secondary windows |
| ctk.CTkFrame | QFrame/QWidget | Container widgets |
| ctk.CTkLabel | QLabel | Text labels |
| ctk.CTkButton | QPushButton | Buttons |
| ctk.CTkEntry | QLineEdit | Text input fields |
| ctk.CTkComboBox | QComboBox | Dropdown selections |
| ctk.CTkOptionMenu | QComboBox | Option menus |
| ctk.CTkTextbox | QTextEdit | Multi-line text |
| ttk.Treeview | QTreeWidget | Tree displays |
| ttk.PanedWindow | QSplitter | Resizable panes |
| ttk.Scrollbar | QScrollBar | Scrollbars (built into Qt widgets) |

## Nuke-Style Dark Theme Specifications

### Color Palette (Nuke-inspired)
- **Background**: #393939 (dark gray)
- **Panel Background**: #4a4a4a (lighter gray)
- **Text**: #cccccc (light gray)
- **Accent**: #ff6600 (orange - Nuke's signature color)
- **Selection**: #ff6600 with transparency
- **Border**: #2a2a2a (darker border)
- **Button Hover**: #5a5a5a
- **Disabled**: #666666

### Typography
- **Font Family**: "Segoe UI" or "Arial"
- **Button Font**: 12px, regular weight
- **Header Font**: 14px, bold weight  
- **Label Font**: 12px, regular weight
- **Log Font**: 10px, monospace preferred

### Styling Elements
- **Corner Radius**: 6px (minimal rounded corners)
- **Border Width**: 1px
- **Button Height**: 28px standard, 25px for small buttons
- **Icon Size**: 16px for most icons, 24px for main actions
- **Spacing**: 5px standard padding, 10px between sections

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create PyQt5 theme stylesheet
2. Convert main application window (app_gui.py)
3. Convert widget factory base structure

### Phase 2: Main Components  
1. Convert top control frame
2. Convert resizable layout (QSplitter)
3. Convert source tree section
4. Convert preview section

### Phase 3: Secondary Components
1. Convert progress panels
2. Convert VLC player window
3. Convert JSON editors
4. Convert batch edit dialog

### Phase 4: Polish & Integration
1. Apply Nuke-style dark theme
2. Add proper icon integration
3. Test all functionality
4. Performance optimization

## Critical Preservation Requirements

### Function Names & Signatures
- All method names must remain identical
- All variable names must remain identical  
- All signal/callback connections must remain identical
- All public interfaces must remain identical

### Application Logic
- Profile loading/saving logic
- File scanning and mapping logic
- Tree population and selection logic
- File operations (copy/move) logic
- Settings management logic

### Data Flow
- StringVar equivalents (QLineEdit.text() or custom properties)
- Tree item data storage and retrieval
- Progress reporting mechanisms
- Logging system integration

## Icon Integration Plan
Available Nuke icons in `icons/` folder can be used for:
- Folder icons: `folder_open_16.png`, `folder_closed_16.png` 
- File type icons: `file_16.png`, `sequence_16.png`, `image_16.png`, `video_16.png`, `audio_16.png`
- UI actions: `settings_16.png`, `refresh_16.png`, `arrow_*_16.png`
- Media controls: `media_play.png`, `media_pause.png`, `media_stop.png`
- Tasks: `task_16.png`, `asset_16.png`

## Testing Requirements
- All button clicks must trigger correct functions
- All menu selections must work
- All text field updates must propagate correctly
- All tree operations must function (expand, select, right-click)
- All progress reporting must display correctly
- All dialogs must open and close properly
- Theme switching must work
- File operations must complete successfully

## Risk Mitigation
- Create backup copies of original files
- Implement conversion one file at a time
- Test each component thoroughly before proceeding
- Maintain detailed changelog of all changes
- Create rollback plan if issues arise
