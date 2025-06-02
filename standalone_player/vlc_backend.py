"""
Phase 2: VLC Backend Integration for Standalone Player

- Embeds VLC video playback in the player window
- Handles play/pause/stop, seek, and frame/time display
- Prepares for zoom/pan integration in later steps
"""
import sys
import vlc
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class VLCVideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def set_media(self, media_path):
        media = self.instance.media_new(media_path)
        self.mediaplayer.set_media(media)
        if sys.platform.startswith('linux'):
            self.mediaplayer.set_xwindow(self.winId())
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(self.winId())
        elif sys.platform == "darwin":
            self.mediaplayer.set_nsobject(int(self.winId()))

    def play(self):
        self.mediaplayer.play()

    def pause(self):
        self.mediaplayer.pause()

    def stop(self):
        self.mediaplayer.stop()

    def set_position(self, pos):
        self.mediaplayer.set_position(pos)

    def get_position(self):
        return self.mediaplayer.get_position()

    def is_playing(self):
        return self.mediaplayer.is_playing()

    def release(self):
        self.mediaplayer.release()
        self.instance.release()
