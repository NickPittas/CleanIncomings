import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import sys
from PIL import Image

# Attempt to import vlc, will be None if app_gui.py failed to import it
try:
    import vlc
except ImportError:
    vlc = None

class VLCPlayerWindow(ctk.CTkToplevel):
    def __init__(self, parent, media_path: str):
        super().__init__(parent)
        self.title("Embedded VLC Player")
        self.geometry("800x650") # Initial size, can be adjusted
        self.parent_app = parent # Reference to the main app instance

        if vlc is None:
            error_label = ctk.CTkLabel(self, text="VLC library not found or failed to load.\nEmbedded playback is unavailable.", font=("Arial", 16))
            error_label.pack(expand=True, padx=20, pady=20)
            self.after(3000, self.destroy) # Close after a few seconds
            return

        self.media_path = media_path
        self.vlc_instance = None
        self.media_player = None
        self.is_playing = False
        self.duration_ms = 0
        self.media_info = {}
        
        # Zoom functionality
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        
        # Load media player icons
        self._load_icons()

        self._setup_ui()
        self._initialize_vlc()
        
        if self.media_player and self.media_path:
            self.load_media(self.media_path)        
            self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_icons(self):
        """Load media player icons"""
        self.icons = {}
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "icons")
        icon_size = (24, 24)
        
        icon_files = {
            'play': 'media_play.png',
            'pause': 'media_pause.png', 
            'stop': 'media_stop.png',
            'step_backward': 'media_step_backward.png',
            'step_forward': 'media_step_forward.png',
            'zoom_in': 'media_zoom_in.png',
            'zoom_out': 'media_zoom_out.png',
            'reset_zoom': 'media_reset_zoom.png'
        }
        
        for icon_name, filename in icon_files.items():
            try:
                icon_path = os.path.join(icon_dir, filename)
                if os.path.exists(icon_path):
                    image = Image.open(icon_path)
                    image = image.resize(icon_size, Image.Resampling.LANCZOS)
                    self.icons[icon_name] = ctk.CTkImage(light_image=image, dark_image=image, size=icon_size)
                else:
                    self.icons[icon_name] = None
            except Exception as e:
                print(f"Failed to load icon {filename}: {e}")
                self.icons[icon_name] = None

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Video frame
        self.grid_rowconfigure(1, weight=0) # Media info
        self.grid_rowconfigure(2, weight=0) # Seek bar
        self.grid_rowconfigure(3, weight=0) # Controls

        # Video Display Frame (this is where VLC will draw)
        self.video_frame = ctk.CTkFrame(self, fg_color="black")
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Bind mouse wheel events for zooming
        self.video_frame.bind("<MouseWheel>", self._on_mouse_wheel)
        self.bind("<MouseWheel>", self._on_mouse_wheel)  # Also bind to main window
        
        # Bind keyboard shortcuts for zoom
        self.bind("<Control-plus>", lambda e: self.zoom_in())
        self.bind("<Control-equal>", lambda e: self.zoom_in())  # = key (shift not needed)
        self.bind("<Control-minus>", lambda e: self.zoom_out())
        self.bind("<Control-0>", lambda e: self.reset_zoom())
        self.focus_set()  # Ensure window can receive keyboard events

        # Media Info Frame
        self.media_info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.media_info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        self.media_info_label = ctk.CTkLabel(self.media_info_frame, text="", font=("Arial", 10))
        self.media_info_label.pack(side="left")

        # Seek Bar
        self.seek_slider_var = tk.DoubleVar()
        self.seek_slider = ctk.CTkSlider(
            self, 
            from_=0, 
            to=100, 
            variable=self.seek_slider_var, 
            command=self._on_seek,
            height=20,
            button_color=("#1f538d", "#14375e"),
            button_hover_color=("#2562a8", "#1c4676"),
            progress_color=("#1f538d", "#14375e")
        )
        self.seek_slider.grid(row=2, column=0, sticky="ew", padx=10, pady=8)
        self.seek_slider.set(0) # Initialize

        # Time Labels Frame (overlaid on seek bar area)
        self.time_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_label_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=8) # Overlay on slider row
        
        self.current_time_label = ctk.CTkLabel(self.time_label_frame, text="00:00:00", font=("Arial", 9))
        self.current_time_label.pack(side="left")
        
        self.total_time_label = ctk.CTkLabel(self.time_label_frame, text="00:00:00", font=("Arial", 9))
        self.total_time_label.pack(side="right")

        # Controls Frame - Properly centered
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=3, column=0, pady=15)
        
        # Create buttons with icons and proper centering
        button_config = {
            'width': 50,
            'height': 40,
            'font': ("Arial", 10)
        }

        # Frame step backward button
        self.frame_prev_button = ctk.CTkButton(
            controls_frame, 
            text="◀◀" if not self.icons.get('step_backward') else "",
            image=self.icons.get('step_backward'),
            command=self.frame_step_backward,
            **button_config
        )
        self.frame_prev_button.grid(row=0, column=0, padx=8)

        # Play/Pause button  
        self.play_pause_button = ctk.CTkButton(
            controls_frame,
            text="▶" if not self.icons.get('play') else "",
            image=self.icons.get('play'),
            command=self.toggle_play_pause,
            width=60,
            height=40,
            font=("Arial", 12)
        )
        self.play_pause_button.grid(row=0, column=1, padx=8)

        # Stop button
        self.stop_button = ctk.CTkButton(
            controls_frame,
            text="■" if not self.icons.get('stop') else "",
            image=self.icons.get('stop'),
            command=self.stop_media,
            **button_config
        )
        self.stop_button.grid(row=0, column=2, padx=8)
        
        # Frame step forward button
        self.frame_next_button = ctk.CTkButton(
            controls_frame,
            text="▶▶" if not self.icons.get('step_forward') else "",
            image=self.icons.get('step_forward'),
            command=self.frame_step_forward,
            **button_config
        )
        self.frame_next_button.grid(row=0, column=3, padx=8)

        # Zoom in button
        self.zoom_in_button = ctk.CTkButton(
            controls_frame,
            text="🔍+" if not self.icons.get('zoom_in') else "",
            image=self.icons.get('zoom_in'),
            command=self.zoom_in,
            **button_config
        )
        self.zoom_in_button.grid(row=0, column=4, padx=8)

        # Zoom out button
        self.zoom_out_button = ctk.CTkButton(
            controls_frame,
            text="🔍-" if not self.icons.get('zoom_out') else "",
            image=self.icons.get('zoom_out'),
            command=self.zoom_out,
            **button_config
        )
        self.zoom_out_button.grid(row=0, column=5, padx=8)

        # Reset zoom button
        self.reset_zoom_button = ctk.CTkButton(
            controls_frame,
            text="⌂" if not self.icons.get('reset_zoom') else "",
            image=self.icons.get('reset_zoom'),
            command=self.reset_zoom,
            **button_config
        )
        self.reset_zoom_button.grid(row=0, column=6, padx=8)


    def _initialize_vlc(self):
        try:
            # VLC Instance options (can be customized)
            # Example: --no-xlib for headless if needed, or other interface options
            # For now, default options are fine.
            self.vlc_instance = vlc.Instance()
            self.media_player = self.vlc_instance.media_player_new()

            # Set the window handle for the video frame
            # Needs to happen after the window is visible and IDs are assigned.
            self.after(100, self._set_vlc_hwnd)

            # Event Manager
            events = self.media_player.event_manager()
            events.event_attach(vlc.EventType.MediaPlayerTimeChanged, self._on_time_changed)
            events.event_attach(vlc.EventType.MediaPlayerPositionChanged, self._on_position_changed)
            events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
            events.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
            events.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
            events.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)

        except Exception as e:
            print(f"Error initializing VLC: {e}")
            messagebox.showerror("VLC Error", f"Failed to initialize VLC components: {e}")
            self.destroy()

    def _set_vlc_hwnd(self):
        if self.media_player and self.video_frame.winfo_exists():
            try:
                if sys.platform.startswith('win32'):
                    self.media_player.set_hwnd(self.video_frame.winfo_id())
                elif sys.platform.startswith('linux'):
                    self.media_player.set_xwindow(self.video_frame.winfo_id())
                # macOS might need set_nsobject, which is more complex.
                # For now, focusing on Windows/Linux.
            except Exception as e:
                print(f"Error setting HWND for VLC: {e}")
    def load_media(self, media_path: str):
        if not self.media_player or not media_path or not os.path.exists(media_path):
            print(f"VLC: Media path invalid or player not initialized: {media_path}")
            return
        
        # Normalize path for VLC (especially on Windows)        
        normalized_path = os.path.normpath(media_path)
        if sys.platform.startswith('win32'):
            # For file URIs, VLC might prefer forward slashes
            normalized_path = normalized_path.replace('\\', '/')
            if not normalized_path.startswith('file:///'):
                normalized_path = 'file:///' + normalized_path

        media = self.vlc_instance.media_new(normalized_path)
        self.media_player.set_media(media)
        
        # Set initial play button state with icon
        if self.icons.get('play'):
            self.play_pause_button.configure(image=self.icons['play'], text="", state="normal")
        else:
            self.play_pause_button.configure(text="▶", image=None, state="normal")
            
        self.seek_slider.set(0)
        self.current_time_label.configure(text="00:00:00")
        
        # Get duration after media is parsed (might take a moment)
        self.after(500, self._get_media_duration)
        self._get_media_info(media_path)
    def _get_media_duration(self):
        if self.media_player:
            self.duration_ms = self.media_player.get_length()
            if self.duration_ms <= 0: # Sometimes takes longer to parse
                self.after(500, self._get_media_duration) # Retry
            else:
                self.total_time_label.configure(text=self._format_time(self.duration_ms))
                self.seek_slider.configure(to=self.duration_ms)

    def _get_media_info(self, media_path):
        """Extract and display media information"""
        filename = os.path.basename(media_path)
        file_size = os.path.getsize(media_path) / (1024 * 1024)  # MB
        
        # Basic info to display
        info_text = f"File: {filename} | Size: {file_size:.1f} MB"
        
        # Try to get additional media info when VLC has processed the media
        self.media_info_label.configure(text=info_text)
        self.after(1000, lambda: self._update_media_info_from_vlc(info_text))
    
    def _update_media_info_from_vlc(self, base_info):
        """Update media info with VLC-provided details"""
        if not self.media_player:
            return
            
        try:
            # Get additional VLC media information
            fps = self.media_player.get_fps()
            video_size = self.media_player.video_get_size()
            
            enhanced_info = base_info
            if fps > 0:
                enhanced_info += f" | FPS: {fps:.1f}"
            if video_size and video_size != (0, 0):
                enhanced_info += f" | Resolution: {video_size[0]}x{video_size[1]}"
                
            self.media_info_label.configure(text=enhanced_info)
        except Exception as e:
            print(f"Error getting VLC media info: {e}")
    def toggle_play_pause(self):
        if not self.media_player:
            return
        if self.media_player.is_playing():
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_media(self):
        if self.media_player:
            self.media_player.stop()
            # Update button to show play icon/text
            if self.icons.get('play'):
                self.play_pause_button.configure(image=self.icons['play'], text="")
            else:
                self.play_pause_button.configure(text="▶", image=None)
            self.seek_slider.set(0)
            self.current_time_label.configure(text="00:00:00")
            self.is_playing = False

    def frame_step_forward(self):
        if self.media_player:
            # VLC's next_frame might not be reliable or might advance too much.
            # A common workaround is to pause, then seek slightly if next_frame isn't precise.
            # For now, let's try the direct approach if available, or a small seek.
            if self.media_player.is_seekable():
                current_time = self.media_player.get_time()
                fps = self.media_player.get_fps()
                if fps == 0: fps = 25 # Default if not available
                frame_duration = 1000 / fps
                self.media_player.set_time(int(current_time + frame_duration))
                if not self.media_player.is_playing(): # If paused, play and pause to refresh frame
                    self.media_player.play()
                    self.after(int(frame_duration/2) if frame_duration > 20 else 10, self.media_player.pause)


    def frame_step_backward(self):
        if self.media_player and self.media_player.is_seekable():
            current_time = self.media_player.get_time()
            fps = self.media_player.get_fps()
            if fps == 0: fps = 25 # Default
            frame_duration = 1000 / fps
            new_time = int(current_time - frame_duration)
            self.media_player.set_time(max(0, new_time))
            if not self.media_player.is_playing():
                self.media_player.play()
                self.after(int(frame_duration/2) if frame_duration > 20 else 10, self.media_player.pause)


    def _on_seek(self, value_str):
        if self.media_player and self.media_player.is_seekable():
            # Value from slider is already in ms if 'to' is set to duration_ms
            self.media_player.set_time(int(float(value_str)))

    def _on_time_changed(self, event):
        current_time_ms = event.u.new_time
        self.current_time_label.configure(text=self._format_time(current_time_ms))
        # Only update slider if not currently being dragged by user (to avoid jitter)
        # This needs a flag, for now, direct update.
        self.seek_slider.set(current_time_ms)


    def _on_position_changed(self, event):
        # Position is 0.0 to 1.0. We are using time_changed for slider.
        # If using position:
        # new_position = event.u.new_position
        # self.seek_slider.set(new_position * self.duration_ms)
        pass

    def _on_playing(self, event):
        # Update button to show pause icon/text
        if self.icons.get('pause'):
            self.play_pause_button.configure(image=self.icons['pause'], text="")
        else:
            self.play_pause_button.configure(text="⏸", image=None)
        self.is_playing = True
        if self.duration_ms <= 0: # If duration wasn't fetched yet
            self._get_media_duration()

    def _on_paused(self, event):
        # Update button to show play icon/text
        if self.icons.get('play'):
            self.play_pause_button.configure(image=self.icons['play'], text="")
        else:
            self.play_pause_button.configure(text="▶", image=None)
        self.is_playing = False

    def _on_stopped(self, event):
        # Update button to show play icon/text
        if self.icons.get('play'):
            self.play_pause_button.configure(image=self.icons['play'], text="")
        else:
            self.play_pause_button.configure(text="▶", image=None)
        self.seek_slider.set(0)
        self.current_time_label.configure(text="00:00:00")
        self.is_playing = False

    def _on_end_reached(self, event):
        self.media_player.stop() # Prevent auto-close on video end

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling for zoom"""
        if not self.media_player:
            return
            
        # event.delta is positive for scroll up, negative for scroll down
        # On Windows, delta is typically 120 or -120
        zoom_change = self.zoom_step if event.delta > 0 else -self.zoom_step
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_change))
        
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self._apply_zoom()

    def _apply_zoom(self):
        """Apply the current zoom factor to the video"""
        if not self.media_player:
            return
            
        try:
            # VLC uses scale factor for video zoom
            self.media_player.video_set_scale(self.zoom_factor)
            
            # Update window title to show zoom level
            zoom_percent = int(self.zoom_factor * 100)
            base_title = "Embedded VLC Player"
            if self.zoom_factor != 1.0:
                self.title(f"{base_title} - Zoom: {zoom_percent}%")
            else:
                self.title(base_title)
                
        except Exception as e:
            print(f"Error applying zoom: {e}")

    def reset_zoom(self):
        """Reset zoom to fit window (1.0 scale)"""
        self.zoom_factor = 1.0
        self._apply_zoom()

    def zoom_in(self):
        """Zoom in by one step"""
        new_zoom = min(self.max_zoom, self.zoom_factor + self.zoom_step)
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self._apply_zoom()

    def zoom_out(self):
        """Zoom out by one step"""
        new_zoom = max(self.min_zoom, self.zoom_factor - self.zoom_step)
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self._apply_zoom()

    def _format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"

    def _on_closing(self):
        print("VLC Player Window: Closing and releasing resources.")
        if self.media_player:
            self.media_player.stop()
            self.media_player.release()
            self.media_player = None
        if self.vlc_instance:
            self.vlc_instance.release()
            self.vlc_instance = None
        self.destroy()

if __name__ == '__main__':
    # This is for testing the VLCPlayerWindow independently
    # You'll need a sample video file to test.
    # Ensure VLC is installed or libvlc is findable by your system PATH for this test.
    
    # Create a dummy root window for testing
    root = ctk.CTk()
    root.withdraw() # Hide the dummy root

    # IMPORTANT: For this standalone test to find VLC DLLs, 
    # you might need to have your VLC installation directory in your system PATH,
    # or ensure the libvlc setup from app_gui.py (if run from project root) has executed.
    # The VLC path configuration in app_gui.py is designed for when the app runs as a whole.
    
    # Path to a sample video file (replace with an actual path on your system)
    # For example: sample_video_path = "C:/Users/YourUser/Videos/sample.mp4"
    sample_video_path = "path/to/your/sample/video.mp4" # REPLACE THIS

    if os.path.exists(sample_video_path) and vlc is not None:
        player_window = VLCPlayerWindow(root, sample_video_path)
        player_window.mainloop() # This is not standard for CTkToplevel, usually parent's loop runs
    elif vlc is None:
        print("VLC module not loaded. Cannot run standalone test.")
    else:
        print(f"Sample video not found at: {sample_video_path}. Cannot run standalone test.")
    
    root.quit() # Ensure main loop exits if it was started implicitly
