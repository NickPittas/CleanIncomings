import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QOpenGLWidget, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPainter

class ImageSequenceWidget(QOpenGLWidget):
    """
    Widget for playback of image sequences using OpenCV backend.
    Supports play, pause, stop, seek, and frame navigation.
    Handles large images (up to 12K x 12K) with LRU frame caching.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.files = []
        self.fps = 24.0
        self.current_frame_idx = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        self.frame_cache = {}
        self.cache_size = 3  # LRU cache for 3 frames
        self.is_playing = False
        self.error_message = None
        self.setMinimumSize(320, 240)

    def set_sequence(self, files, fps=24.0):
        self.files = files
        self.fps = fps
        self.current_frame_idx = 0
        self.frame_cache.clear()
        self.error_message = None
        self.update()

    def play(self):
        if not self.files:
            return
        self.is_playing = True
        self.timer.start(int(1000 / self.fps))

    def pause(self):
        self.is_playing = False
        self.timer.stop()

    def stop(self):
        self.is_playing = False
        self.timer.stop()
        self.current_frame_idx = 0
        self.update()

    def seek(self, idx):
        if not self.files:
            return
        self.current_frame_idx = max(0, min(idx, len(self.files) - 1))
        self.update()

    def _next_frame(self):
        if not self.files:
            return
        self.current_frame_idx += 1
        if self.current_frame_idx >= len(self.files):
            self.current_frame_idx = 0  # Loop
        self.update()

    def _get_frame(self, idx):
        # LRU cache logic
        if idx in self.frame_cache:
            return self.frame_cache[idx]
        path = self.files[idx]
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            self.error_message = f"Failed to load: {os.path.basename(path)}"
            return None
        # Convert BGR/GRAY to RGB for QImage
        if img.ndim == 2:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_Grayscale8)
        elif img.shape[2] == 4:
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_RGBA8888)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        # LRU cache update
        self.frame_cache[idx] = qimg
        if len(self.frame_cache) > self.cache_size:
            # Remove least-recently-used
            oldest = sorted(self.frame_cache.keys())[0]
            del self.frame_cache[oldest]
        return qimg

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.files:
            painter.fillRect(self.rect(), Qt.black)
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Sequence Loaded")
            return
        frame = self._get_frame(self.current_frame_idx)
        if frame is None:
            painter.fillRect(self.rect(), Qt.black)
            painter.setPen(Qt.red)
            painter.drawText(self.rect(), Qt.AlignCenter, self.error_message or "Frame Load Error")
            return
        # Center the frame
        w, h = frame.width(), frame.height()
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        painter.drawImage(x, y, frame)

    def sizeHint(self):
        return self.minimumSize()

    def get_position(self):
        if not self.files:
            return 0.0
        return self.current_frame_idx / max(1, len(self.files) - 1)

    def set_position(self, pos):
        if not self.files:
            return
        idx = int(pos * (len(self.files) - 1))
        self.seek(idx)

    def get_timecode(self):
        if not self.files:
            return "00:00:00"
        frame = self.current_frame_idx
        seconds = int(frame / self.fps)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}:{frame % int(self.fps):02d}"

    def is_playing_state(self):
        return self.is_playing

    def step_frame(self, step):
        if not self.files:
            return
        self.seek(self.current_frame_idx + step)
