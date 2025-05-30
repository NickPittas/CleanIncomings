"""
Theme Manager Module

Handles appearance modes, color themes, and treeview styling
for the Clean Incomings GUI application.
Enhanced with VS Code-inspired themes and panel variations.
Now includes proper CTkImage-based icon system.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw
import io
import os


class ThemeManager:
    """Manages themes, appearance modes, styling, and icons for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the ThemeManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        
        # Available appearance modes
        self.appearance_modes = ["Light", "Dark", "System"]
        
        # VS Code-inspired themes with panel variations
        self.vs_code_themes = {
            "Default Blue": {
                "primary": "#007ACC",
                "secondary": "#1E1E1E", 
                "accent": "#0E639C",
                "bg_light": "#F3F3F3",
                "bg_dark": "#252526",
                "text_light": "#000000",
                "text_dark": "#CCCCCC"
            },
            "Dark Plus": {
                "primary": "#264F78",
                "secondary": "#1E1E1E",
                "accent": "#0078D4", 
                "bg_light": "#FFFFFF",
                "bg_dark": "#1E1E1E",
                "text_light": "#000000",
                "text_dark": "#D4D4D4"
            },
            "Light Plus": {
                "primary": "#005A9F",
                "secondary": "#F8F8F8",
                "accent": "#0066B8",
                "bg_light": "#FFFFFF", 
                "bg_dark": "#F8F8F8",
                "text_light": "#000000",
                "text_dark": "#383A42"
            },
            "Monokai": {
                "primary": "#F92672",
                "secondary": "#272822",
                "accent": "#A6E22E",
                "bg_light": "#F8F8F2",
                "bg_dark": "#272822", 
                "text_light": "#272822",
                "text_dark": "#F8F8F2"
            },
            "Solarized Dark": {
                "primary": "#268BD2",
                "secondary": "#002B36",
                "accent": "#2AA198",
                "bg_light": "#FDF6E3",
                "bg_dark": "#002B36",
                "text_light": "#002B36", 
                "text_dark": "#839496"
            },
            "Solarized Light": {
                "primary": "#268BD2", 
                "secondary": "#FDF6E3",
                "accent": "#2AA198",
                "bg_light": "#FDF6E3",
                "bg_dark": "#EEE8D5",
                "text_light": "#002B36",
                "text_dark": "#657B83"
            },
            "GitHub Dark": {
                "primary": "#58A6FF",
                "secondary": "#0D1117", 
                "accent": "#238636",
                "bg_light": "#FFFFFF",
                "bg_dark": "#0D1117",
                "text_light": "#24292F",
                "text_dark": "#F0F6FC"
            },
            "GitHub Light": {
                "primary": "#0969DA",
                "secondary": "#FFFFFF",
                "accent": "#1A7F37", 
                "bg_light": "#FFFFFF",
                "bg_dark": "#F6F8FA",
                "text_light": "#24292F",
                "text_dark": "#656D76"
            },
            "One Dark Pro": {
                "primary": "#61AFEF",
                "secondary": "#282C34",
                "accent": "#98C379",
                "bg_light": "#FAFAFA",
                "bg_dark": "#282C34",
                "text_light": "#383A42",
                "text_dark": "#ABB2BF"
            },
            "Material Ocean": {
                "primary": "#82AAFF", 
                "secondary": "#0F111A",
                "accent": "#C3E88D",
                "bg_light": "#FFFFFF",
                "bg_dark": "#0F111A", 
                "text_light": "#2E3C43",
                "text_dark": "#B2CCD6"
            }
        }
        
        # Panel shade variations (relative to base theme)
        self.panel_shades = {
            "source": 5,      # +5% lighter (source browser)
            "preview": 0,     # Base color (preview panel)  
            "progress": -2,   # -2% darker (progress panel)
            "log": -5,        # -5% darker (log panel)
            "control": 3      # +3% lighter (control panel)
        }
        
        # Load CTkImage icons
        self.icon_cache = {}
        self._create_icons()
        
        print(f"Created {len(self.icon_cache)} icons successfully")
    
    def _create_icons(self):
        """Load actual icon files from the icons folder."""
        import os
        
        try:
            icons_dir = "icons"
            if not os.path.exists(icons_dir):
                print(f"Icons directory not found: {icons_dir}")
                return
                
            # Icon file mapping - use 24px size for better visibility
            icon_files = {
                "folder_closed": "folder_closed_24.png",
                "folder_open": "folder_open_24.png", 
                "file": "file_24.png",
                "sequence": "sequence_24.png",
                "video": "video_24.png",
                "image": "image_24.png",
                "audio": "audio_24.png",
                "asset": "asset_24.png",
                "task": "task_24.png",
                "arrow_right": "arrow_right_24.png",
                "arrow_down": "arrow_down_24.png",
                "arrow_up": "arrow_up_24.png",
                "refresh": "refresh_24.png",
                "settings": "settings_24.png",
                "success": "file_24.png",  # Use file icon as placeholder
                "warning": "file_24.png",
                "error": "file_24.png",
                "info": "file_24.png",
            }
            
            # Load each icon file
            for icon_name, filename in icon_files.items():
                filepath = os.path.join(icons_dir, filename)
                try:
                    if os.path.exists(filepath):
                        # Load PIL image
                        pil_image = Image.open(filepath)
                        # Create CTkImage with proper size (20x20 for display)
                        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(20, 20))
                        self.icon_cache[icon_name] = ctk_image
                    else:
                        print(f"Icon file not found: {filepath}")
                except Exception as e:
                    print(f"Error loading icon {icon_name}: {e}")
            
            print(f"Created {len(self.icon_cache)} icons successfully")
            
        except Exception as e:
            print(f"Error creating icons: {e}")
            # Fallback to empty cache
            self.icon_cache = {}
    
    def get_icon(self, icon_name: str) -> Optional[ctk.CTkImage]:
        """Get an icon by name, returns None if not found."""
        return self.icon_cache.get(icon_name)
    
    def get_icon_image(self, icon_name: str) -> Optional[ctk.CTkImage]:
        """Get CTkImage object for use in buttons and labels."""
        return self.icon_cache.get(icon_name)
    
    def get_icon_text(self, icon_name: str) -> str:
        """Get fallback text for icons when CTkImage is not available."""
        icon_text_map = {
            "folder_closed": "📁",
            "folder_open": "📂", 
            "file": "📄",
            "sequence": "🎬",
            "video": "🎥",
            "image": "🖼️",
            "audio": "🎵",
            "asset": "🎨",
            "task": "⚙️",
            "arrow_right": "▶",
            "arrow_down": "▼",
            "arrow_up": "▲",
            "refresh": "🔄",
            "settings": "⚙️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        return icon_text_map.get(icon_name, "")

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.vs_code_themes.keys())
    
    @property
    def color_themes(self) -> List[str]:
        """Get list of available color theme names (for backward compatibility)."""
        return list(self.vs_code_themes.keys())
    
    def calculate_panel_color(self, base_color: str, panel_type: str) -> str:
        """
        Calculate panel-specific color based on base color and panel type.
        
        Args:
            base_color: Base hex color (e.g., "#1E1E1E")
            panel_type: Type of panel ("source", "preview", "progress", "log", "control")
            
        Returns:
            Adjusted hex color string
        """
        if panel_type not in self.panel_shades:
            return base_color
            
        shade_percent = self.panel_shades[panel_type]
        return self._adjust_color_brightness(base_color, shade_percent)
    
    def _adjust_color_brightness(self, hex_color: str, percent: int) -> str:
        """
        Adjust the brightness of a hex color by a percentage.
        
        Args:
            hex_color: Hex color string (e.g., "#1E1E1E")
            percent: Percentage to adjust (-100 to +100)
            
        Returns:
            Adjusted hex color string
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16) 
        b = int(hex_color[4:6], 16)
        
        # Adjust brightness
        factor = percent / 100.0
        if factor > 0:
            # Lighten - move towards white
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)
        else:
            # Darken - move towards black
            r = int(r * (1 + factor))
            g = int(g * (1 + factor))
            b = int(b * (1 + factor))
        
        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_theme_colors(self, theme_name: str, appearance_mode: str) -> Dict[str, str]:
        """
        Get color configuration for a specific theme and appearance mode.
        
        Args:
            theme_name: Name of the VS Code theme
            appearance_mode: "Light" or "Dark"
            
        Returns:
            Dictionary containing color mappings
        """
        if theme_name not in self.vs_code_themes:
            theme_name = "Default Blue"  # Fallback
            
        theme = self.vs_code_themes[theme_name]
        is_dark = appearance_mode.lower() == "dark"
        
        return {
            "primary": theme["primary"],
            "secondary": theme["secondary"],
            "accent": theme["accent"],
            "background": theme["bg_dark"] if is_dark else theme["bg_light"],
            "text": theme["text_dark"] if is_dark else theme["text_light"]
        }
    
    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Handle appearance mode change."""
        ctk.set_appearance_mode(new_appearance_mode)
        self.app.current_appearance_mode = new_appearance_mode
        
        # Save setting
        if hasattr(self.app, 'settings_manager'):
            self.app.settings_manager.save_ui_state('appearance_mode', new_appearance_mode)
        
        # Apply theme colors
        self.apply_current_theme()
    
    def change_color_theme(self, theme_name: str):
        """
        Change the current color theme.
        
        Args:
            theme_name: Name of the theme to apply
        """
        self.app.current_color_theme = theme_name
        
        # Save setting
        if hasattr(self.app, 'settings_manager'):
            self.app.settings_manager.save_ui_state('color_theme', theme_name)
        
        # Apply theme
        self.apply_current_theme()
    
    def change_color_theme_event(self, theme_name: str):
        """Handle color theme change event (backward compatibility)."""
        self.change_color_theme(theme_name)
    
    def apply_current_theme(self):
        """Apply the current theme to all widgets."""
        if not hasattr(self.app, 'current_color_theme'):
            return
            
        theme_colors = self.get_theme_colors(
            self.app.current_color_theme, 
            self.app.current_appearance_mode
        )
        
        # Apply to accent widgets
        if hasattr(self.app, 'accent_widgets'):
            for widget in self.app.accent_widgets:
                try:
                    if hasattr(widget, 'configure'):
                        widget.configure(
                            fg_color=theme_colors["accent"],
                            hover_color=self._adjust_color_brightness(theme_colors["accent"], -15)
                        )
                except Exception as e:
                    print(f"Error applying theme to widget: {e}")
        
        # Apply panel-specific colors
        self._apply_panel_themes(theme_colors)
    
    def _apply_panel_themes(self, theme_colors: Dict[str, str]):
        """Apply panel-specific color themes."""
        panel_widgets = {
            "source": getattr(self.app, 'source_panel_frame', None),
            "preview": getattr(self.app, 'preview_panel_frame', None), 
            "progress": getattr(self.app, 'progress_panel_frame', None),
            "log": getattr(self.app, 'log_panel_frame', None),
            "control": getattr(self.app, 'control_panel_frame', None)
        }
        
        for panel_type, panel_widget in panel_widgets.items():
            if panel_widget and hasattr(panel_widget, 'configure'):
                try:
                    panel_color = self.calculate_panel_color(theme_colors["background"], panel_type)
                    panel_widget.configure(fg_color=panel_color)
                except Exception as e:
                    print(f"Error applying {panel_type} panel theme: {e}")
    
    def get_treeview_style_config(self) -> Dict[str, any]:
        """Get treeview styling configuration for current theme."""
        return {
            "font": ("Segoe UI", 10),
            "rowheight": 26,
            "selectmode": "extended"
        }

    def setup_treeview_style(self):
        """Sets up the treeview styling based on current theme and appearance mode."""
        style = ttk.Style(self.app)
        current_mode = ctk.get_appearance_mode()

        # Get current theme colors
        theme_colors = self.get_current_theme_colors()
        
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

        # Use theme colors for selection
        selected_color = theme_colors["primary"]
        header_active_bg_color = theme_colors["secondary"]

        # Determine selected_text_color based on the selected_color's brightness
        try:
            r, g, b = self.app.winfo_rgb(selected_color)
            brightness = (r/256 * 0.299 + g/256 * 0.587 + b/256 * 0.114)
            selected_text_color = "#000000" if brightness > 128 else "#FFFFFF"
        except tk.TclError:
            selected_text_color = "#FFFFFF" if current_mode == "Dark" else "#000000"

        style.theme_use("default")  # Start with a basic theme to override for ttk

        # Configure tree view with larger font for better icon visibility
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        borderwidth=1,
                        relief="solid",
                        font=('Segoe UI', 11),  # Larger font for better icon display
                        rowheight=26)  # Taller rows for better icon spacing
        style.map("Treeview",
                  background=[('selected', selected_color), ('focus', selected_color)],
                  foreground=[('selected', selected_text_color), ('focus', selected_text_color)])

        style.configure("Treeview.Heading",
                        background=header_bg_color,
                        foreground=header_text_color,
                        font=('Segoe UI', 10, 'bold'),  # Slightly larger header font
                        relief="flat",
                        padding=(5, 5))
        style.map("Treeview.Heading",
                  background=[('active', header_active_bg_color), ('!active', header_bg_color)],
                  relief=[('active', 'groove')])

        # Apply to treeviews if they exist
        if hasattr(self.app, 'source_tree'):
            self.app.source_tree.configure(style="Treeview")
        if hasattr(self.app, 'preview_tree'):
            self.app.preview_tree.configure(style="Treeview")

        self.app.update_idletasks()
        self.app.update()

    def get_current_theme_colors(self) -> Dict[str, str]:
        """Get current theme colors based on selected theme and mode."""
        current_theme = getattr(self.app, 'current_color_theme', 'Default Blue')
        current_mode = ctk.get_appearance_mode().lower()
        
        return self.get_theme_colors(current_theme, current_mode)

    def apply_panel_colors(self):
        """Apply shade variations to different panels."""
        try:
            current_mode = ctk.get_appearance_mode()
            
            # Get base frame color from current theme
            base_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][0 if current_mode == "Light" else 1]
            
            # Apply to specific panels if they exist
            panels = {
                'source_tree_frame': 'source',
                'preview_frame': 'preview', 
                'progress_panel_frame': 'progress',
                'log_frame': 'log'
            }
            
            for panel_attr, panel_type in panels.items():
                if hasattr(self.app, panel_attr):
                    panel = getattr(self.app, panel_attr)
                    adjusted_color = self.calculate_panel_color(base_color, panel_type)
                    if hasattr(panel, 'configure'):
                        panel.configure(fg_color=adjusted_color)
                        
        except Exception as e:
            print(f"Error applying panel colors: {e}")

    def update_theme_widgets(self, theme_name: str):
        """Update widgets with custom theme colors."""
        current_mode = ctk.get_appearance_mode()
        
        # Get theme colors
        theme_colors = self.get_current_theme_colors()
        
        for widget in getattr(self.app, 'accent_widgets', []):
            try:
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(
                        fg_color=theme_colors["primary"], 
                        hover_color=theme_colors["secondary"],
                        border_color=theme_colors["accent"]
                    )
                
                elif isinstance(widget, (ctk.CTkComboBox, ctk.CTkOptionMenu)):
                    widget.configure(
                        fg_color=theme_colors["primary"],
                        button_color=theme_colors["primary"],
                        button_hover_color=theme_colors["secondary"],
                        dropdown_fg_color=theme_colors["accent"]
                    )
            except Exception as e:
                print(f"Error applying theme to widget {widget}: {e}") 