"""
Theme Manager Module

Handles appearance modes, color themes, and treeview styling
for the Clean Incomings GUI application.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List


class ThemeManager:
    """Manages themes, appearance modes, and styling for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the ThemeManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.appearance_modes = ["Light", "Dark", "System"]
        self.color_themes = ["blue", "green", "dark-blue"]

    def change_appearance_mode_event(self, new_mode: str):
        """Handles changing the appearance mode."""
        ctk.set_appearance_mode(new_mode)
        self.setup_treeview_style()  # Re-apply style for Treeview
        self.app.status_label.configure(text=f"Appearance mode changed to {new_mode}")

    def change_color_theme_event(self, new_color_theme: str):
        """Handles changing the color theme."""
        ctk.set_default_color_theme(new_color_theme)
        
        current_mode = ctk.get_appearance_mode()
        mode_idx = 0 if current_mode == "Light" else 1

        for widget in self.app.accent_widgets:
            try:
                if isinstance(widget, ctk.CTkButton):
                    fg_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"][mode_idx]
                    hover_color = ctk.ThemeManager.theme["CTkButton"]["hover_color"][mode_idx]
                    border_color = ctk.ThemeManager.theme["CTkButton"]["border_color"][mode_idx]
                    text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"][mode_idx]
                    widget.configure(fg_color=fg_color, hover_color=hover_color, border_color=border_color, text_color=text_color)
                
                elif isinstance(widget, (ctk.CTkComboBox, ctk.CTkOptionMenu)):
                    # For ComboBox and OptionMenu, colors are slightly different
                    # Main widget part (looks like a button)
                    fg_color = ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"][mode_idx]
                    hover_color = ctk.ThemeManager.theme["CTkOptionMenu"]["button_hover_color"][mode_idx]
                    text_color = ctk.ThemeManager.theme["CTkOptionMenu"]["text_color"][mode_idx]
                    
                    widget.configure(fg_color=fg_color,
                                     button_color=fg_color,
                                     button_hover_color=hover_color,
                                     text_color=text_color,
                                     dropdown_fg_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_fg_color"][mode_idx],
                                     dropdown_hover_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_hover_color"][mode_idx],
                                     dropdown_text_color=ctk.ThemeManager.theme["CTkOptionMenu"]["dropdown_text_color"][mode_idx]
                                     )
            except Exception as e:
                print(f"Error applying theme to widget {widget}: {e}")

        self.setup_treeview_style()  # Re-apply style for Treeview
        self.app.status_label.configure(text=f"Color theme changed to {new_color_theme}")
        self.app.color_theme_menu.set(new_color_theme)
        
        self.app.update_idletasks()
        self.app.update()  # Standard Tkinter updates

    def setup_treeview_style(self):
        """Sets up the treeview styling based on current theme and appearance mode."""
        style = ttk.Style(self.app)
        current_mode = ctk.get_appearance_mode()

        active_color_theme_name = self.app.color_theme_menu.get()  # e.g. "blue", "green"

        # Define base colors for Treeview (non-selected parts)
        if current_mode == "Light":
            bg_color = "#FFFFFF"  # White background for light mode
            text_color = "#000000"  # Black text for light mode
            header_bg_color = "#EAEAEA"  # Light gray for header
            header_text_color = "#000000"
        else:  # Dark Mode
            bg_color = "#2B2B2B"  # Dark gray background for dark mode
            text_color = "#FFFFFF"  # White text for dark mode
            header_bg_color = "#3C3C3C"  # Slightly lighter dark gray for header
            header_text_color = "#FFFFFF"

        # Attempt to get accent color from the current CustomTkinter theme for SELECTION
        # Default to a sensible blue if theme colors are not available or not suitable
        default_selected_fg_light = "#3B8ED0"  # Default blue for light mode selection
        default_selected_fg_dark = "#1F6AA5"   # Default blue for dark mode selection

        try:
            button_theme = ctk.ThemeManager.theme["CTkButton"]
            raw_selected_color = button_theme["fg_color"][0 if current_mode == "Light" else 1]
            raw_header_active_bg = button_theme["hover_color"][0 if current_mode == "Light" else 1]

            # Validate selected_color
            try:
                self.app.winfo_rgb(raw_selected_color)  # Test if it's a valid Tk color
                selected_color = raw_selected_color
            except tk.TclError:
                selected_color = default_selected_fg_light if current_mode == "Light" else default_selected_fg_dark

            # Validate header_active_bg_color
            try:
                self.app.winfo_rgb(raw_header_active_bg)
                header_active_bg_color = raw_header_active_bg
            except tk.TclError:
                header_active_bg_color = selected_color  # Fallback to validated selected_color

            # Determine selected_text_color based on the validated selected_color's brightness
            try:
                r, g, b = self.app.winfo_rgb(selected_color)  # Use validated selected_color
                brightness = (r/256 * 0.299 + g/256 * 0.587 + b/256 * 0.114)
                selected_text_color = "#000000" if brightness > 128 else "#FFFFFF"
            except tk.TclError:  # Should not happen if selected_color is validated, but as a safeguard
                selected_text_color = "#FFFFFF" if current_mode == "Dark" else "#000000"
                
        except (KeyError, AttributeError, TypeError):
            # Fallback for entire block if theme properties are missing
            selected_color = default_selected_fg_light if current_mode == "Light" else default_selected_fg_dark
            selected_text_color = "#FFFFFF" if (self.app.winfo_rgb(selected_color)[0]/256 * 0.299 + self.app.winfo_rgb(selected_color)[1]/256 * 0.587 + self.app.winfo_rgb(selected_color)[2]/256 * 0.114) <= 128 else "#000000"
            header_active_bg_color = selected_color

        style.theme_use("default")  # Start with a basic theme to override for ttk

        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        borderwidth=1,
                        relief="solid")
        style.map("Treeview",
                  background=[('selected', selected_color), ('focus', selected_color)],
                  foreground=[('selected', selected_text_color), ('focus', selected_text_color)])

        style.configure("Treeview.Heading",
                        background=header_bg_color,
                        foreground=header_text_color,
                        font=('Segoe UI', 9, 'bold'),
                        relief="flat",
                        padding=(5, 5))
        style.map("Treeview.Heading",
                  background=[('active', header_active_bg_color), ('!active', header_bg_color)],
                  relief=[('active', 'groove')])

        self.app.source_tree.configure(style="Treeview")
        self.app.preview_tree.configure(style="Treeview")

        self.app.update_idletasks()
        self.app.update() 