"""
ImageViewer: QWidget for displaying images with zoom/pan and overlays.
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QWheelEvent, QMouseEvent
from PyQt5.QtCore import Qt, QRectF
import numpy as np

class ImageViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.qimage = None
        self.zoom = 1.0
        self.pan = [0, 0]
        self.last_mouse_pos = None
        self.setMinimumSize(320, 240)
        self.setMouseTracking(True)

    def set_image(self, arr):
        """Set the image as a numpy array (float32, RGB)."""
        if arr is None:
            self.image = None
            self.qimage = None
            self.update()
            return
        self.image = arr
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        h, w = arr.shape[:2]
        self.qimage = QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.qimage:
            # Center and scale
            w, h = self.qimage.width(), self.qimage.height()
            zw, zh = w * self.zoom, h * self.zoom
            x = (self.width() - zw) / 2 + self.pan[0]
            y = (self.height() - zh) / 2 + self.pan[1]
            target = QRectF(x, y, zw, zh)
            painter.drawImage(target, self.qimage)

    def wheelEvent(self, event: QWheelEvent):
        angle = event.angleDelta().y()
        factor = 1.2 if angle > 0 else 0.8
        self.zoom = max(0.05, min(self.zoom * factor, 20.0))
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_mouse_pos is not None:
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.pan[0] += dx
            self.pan[1] += dy
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = None
