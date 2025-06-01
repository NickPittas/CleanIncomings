from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt
import vlc # Assuming python-vlc is installed
import sys
import os

class VlcPlayerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VLC Player")
        self.setMinimumSize(800, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        layout = QVBoxLayout(self)
        self.video_frame = QFrame()
        self.video_frame.setAttribute(Qt.WA_StyledBackground, True)
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame)

        # Set the window ID for VLC
        if sys.platform.startswith('linux'): # for Linux using X Server
            self.media_player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32": # for Windows
            self.media_player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin": # for macOS
            self.media_player.set_nsobject(int(self.video_frame.winId()))

    def play_media(self, media_path):
        if not os.path.exists(media_path):
            print(f"Error: Media path does not exist: {media_path}")
            return
        media = self.instance.media_new(media_path)
        self.media_player.set_media(media)
        self.media_player.play()

    def closeEvent(self, event):
        self.media_player.stop()
        super().closeEvent(event)
