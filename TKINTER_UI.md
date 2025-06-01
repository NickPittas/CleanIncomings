# Files using tkinter / customtkinter

Below is every module that directly imports `tkinter` or `customtkinter`. 
These are candidates for porting to PyQt5.

- python/app_gui.py  
  (imports `customtkinter as ctk`, defines `CleanIncomingsApp(ctk.CTk)`)

- python/gui_components/widget_factory.py  
  (imports `tkinter as tk`, `from tkinter import ttk, filedialog, messagebox`, `import customtkinter as ctk`)

- python/gui_components/vlc_player_window.py  
  (imports `tkinter as tk`, `import customtkinter as ctk`)

- python/gui_components/progress_panel.py  
  (imports `tkinter` or `customtkinter`)

- python/gui_components/file_operations_progress.py  
  (imports `tkinter` or `customtkinter`)

- python/gui_components/batch_edit_dialog.py  
  (imports `tkinter` or `customtkinter`)

- python/gui_components/json_editors/PatternsEditorWindow.py  
  (imports `tkinter` or `customtkinter`)

- python/gui_components/json_editors/ProfilesEditorWindow.py  
  (imports `tkinter` or `customtkinter`)