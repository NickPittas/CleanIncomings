"""
Standalone Nuke-style Media Player Main Window (Phase 1 Skeleton)

- Dark theme, playback bar, zoom/pan controls (UI placeholders)
- No playback logic yet (Phase 1)
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

class PlayerWindow(QMainWindow):
    def __init__(self, media_path=None):
        super().__init__()
        self.setWindowTitle("Nuke-Style Media Player")
        self.setGeometry(100, 100, 1280, 720)
        self._apply_dark_theme()
        self._init_ui()
        self._connect_signals()
        self._init_timer()
        if media_path:
            self.load_media(media_path)

    def _apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(40, 40, 40))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(60, 120, 180))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)
        # Apply dark stylesheet for all widgets
        self.setStyleSheet('''
            QMainWindow { background: #1e1e1e; }
            QWidget { background: #232323; color: #e0e0e0; }
            QPushButton { background: #222; color: #eee; border: 1px solid #444; border-radius: 4px; padding: 6px 10px; }
            QPushButton:disabled { background: #222; color: #444; border: 1px solid #333; }
            QPushButton:hover { background: #333; }
            QSlider::groove:horizontal { background: #444; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #888; border: 1px solid #222; width: 12px; margin: -4px 0; border-radius: 6px; }
            QLabel { color: #e0e0e0; }
        ''')

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Dynamic Display Area: ImageViewer for sequences, VLCVideoWidget for video
        from widgets.image_viewer import ImageViewer
        self.display_area = ImageViewer(self)
        self.display_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.display_area)
        self._main_layout = layout  # for future use

        # Color Space Dropdown
        from PyQt5.QtWidgets import QComboBox
        self.cmb_colorspace = QComboBox()
        self.cmb_colorspace.addItems(["rec709", "srgb", "acescg", "linear"])
        self.cmb_colorspace.setCurrentText("rec709")
        layout.addWidget(self.cmb_colorspace)

        # Memory Limit Slider
        self.mem_slider = QSlider(Qt.Horizontal)
        self.mem_slider.setMinimum(1)
        self.mem_slider.setMaximum(128)
        self.mem_slider.setValue(128)
        self.mem_slider.setTickInterval(8)
        self.mem_slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(QLabel("Preload Memory Limit (GB):"))
        layout.addWidget(self.mem_slider)
        self.lbl_memval = QLabel("128 GB")
        layout.addWidget(self.lbl_memval)
        self.mem_slider.valueChanged.connect(lambda v: self.lbl_memval.setText(f"{v} GB"))

        # Playback bar
        playback_bar = QHBoxLayout()
        self.btn_play = QPushButton(self.style().standardIcon(QStyle.SP_MediaPlay), "")
        self.btn_pause = QPushButton(self.style().standardIcon(QStyle.SP_MediaPause), "")
        self.btn_stop = QPushButton(self.style().standardIcon(QStyle.SP_MediaStop), "")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.lbl_time = QLabel("00:00 / 00:00")
        playback_bar.addWidget(self.btn_play)
        playback_bar.addWidget(self.btn_pause)
        playback_bar.addWidget(self.btn_stop)
        playback_bar.addWidget(self.slider, 1)
        playback_bar.addWidget(self.lbl_time)
        layout.addLayout(playback_bar)

        # Zoom & Pan controls
        controls_bar = QHBoxLayout()
        self.btn_zoom_in = QPushButton("Zoom +")
        self.btn_zoom_out = QPushButton("Zoom -")
        self.btn_zoom_fit = QPushButton("Fit")
        self.btn_pan_left = QPushButton("←")
        self.btn_pan_right = QPushButton("→")
        self.btn_pan_up = QPushButton("↑")
        self.btn_pan_down = QPushButton("↓")
        # Disable zoom/pan buttons (not implemented)
        for btn in [self.btn_zoom_in, self.btn_zoom_out, self.btn_zoom_fit, self.btn_pan_left, self.btn_pan_right, self.btn_pan_up, self.btn_pan_down]:
            btn.setEnabled(False)
        controls_bar.addWidget(self.btn_zoom_in)
        controls_bar.addWidget(self.btn_zoom_out)
        controls_bar.addWidget(self.btn_zoom_fit)
        controls_bar.addWidget(self.btn_pan_left)
        controls_bar.addWidget(self.btn_pan_right)
        controls_bar.addWidget(self.btn_pan_up)
        controls_bar.addWidget(self.btn_pan_down)
        layout.addLayout(controls_bar)

        # Keyboard shortcuts
        self._init_shortcuts()

    def _connect_signals(self):
        self.btn_play.clicked.connect(self.play_media)
        self.btn_pause.clicked.connect(self.pause_media)
        self.btn_stop.clicked.connect(self.stop_media)
        self.slider.sliderMoved.connect(self.seek_media)

    def _init_timer(self):
        from PyQt5.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # ms
        self.timer.timeout.connect(self._update_ui)
        self.timer.start()

    def _init_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        QShortcut(QKeySequence("Space"), self, self.play_pause_toggle)
        QShortcut(QKeySequence("S"), self, self.stop_media)
        QShortcut(QKeySequence("Left"), self, lambda: self._step_frame(-1))
        QShortcut(QKeySequence("Right"), self, lambda: self._step_frame(1))

    def load_media(self, media_path):
        # Wire up image sequence playback
        import os
        from sequence_loader import SequenceLoader
        import image_decode
        self.sequence_loader = None
        self.frame_idx = 0
        self.timer = None
        self.is_playing = False
        self.loop = True
        self.color_space = self.cmb_colorspace.currentText()
        self.mem_limit = self.mem_slider.value()
        self.cmb_colorspace.currentTextChanged.connect(self._on_colorspace_changed)
        self.mem_slider.valueChanged.connect(self._on_memlimit_changed)
        self.btn_play.clicked.connect(self._on_play)
        self.btn_pause.clicked.connect(self._on_pause)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self._image_decode = image_decode

        try:
            self.sequence_loader = SequenceLoader(media_path, mem_limit_gb=self.mem_limit)
        except Exception as e:
            self.display_area.set_image(None)
            self.slider.setMaximum(1)
            self.lbl_time.setText(f"Error: {e}")
            return
        num_frames = self.sequence_loader.num_frames()
        self.slider.setMaximum(max(1, num_frames-1))
        self.lbl_time.setText(f"Frame 1 / {num_frames}")
        self._show_frame(0)

    def _show_frame(self, idx):
        arr = self.sequence_loader.get_frame(idx, self._image_decode.load_image)
        arr = self._image_decode.apply_color_transform(arr, self.color_space)
        self.display_area.set_image(arr)
        self.frame_idx = idx
        self.slider.blockSignals(True)
        self.slider.setValue(idx)
        self.slider.blockSignals(False)
        self.lbl_time.setText(f"Frame {idx+1} / {self.sequence_loader.num_frames()}")

    def _on_slider_moved(self, val):
        self._show_frame(val)

    def _on_play(self):
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._on_next_frame)
        self.is_playing = True
        self.timer.start(42)  # ~24fps

    def _on_pause(self):
        if self.timer:
            self.timer.stop()
        self.is_playing = False

    def _on_next_frame(self):
        idx = (self.frame_idx + 1) % self.sequence_loader.num_frames() if self.loop else min(self.frame_idx + 1, self.sequence_loader.num_frames()-1)
        self._show_frame(idx)
        if not self.loop and idx == self.sequence_loader.num_frames()-1:
            self._on_pause()

    def _on_colorspace_changed(self, text):
        self.color_space = text
        self._show_frame(self.frame_idx)

    def _on_memlimit_changed(self, val):
        self.mem_limit = val
        # Re-initialize loader with new memory limit
        if hasattr(self, 'sequence_loader') and self.sequence_loader:
            path = self.sequence_loader.sequence_files[self.frame_idx]
            self.load_media(path)
            # Replace VLC widget with ImageSequenceWidget
            if hasattr(self, 'display_area') and self.display_area:
                self._main_layout.removeWidget(self.display_area)
                self.display_area.deleteLater()
            self.display_area = ImageSequenceWidget(self)
            self._main_layout.insertWidget(0, self.display_area)
            self.display_area.set_sequence(files)
        else:
            self.display_area.set_media(media_path)
        self.play_media()

    def play_media(self):
        if hasattr(self.display_area, 'play'):
            self.display_area.play()

    def pause_media(self):
        if hasattr(self.display_area, 'pause'):
            self.display_area.pause()

    def stop_media(self):
        if hasattr(self.display_area, 'stop'):
            self.display_area.stop()

    def play_pause_toggle(self):
        if hasattr(self.display_area, 'is_playing_state'):
            playing = self.display_area.is_playing_state()
        elif hasattr(self.display_area, 'is_playing'):
            playing = self.display_area.is_playing()
        else:
            playing = False
        if playing:
            self.pause_media()
        else:
            self.play_media()

    def seek_media(self, value):
        pos = value / 1000.0
        if hasattr(self.display_area, 'set_position'):
            self.display_area.set_position(pos)

    def _update_ui(self):
        pos = 0.0
        if hasattr(self.display_area, 'get_position'):
            pos = self.display_area.get_position()
        if pos is not None:
            self.slider.blockSignals(True)
            self.slider.setValue(int(pos * 1000))
            self.slider.blockSignals(False)
        if hasattr(self.display_area, 'get_timecode'):
            self.lbl_time.setText(self.display_area.get_timecode())
        else:
            mp = self.display_area.mediaplayer
            length = mp.get_length() / 1000.0 if mp else 0
            time = mp.get_time() / 1000.0 if mp else 0
            self.lbl_time.setText(f"{self._format_time(time)} / {self._format_time(length)}")

    def _format_time(self, seconds):
        if seconds is None or seconds < 0:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def _step_frame(self, step):
        if hasattr(self.display_area, 'step_frame'):
            self.display_area.step_frame(step)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Standalone Nuke-Style Media Player")
    parser.add_argument("media", nargs="?", help="Path to media file to play")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    window = PlayerWindow(media_path=args.media)
    window.show()
    sys.exit(app.exec_())
