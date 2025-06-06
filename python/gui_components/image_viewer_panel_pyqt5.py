"""
Collapsible Image Viewer Panel for CleanIncomings
Shows the middle frame of image sequences directly in a collapsible side panel
"""

import os
import subprocess
import platform
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QScrollArea, QGroupBox, QApplication,
    QSplitter, QMessageBox, QSlider
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QProcess, QPoint
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QColor, QWheelEvent, QMouseEvent


class ImageLoaderThread(QThread):
    """Thread for loading images without blocking the UI"""
    
    image_loaded = pyqtSignal(QPixmap)  # Emitted when image is loaded
    error_occurred = pyqtSignal(str)  # Emitted on error
    
    def __init__(self, file_path: str, max_size: QSize = None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.max_size = max_size or QSize(400, 300)
        
    def run(self):
        """Load image in a separate thread"""
        try:
            if not os.path.exists(self.file_path):
                self.error_occurred.emit(f"File not found: {self.file_path}")
                return
            
            # Try loading with Qt first
            pixmap = QPixmap(self.file_path)
            
            # If Qt can't load it (e.g., EXR files), try alternative methods
            if pixmap.isNull():
                file_ext = os.path.splitext(self.file_path)[1].lower()
                
                # For EXR and other HDR formats, try to convert using external tools
                if file_ext in ['.exr', '.hdr', '.dpx', '.cin', '.tiff', '.tif']:
                    converted_pixmap = self._try_convert_with_external_tools()
                    if converted_pixmap and not converted_pixmap.isNull():
                        pixmap = converted_pixmap
                    else:
                        # Create a placeholder for unsupported formats
                        pixmap = self._create_placeholder_image()
                else:
                    self.error_occurred.emit(f"Could not load image: {os.path.basename(self.file_path)}")
                    return
            
            # Scale the image to fit within max_size while maintaining aspect ratio
            if pixmap.width() > self.max_size.width() or pixmap.height() > self.max_size.height():
                pixmap = pixmap.scaled(
                    self.max_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
            
            self.image_loaded.emit(pixmap)
                
        except Exception as e:
            self.error_occurred.emit(f"Error loading image: {e}")
    
    def _try_convert_with_external_tools(self) -> Optional[QPixmap]:
        """Try to convert unsupported formats using external tools"""
        try:
            # Try using ffmpeg to convert to a temporary PNG
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    temp_file = f.name
                
                # Try ffmpeg conversion
                cmd = [
                    'ffmpeg', '-i', self.file_path, 
                    '-vf', f'scale={self.max_size.width()}:{self.max_size.height()}:force_original_aspect_ratio=decrease',
                    '-y', temp_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(temp_file):
                    pixmap = QPixmap(temp_file)
                    os.unlink(temp_file)  # Clean up temp file
                    return pixmap
                    
            except Exception:
                pass
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
        except Exception:
            pass
        
        return None
    
    def _create_placeholder_image(self) -> QPixmap:
        """Create a placeholder image for unsupported formats"""
        try:
            # Create a placeholder pixmap
            pixmap = QPixmap(self.max_size)
            pixmap.fill(QColor(60, 60, 60))  # Dark gray background
            
            # Draw placeholder text
            painter = QPainter(pixmap)
            painter.setPen(QColor(170, 170, 170))  # Light gray text
            painter.drawText(pixmap.rect(), Qt.AlignCenter, 
                           f"Preview not available\n\n{os.path.basename(self.file_path)}\n\nUse external viewer for full preview")
            painter.end()
            
            return pixmap
            
        except Exception:
            # Return a simple colored rectangle as last resort
            pixmap = QPixmap(200, 150)
            pixmap.fill(QColor(60, 60, 60))
            return pixmap


class ZoomableImageLabel(QLabel):
    """
    Custom QLabel that supports zoom and pan functionality
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        self.last_mouse_pos = QPoint()
        self.is_panning = False
        
        # Enable mouse tracking for smooth panning
        self.setMouseTracking(True)
        # Accept focus to receive mouse events properly
        self.setFocusPolicy(Qt.StrongFocus)
        
    def set_pixmap(self, pixmap: QPixmap):
        """Set the pixmap and reset zoom/pan"""
        self.original_pixmap = pixmap
        self.zoom_factor = 1.0
        self._update_display()
        
    def clear_image(self):
        """Clear the image and reset zoom/pan"""
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.zoom_factor = 1.0
        self.clear()
        
    def fit_to_window(self, container_size: QSize):
        """Fit image to the given container size"""
        if not self.original_pixmap:
            return
            
        # Calculate zoom factor to fit image in container
        pixmap_size = self.original_pixmap.size()
        container_size = QSize(container_size.width() - 40, container_size.height() - 40)  # Margin
        
        zoom_x = container_size.width() / pixmap_size.width()
        zoom_y = container_size.height() / pixmap_size.height()
        
        self.zoom_factor = min(zoom_x, zoom_y)
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, self.zoom_factor))
        self._update_display()
        
    def set_actual_size(self):
        """Set image to actual size (100% zoom)"""
        if not self.original_pixmap:
            return
            
        self.zoom_factor = 1.0
        self._update_display()
        
    def zoom_in(self):
        """Zoom in by the zoom step"""
        if self.original_pixmap:
            self.zoom_factor = min(self.max_zoom, self.zoom_factor + self.zoom_step)
            self._update_display()
            
    def zoom_out(self):
        """Zoom out by the zoom step"""
        if self.original_pixmap:
            self.zoom_factor = max(self.min_zoom, self.zoom_factor - self.zoom_step)
            self._update_display()
            
    def get_zoom_percentage(self) -> int:
        """Get current zoom as percentage"""
        return int(self.zoom_factor * 100)
        
    def _update_display(self):
        """Update the displayed image with current zoom and pan"""
        if not self.original_pixmap:
            return
            
        # Scale the image
        new_size = self.original_pixmap.size() * self.zoom_factor
        self.scaled_pixmap = self.original_pixmap.scaled(
            new_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Set the pixmap and adjust widget size
        self.setPixmap(self.scaled_pixmap)
        self.resize(self.scaled_pixmap.size())
        
        # Emit signal to parent about zoom change if needed
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), '_update_zoom_display'):
            try:
                self.parent().parent()._update_zoom_display()
            except:
                pass  # Ignore if method doesn't exist
            
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if not self.original_pixmap:
            return
            
        # Get the scroll direction
        delta = event.angleDelta().y()
        
        # Calculate zoom change
        if delta > 0:
            # Zoom in
            new_zoom = min(self.max_zoom, self.zoom_factor + self.zoom_step)
        else:
            # Zoom out
            new_zoom = max(self.min_zoom, self.zoom_factor - self.zoom_step)
            
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self._update_display()
            
        event.accept()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning"""
        if event.button() == Qt.MiddleButton and self.original_pixmap:
            self.is_panning = True
            self.last_mouse_pos = event.globalPos()  # Use global position for more reliable tracking
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning"""
        if self.is_panning and self.original_pixmap:
            current_global_pos = event.globalPos()
            
            # Calculate delta in global coordinates
            delta = current_global_pos - self.last_mouse_pos
            self.last_mouse_pos = current_global_pos
            
            # Get parent scroll area and adjust scroll position
            scroll_area = self.get_scroll_area()
            if scroll_area:
                h_scrollbar = scroll_area.horizontalScrollBar()
                v_scrollbar = scroll_area.verticalScrollBar()
                
                # Check if scrollbars are actually visible/needed
                h_visible = h_scrollbar.isVisible() and h_scrollbar.maximum() > 0
                v_visible = v_scrollbar.isVisible() and v_scrollbar.maximum() > 0
                
                if h_visible or v_visible:
                    old_h = h_scrollbar.value()
                    old_v = v_scrollbar.value()
                    
                    # Invert delta for natural panning feel
                    new_h = max(0, min(h_scrollbar.maximum(), old_h - delta.x()))
                    new_v = max(0, min(v_scrollbar.maximum(), old_v - delta.y()))
                    
                    h_scrollbar.setValue(new_h)
                    v_scrollbar.setValue(new_v)
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop panning"""
        if event.button() == Qt.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def get_scroll_area(self):
        """Get the parent scroll area"""
        parent = self.parent()
        # The parent should be the QScrollArea
        if hasattr(parent, 'horizontalScrollBar') and hasattr(parent, 'verticalScrollBar'):
            return parent
        # If not direct parent, try going up the hierarchy
        while parent:
            if hasattr(parent, 'horizontalScrollBar') and hasattr(parent, 'verticalScrollBar'):
                return parent
            parent = parent.parent()
        return None

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for testing"""
        if self.original_pixmap:
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.zoom_in()
                event.accept()
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
            elif event.key() == Qt.Key_0:
                self.set_actual_size()
                event.accept()
            elif event.key() == Qt.Key_F:
                # Get parent scroll area size for fit operation
                scroll_area = self.get_scroll_area()
                if scroll_area:
                    self.fit_to_window(scroll_area.size())
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class CollapsibleImageViewer(QWidget):
    """
    Collapsible image viewer panel that shows frames from image sequences with scrub control
    """
    
    # Signals
    panel_toggled = pyqtSignal(bool)  # Emitted when panel is expanded/collapsed
    
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.current_sequence_data = None
        self.current_image_loader = None
        self.current_pixmap = None
        self.current_frame_index = 0
        self.total_frames = 0
        self.sequence_files = []
        self.is_expanded = False
        self.preferred_width = 450  # Width when expanded
        self.collapsed_width = 30   # Width when collapsed
        
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)
        
        self._setup_ui()
        self._connect_signals()
        
        # Start collapsed
        self._set_collapsed_state()
        
    def _setup_ui(self):
        """Set up the user interface"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create the content area (no internal toggle button)
        self._create_content_area()
        
        # Apply initial styling
        self.setObjectName("image_viewer_panel")
        self.setStyleSheet("""
            QWidget#image_viewer_panel {
                background-color: #2b2b2b;
                border-left: 1px solid #555;
            }
            QLabel#header {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #3c3c3c;
                border-radius: 3px;
            }
            QLabel#status {
                color: #aaaaaa;
                font-size: 10px;
                padding: 5px;
            }
            QPushButton#control {
                background-color: #4a4a4a;
                border: 1px solid #666;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton#control:hover {
                background-color: #5a5a5a;
                border-color: #777;
            }
            QPushButton#control:pressed {
                background-color: #3a3a3a;
            }
            QPushButton#control:disabled {
                background-color: #333;
                color: #666;
                border-color: #444;
            }
            QPushButton#nav {
                background-color: #4a4a4a;
                border: 1px solid #666;
                color: white;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
                min-width: 30px;
            }
            QPushButton#nav:hover {
                background-color: #5a5a5a;
                border-color: #777;
            }
            QPushButton#nav:pressed {
                background-color: #3a3a3a;
            }
            QPushButton#nav:disabled {
                background-color: #333;
                color: #666;
                border-color: #444;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ff6600;
                border: 1px solid #cc5200;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff7f33;
                border-color: #e55a00;
            }
            QSlider::handle:horizontal:pressed {
                background: #e55a00;
                border-color: #b84700;
            }
        """)
    
    def _create_content_area(self):
        """Create the main content area"""
        self.content_frame = QFrame()
        self.content_frame.setObjectName("content")
        self.content_frame.setVisible(False)  # Start hidden
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)
        
        # Header
        self.header_label = QLabel("Image Viewer")
        self.header_label.setObjectName("header")
        self.header_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.header_label)
        
        # Status area
        self.status_label = QLabel("No sequence selected")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        content_layout.addWidget(self.status_label)
        
        # Image display area - scrollable for large images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setMinimumHeight(200)
        
        # Enable scroll bars when needed
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #555;
                border-radius: 5px;
                background-color: #333;
            }
        """)
        
        self.image_label = ZoomableImageLabel(self.scroll_area)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 200)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #aaa;
                border: none;
                padding: 20px;
            }
        """)
        self.image_label.setText("Select an image sequence to view frames")
        
        self.scroll_area.setWidget(self.image_label)
        content_layout.addWidget(self.scroll_area)
        
        # Frame scrub controls
        self._create_scrub_controls(content_layout)
        
        # Frame info
        self.frame_info_label = QLabel("")
        self.frame_info_label.setObjectName("status")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label.setWordWrap(True)
        content_layout.addWidget(self.frame_info_label)
        
        # Image controls
        self._create_image_controls(content_layout)
        
        content_layout.addStretch()
        self.main_layout.addWidget(self.content_frame)
    
    def _create_scrub_controls(self, parent_layout):
        """Create the frame scrubbing controls"""
        scrub_frame = QFrame()
        scrub_frame.setStyleSheet("QFrame { border: 1px solid #555; border-radius: 3px; padding: 5px; }")
        scrub_layout = QVBoxLayout(scrub_frame)
        scrub_layout.setSpacing(3)
        
        # Frame navigation buttons
        nav_layout = QHBoxLayout()
        
        self.first_frame_btn = QPushButton("⏮")
        self.first_frame_btn.setObjectName("nav")
        self.first_frame_btn.setToolTip("Go to first frame")
        self.first_frame_btn.clicked.connect(self._go_to_first_frame)
        self.first_frame_btn.setEnabled(False)
        nav_layout.addWidget(self.first_frame_btn)
        
        self.prev_frame_btn = QPushButton("◀")
        self.prev_frame_btn.setObjectName("nav")
        self.prev_frame_btn.setToolTip("Previous frame")
        self.prev_frame_btn.clicked.connect(self._go_to_prev_frame)
        self.prev_frame_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_frame_btn)
        
        nav_layout.addStretch()
        
        # Frame counter
        self.frame_counter_label = QLabel("0 / 0")
        self.frame_counter_label.setObjectName("status")
        self.frame_counter_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.frame_counter_label)
        
        nav_layout.addStretch()
        
        self.next_frame_btn = QPushButton("▶")
        self.next_frame_btn.setObjectName("nav")
        self.next_frame_btn.setToolTip("Next frame")
        self.next_frame_btn.clicked.connect(self._go_to_next_frame)
        self.next_frame_btn.setEnabled(False)
        nav_layout.addWidget(self.next_frame_btn)
        
        self.last_frame_btn = QPushButton("⏭")
        self.last_frame_btn.setObjectName("nav")
        self.last_frame_btn.setToolTip("Go to last frame")
        self.last_frame_btn.clicked.connect(self._go_to_last_frame)
        self.last_frame_btn.setEnabled(False)
        nav_layout.addWidget(self.last_frame_btn)
        
        scrub_layout.addLayout(nav_layout)
        
        # Timeline slider
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self._on_frame_slider_changed)
        self.frame_slider.setToolTip("Scrub through frames")
        scrub_layout.addWidget(self.frame_slider)
        
        parent_layout.addWidget(scrub_frame)
    
    def _create_image_controls(self, parent_layout):
        """Create image control buttons"""
        controls_layout = QHBoxLayout()
        
        # Zoom controls
        self.zoom_out_button = QPushButton("🔍−")
        self.zoom_out_button.setObjectName("control")
        self.zoom_out_button.setToolTip("Zoom out (Mouse wheel down)")
        self.zoom_out_button.clicked.connect(self._zoom_out)
        self.zoom_out_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_out_button)
        
        # Zoom percentage display
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("status")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setToolTip("Current zoom level")
        controls_layout.addWidget(self.zoom_label)
        
        self.zoom_in_button = QPushButton("🔍+")
        self.zoom_in_button.setObjectName("control")
        self.zoom_in_button.setToolTip("Zoom in (Mouse wheel up)")
        self.zoom_in_button.clicked.connect(self._zoom_in)
        self.zoom_in_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_in_button)
        
        controls_layout.addSpacing(10)
        
        # Refresh button
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setObjectName("control")
        self.refresh_button.setToolTip("Refresh the current image")
        self.refresh_button.clicked.connect(self._refresh_image)
        self.refresh_button.setEnabled(False)
        controls_layout.addWidget(self.refresh_button)
        
        # Fit to window button
        self.fit_button = QPushButton("⊞ Fit")
        self.fit_button.setObjectName("control")
        self.fit_button.setToolTip("Fit image to window")
        self.fit_button.clicked.connect(self._fit_image)
        self.fit_button.setEnabled(False)
        controls_layout.addWidget(self.fit_button)
        
        # Actual size button
        self.actual_size_button = QPushButton("1:1")
        self.actual_size_button.setObjectName("control")
        self.actual_size_button.setToolTip("Show actual size (100%)")
        self.actual_size_button.clicked.connect(self._actual_size)
        self.actual_size_button.setEnabled(False)
        controls_layout.addWidget(self.actual_size_button)
        
        # Help text for mouse controls
        help_layout = QHBoxLayout()
        help_label = QLabel("💡 Wheel: zoom • Middle-drag: pan (zoom >100% first) • +/-: zoom • F: fit")
        help_label.setObjectName("status")
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setWordWrap(True)
        help_layout.addWidget(help_label)
        
        parent_layout.addLayout(controls_layout)
        parent_layout.addLayout(help_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass
    
    def toggle_panel(self):
        """Toggle the panel between expanded and collapsed states - for external control"""
        if self.is_expanded:
            self._set_collapsed_state()
        else:
            self._set_expanded_state()
    
    def expand_panel(self):
        """Expand the panel - for external control"""
        if not self.is_expanded:
            self._set_expanded_state()
    
    def collapse_panel(self):
        """Collapse the panel - for external control"""
        if self.is_expanded:
            self._set_collapsed_state()
    
    def is_panel_expanded(self) -> bool:
        """Return whether the panel is currently expanded"""
        return self.is_expanded
    
    def _set_expanded_state(self):
        """Set the panel to expanded state"""
        self.is_expanded = True
        self.content_frame.setVisible(True)
        self.setMinimumWidth(self.preferred_width)
        self.setMaximumWidth(self.preferred_width)
        
        self.panel_toggled.emit(True)
        
        # If we have sequence data, show the image
        if self.current_sequence_data:
            self._show_current_frame()
    
    def _set_collapsed_state(self):
        """Set the panel to collapsed state"""
        self.is_expanded = False
        self.content_frame.setVisible(False)
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)
        
        # Stop any running image loader
        self._stop_current_loader()
        
        self.panel_toggled.emit(False)
    
    def set_sequence_data(self, sequence_data: Dict[str, Any]):
        """
        Set the sequence data to display
        
        Args:
            sequence_data: Rich sequence data dict with keys like 'base_name', 'files', etc.
        """
        self.current_sequence_data = sequence_data
        
        if not sequence_data:
            self.status_label.setText("No sequence selected")
            self.frame_info_label.setText("")
            self._disable_controls()
            self._clear_image()
            self._stop_current_loader()
            return
        
        # Extract sequence files and setup
        files = sequence_data.get('files', [])
        if not files:
            self.status_label.setText("No files in sequence")
            self._disable_controls()
            self._clear_image()
            return
        
        # Store sequence information
        self.sequence_files = files
        self.total_frames = len(files)
        self.current_frame_index = self.total_frames // 2  # Start with middle frame
        
        # Update UI elements
        base_name = sequence_data.get('base_name', 'Unknown')
        self.status_label.setText(f"{base_name}\n{self.total_frames} frames")
        
        # Setup frame controls
        self.frame_slider.setMaximum(self.total_frames - 1)
        self.frame_slider.setValue(self.current_frame_index)
        self._enable_controls()
        self._update_frame_counter()
        
        # If panel is expanded, show the current frame
        if self.is_expanded:
            self._show_current_frame()
    
    def _show_current_frame(self):
        """Show the currently selected frame"""
        if not self.sequence_files or self.current_frame_index >= len(self.sequence_files):
            return
        
        # Get current frame file path
        current_file = self.sequence_files[self.current_frame_index]
        if isinstance(current_file, dict):
            file_path = current_file.get('path', '')
        else:
            file_path = str(current_file)
        
        if not file_path or not os.path.exists(file_path):
            self.frame_info_label.setText("Frame file not found")
            self._clear_image()
            return
        
        # Stop any existing loader
        self._stop_current_loader()
        
        # Update frame info
        filename = os.path.basename(file_path)
        self.frame_info_label.setText(f"Loading: {filename}")
        
        # Calculate max size based on current scroll area size
        scroll_size = self.scroll_area.size()
        max_size = QSize(scroll_size.width() - 20, scroll_size.height() - 20)
        
        # Start image loading
        self.current_image_loader = ImageLoaderThread(file_path, max_size, self)
        self.current_image_loader.image_loaded.connect(self._on_image_loaded)
        self.current_image_loader.error_occurred.connect(self._on_error_occurred)
        self.current_image_loader.start()
    
    def _on_frame_slider_changed(self, value):
        """Handle frame slider value changes"""
        if value != self.current_frame_index and self.sequence_files:
            self.current_frame_index = value
            self._update_frame_counter()
            if self.is_expanded:
                self._show_current_frame()
    
    def _go_to_first_frame(self):
        """Go to the first frame"""
        if self.sequence_files:
            self.current_frame_index = 0
            self.frame_slider.setValue(self.current_frame_index)
            self._update_frame_counter()
            if self.is_expanded:
                self._show_current_frame()
    
    def _go_to_prev_frame(self):
        """Go to the previous frame"""
        if self.sequence_files and self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.frame_slider.setValue(self.current_frame_index)
            self._update_frame_counter()
            if self.is_expanded:
                self._show_current_frame()
    
    def _go_to_next_frame(self):
        """Go to the next frame"""
        if self.sequence_files and self.current_frame_index < len(self.sequence_files) - 1:
            self.current_frame_index += 1
            self.frame_slider.setValue(self.current_frame_index)
            self._update_frame_counter()
            if self.is_expanded:
                self._show_current_frame()
    
    def _go_to_last_frame(self):
        """Go to the last frame"""
        if self.sequence_files:
            self.current_frame_index = len(self.sequence_files) - 1
            self.frame_slider.setValue(self.current_frame_index)
            self._update_frame_counter()
            if self.is_expanded:
                self._show_current_frame()
    
    def _update_frame_counter(self):
        """Update the frame counter display"""
        if self.sequence_files:
            self.frame_counter_label.setText(f"{self.current_frame_index + 1} / {self.total_frames}")
        else:
            self.frame_counter_label.setText("0 / 0")
    
    def _enable_controls(self):
        """Enable frame navigation controls"""
        has_frames = bool(self.sequence_files)
        self.frame_slider.setEnabled(has_frames)
        self.first_frame_btn.setEnabled(has_frames)
        self.prev_frame_btn.setEnabled(has_frames)
        self.next_frame_btn.setEnabled(has_frames)
        self.last_frame_btn.setEnabled(has_frames)
        self.refresh_button.setEnabled(has_frames)
        
        # Enable zoom controls if we have frames
        self.zoom_in_button.setEnabled(has_frames)
        self.zoom_out_button.setEnabled(has_frames)
    
    def _disable_controls(self):
        """Disable frame navigation controls"""
        self.frame_slider.setEnabled(False)
        self.first_frame_btn.setEnabled(False)
        self.prev_frame_btn.setEnabled(False)
        self.next_frame_btn.setEnabled(False)
        self.last_frame_btn.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.fit_button.setEnabled(False)
        self.actual_size_button.setEnabled(False)
        
        # Disable zoom controls
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self.zoom_label.setText("100%")
        
        # Reset frame info
        self.current_frame_index = 0
        self.total_frames = 0
        self.sequence_files = []
        self.frame_slider.setMaximum(0)
        self.frame_slider.setValue(0)
        self._update_frame_counter()
    
    def _stop_current_loader(self):
        """Stop the current image loader"""
        if self.current_image_loader:
            self.current_image_loader.quit()
            self.current_image_loader.wait(1000)  # Wait up to 1 second
            self.current_image_loader = None
    
    def _clear_image(self):
        """Clear the current image"""
        self.current_pixmap = None
        self.image_label.clear_image()
        self.image_label.setText("Select an image sequence to view frames")
        self.fit_button.setEnabled(False)
        self.actual_size_button.setEnabled(False)
        self.zoom_label.setText("100%")
    
    def _refresh_image(self):
        """Refresh the current image"""
        if self.sequence_files and self.is_expanded:
            self._show_current_frame()
    
    def _fit_image(self):
        """Fit image to the scroll area"""
        if self.current_pixmap:
            scroll_size = self.scroll_area.size()
            self.image_label.fit_to_window(scroll_size)
            self._update_zoom_display()
    
    def _actual_size(self):
        """Show image at actual size"""
        if self.current_pixmap:
            self.image_label.set_actual_size()
            self._update_zoom_display()
    
    def _zoom_in(self):
        """Zoom in the image"""
        if self.current_pixmap:
            self.image_label.zoom_in()
            self._update_zoom_display()
    
    def _zoom_out(self):
        """Zoom out the image"""
        if self.current_pixmap:
            self.image_label.zoom_out()
            self._update_zoom_display()
    
    def _update_zoom_display(self):
        """Update the zoom percentage display"""
        if self.current_pixmap:
            zoom_percent = self.image_label.get_zoom_percentage()
            self.zoom_label.setText(f"{zoom_percent}%")
    
    def _on_image_loaded(self, pixmap: QPixmap):
        """Called when image is successfully loaded"""
        self.current_pixmap = pixmap
        
        # Set the pixmap in the zoomable image label
        self.image_label.set_pixmap(pixmap)
        
        # Enable image control buttons
        self.fit_button.setEnabled(True)
        self.actual_size_button.setEnabled(True)
        self.zoom_in_button.setEnabled(True)
        self.zoom_out_button.setEnabled(True)
        
        # Update zoom display
        self._update_zoom_display()
        
        # Update frame info with image dimensions
        width = pixmap.width()
        height = pixmap.height()
        
        current_file = self.sequence_files[self.current_frame_index]
        filename = os.path.basename(current_file if isinstance(current_file, str) 
                                   else current_file.get('path', ''))
        
        self.frame_info_label.setText(f"{filename}\n{width} × {height} pixels")
    
    def _on_error_occurred(self, error_message: str):
        """Called when an error occurs during image loading"""
        self.frame_info_label.setText(f"Error: {error_message}")
        self._clear_image()
        if hasattr(self.app, 'logger'):
            self.app.logger.error(f"Image viewer error: {error_message}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self._stop_current_loader()
        super().closeEvent(event)
    
    def sizeHint(self):
        """Provide size hint for the widget"""
        if self.is_expanded:
            return QSize(self.preferred_width, 600)
        else:
            return QSize(self.collapsed_width, 600) 