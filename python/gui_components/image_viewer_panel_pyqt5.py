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
    QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QProcess
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QColor


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


class CollapsibleImageViewer(QWidget):
    """
    Collapsible image viewer panel that shows the middle frame of image sequences
    """
    
    # Signals
    panel_toggled = pyqtSignal(bool)  # Emitted when panel is expanded/collapsed
    
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.current_sequence_data = None
        self.current_image_loader = None
        self.current_pixmap = None
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
        
        # Create the toggle button (always visible)
        self._create_toggle_button()
        
        # Create the content area (hidden when collapsed)
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
            QPushButton#toggle {
                background-color: #4a4a4a;
                border: 1px solid #666;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton#toggle:hover {
                background-color: #5a5a5a;
            }
            QPushButton#toggle:pressed {
                background-color: #333;
            }
            QFrame#content {
                background-color: #2b2b2b;
                border: none;
            }
            QPushButton#control {
                background-color: #4a4a4a;
                border: 1px solid #666;
                color: white;
                padding: 6px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton#control:hover {
                background-color: #5a5a5a;
            }
            QPushButton#control:pressed {
                background-color: #333;
            }
            QPushButton#control:disabled {
                background-color: #333;
                color: #666;
                border: 1px solid #444;
            }
        """)
    
    def _create_toggle_button(self):
        """Create the toggle button for expanding/collapsing"""
        self.toggle_button = QPushButton("▶", self)
        self.toggle_button.setObjectName("toggle")
        self.toggle_button.setFixedSize(25, 25)
        self.toggle_button.setToolTip("Show/Hide Image Viewer")
        self.toggle_button.clicked.connect(self._toggle_panel)
        
        # Position the toggle button
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(self.toggle_button)
        toggle_layout.addStretch()
        
        self.main_layout.addLayout(toggle_layout)
    
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
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #555;
                border-radius: 5px;
                background-color: #333;
            }
        """)
        
        self.image_label = QLabel()
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
        self.image_label.setText("Select an image sequence to view the middle frame")
        
        self.scroll_area.setWidget(self.image_label)
        content_layout.addWidget(self.scroll_area)
        
        # Frame info
        self.frame_info_label = QLabel("")
        self.frame_info_label.setObjectName("status")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label.setWordWrap(True)
        content_layout.addWidget(self.frame_info_label)
        
        # Controls
        self._create_controls(content_layout)
        
        content_layout.addStretch()
        self.main_layout.addWidget(self.content_frame)
    
    def _create_controls(self, parent_layout):
        """Create control buttons"""
        controls_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
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
        self.actual_size_button.setToolTip("Show actual size")
        self.actual_size_button.clicked.connect(self._actual_size)
        self.actual_size_button.setEnabled(False)
        controls_layout.addWidget(self.actual_size_button)
        
        parent_layout.addLayout(controls_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass
    
    def _toggle_panel(self):
        """Toggle the panel between expanded and collapsed states"""
        if self.is_expanded:
            self._set_collapsed_state()
        else:
            self._set_expanded_state()
    
    def _set_expanded_state(self):
        """Set the panel to expanded state"""
        self.is_expanded = True
        self.toggle_button.setText("◀")
        self.toggle_button.setToolTip("Hide Image Viewer")
        
        self.content_frame.setVisible(True)
        self.setMinimumWidth(self.preferred_width)
        self.setMaximumWidth(self.preferred_width)
        
        self.panel_toggled.emit(True)
        
        # If we have sequence data, show the image
        if self.current_sequence_data:
            self._show_middle_frame()
    
    def _set_collapsed_state(self):
        """Set the panel to collapsed state"""
        self.is_expanded = False
        self.toggle_button.setText("▶")
        self.toggle_button.setToolTip("Show Image Viewer")
        
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
            self.refresh_button.setEnabled(False)
            self.fit_button.setEnabled(False)
            self.actual_size_button.setEnabled(False)
            self._clear_image()
            self._stop_current_loader()
            return
        
        # Update status
        base_name = sequence_data.get('base_name', 'Unknown')
        frame_count = sequence_data.get('frame_count', 0)
        self.status_label.setText(f"{base_name}\n{frame_count} frames")
        
        self.refresh_button.setEnabled(True)
        
        # If panel is expanded, show the image
        if self.is_expanded:
            self._show_middle_frame()
    
    def _show_middle_frame(self):
        """Show the middle frame of the current sequence"""
        if not self.current_sequence_data:
            return
        
        files = self.current_sequence_data.get('files', [])
        if not files:
            self.status_label.setText("No files in sequence")
            self._clear_image()
            return
        
        # Find middle frame
        middle_index = len(files) // 2
        if isinstance(files[middle_index], dict):
            middle_file_path = files[middle_index].get('path', '')
        else:
            middle_file_path = str(files[middle_index])
        
        if not middle_file_path or not os.path.exists(middle_file_path):
            self.status_label.setText("Middle frame not found")
            self._clear_image()
            return
        
        # Stop any existing loader
        self._stop_current_loader()
        
        # Update frame info
        filename = os.path.basename(middle_file_path)
        self.frame_info_label.setText(f"Frame {middle_index + 1}/{len(files)}: {filename}")
        
        # Start image loading
        self.status_label.setText(f"Loading frame {middle_index + 1}/{len(files)}...")
        
        # Calculate max size based on current scroll area size
        scroll_size = self.scroll_area.size()
        max_size = QSize(scroll_size.width() - 20, scroll_size.height() - 20)  # Leave some margin
        
        self.current_image_loader = ImageLoaderThread(middle_file_path, max_size, self)
        self.current_image_loader.image_loaded.connect(self._on_image_loaded)
        self.current_image_loader.error_occurred.connect(self._on_error_occurred)
        self.current_image_loader.start()
    
    def _stop_current_loader(self):
        """Stop the current image loader"""
        if self.current_image_loader:
            self.current_image_loader.quit()
            self.current_image_loader.wait(1000)  # Wait up to 1 second
            self.current_image_loader = None
    
    def _clear_image(self):
        """Clear the current image"""
        self.current_pixmap = None
        self.image_label.clear()
        self.image_label.setText("Select an image sequence to view the middle frame")
        self.fit_button.setEnabled(False)
        self.actual_size_button.setEnabled(False)
    
    def _refresh_image(self):
        """Refresh the current image"""
        if self.current_sequence_data and self.is_expanded:
            self._show_middle_frame()
    
    def _fit_image(self):
        """Fit image to the scroll area"""
        if self.current_pixmap:
            scroll_size = self.scroll_area.size()
            fitted_size = QSize(scroll_size.width() - 40, scroll_size.height() - 40)  # Leave margin
            
            scaled_pixmap = self.current_pixmap.scaled(
                fitted_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_pixmap.size())
    
    def _actual_size(self):
        """Show image at actual size"""
        if self.current_pixmap:
            self.image_label.setPixmap(self.current_pixmap)
            self.image_label.resize(self.current_pixmap.size())
    
    def _on_image_loaded(self, pixmap: QPixmap):
        """Called when image is successfully loaded"""
        self.current_pixmap = pixmap
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
        
        # Update status
        base_name = self.current_sequence_data.get('base_name', 'Unknown')
        frame_count = self.current_sequence_data.get('frame_count', 0)
        self.status_label.setText(f"{base_name}\n{frame_count} frames")
        
        # Enable control buttons
        self.fit_button.setEnabled(True)
        self.actual_size_button.setEnabled(True)
        
        # Update frame info with image dimensions
        width = pixmap.width()
        height = pixmap.height()
        files = self.current_sequence_data.get('files', [])
        middle_index = len(files) // 2
        filename = os.path.basename(files[middle_index] if isinstance(files[middle_index], str) 
                                   else files[middle_index].get('path', ''))
        
        self.frame_info_label.setText(f"Frame {middle_index + 1}/{len(files)}: {filename}\n{width} × {height} pixels")
    
    def _on_error_occurred(self, error_message: str):
        """Called when an error occurs during image loading"""
        self.status_label.setText(f"Error loading image")
        self.frame_info_label.setText(error_message)
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