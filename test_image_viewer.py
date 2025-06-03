#!/usr/bin/env python3
"""
Test script for the CollapsibleImageViewer component
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Import the image viewer component
from python.gui_components.image_viewer_panel_pyqt5 import CollapsibleImageViewer


class MockApp:
    """Mock app instance for testing the image viewer"""
    
    def __init__(self):
        self.logger = self._create_mock_logger()
        self.ffplay_path_var = MockStringVar()
        
    def _create_mock_logger(self):
        import logging
        logger = logging.getLogger("MockApp")
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger


class MockStringVar:
    """Mock StringVar for testing"""
    
    def __init__(self, value=""):
        self._value = value
    
    def get(self):
        return self._value
    
    def set(self, value):
        self._value = value


class TestWindow(QMainWindow):
    """Test window to demonstrate the image viewer"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Image Viewer Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create mock app
        self.mock_app = MockApp()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Instructions
        instructions = QLabel("""
Image Viewer Test

Instructions:
1. Click the ▶ button on the right to expand the image viewer panel
2. Use the test buttons below to simulate sequence selection
3. The image viewer should show the middle frame in an external ffplay window

Note: This requires ffplay to be installed and available in your PATH.
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create the image viewer panel
        self.image_viewer = CollapsibleImageViewer(self.mock_app, self)
        layout.addWidget(self.image_viewer)
        
        # Add test buttons
        self._add_test_buttons(layout)
        
        # Apply dark styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                padding: 10px;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666;
                color: white;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
    
    def _add_test_buttons(self, layout):
        """Add test buttons to simulate sequence data"""
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout
        
        button_layout = QHBoxLayout()
        
        # Test with mock sequence data
        test_sequence_btn = QPushButton("Test with Mock EXR Sequence")
        test_sequence_btn.clicked.connect(self._test_mock_sequence)
        button_layout.addWidget(test_sequence_btn)
        
        # Clear sequence data
        clear_btn = QPushButton("Clear Sequence")
        clear_btn.clicked.connect(self._clear_sequence)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
    
    def _test_mock_sequence(self):
        """Test with mock sequence data"""
        # Create mock sequence data that might exist in a real project
        mock_sequence_data = {
            'base_name': 'test_render_v001',
            'suffix': '.exr',
            'directory': '/path/to/sequences',  # This won't exist, but demonstrates the structure
            'frame_count': 120,
            'frame_numbers': list(range(1001, 1121)),  # Frames 1001-1120
            'files': [
                {'path': f'/path/to/sequences/test_render_v001.{i:04d}.exr'} 
                for i in range(1001, 1121)
            ]
        }
        
        print("Setting mock sequence data in image viewer...")
        self.image_viewer.set_sequence_data(mock_sequence_data)
    
    def _clear_sequence(self):
        """Clear the sequence data"""
        print("Clearing sequence data...")
        self.image_viewer.set_sequence_data(None)


def main():
    """Main function to run the test"""
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("Image Viewer Test Started")
    print("="*50)
    print("Click the ▶ button to expand the image viewer panel")
    print("Use the test buttons to simulate sequence selection")
    print("Note: Requires ffplay to be installed for image display")
    print("="*50)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 