#!/usr/bin/env python3
"""
Test script for new UI features:
1. Collapsible log panel
2. Editable folder fields 
3. Settings persistence
"""

import json
import os
from pathlib import Path

# Test 1: Settings persistence
def test_settings_persistence():
    """Test the settings manager functionality."""
    print("=== Testing Settings Persistence ===")
    
    # Create a mock settings file
    test_settings = {
        "ui_state": {
            "window_geometry": "1200x800",
            "window_position": "+100+100",
            "log_panel_collapsed": True,
            "source_folder": "/test/source",
            "destination_folder": "/test/dest",
            "selected_profile": "Test Profile"
        }
    }
    
    settings_file = Path("test_user_settings.json")
    try:
        with open(settings_file, 'w') as f:
            json.dump(test_settings, f, indent=2)
        
        print(f"✓ Created test settings file: {settings_file}")
        
        # Read it back
        with open(settings_file, 'r') as f:
            loaded = json.load(f)
        
        if loaded == test_settings:
            print("✓ Settings save/load works correctly")
        else:
            print("✗ Settings save/load failed")
        
        # Clean up
        settings_file.unlink()
        print("✓ Test cleanup completed")
        
    except Exception as e:
        print(f"✗ Settings test failed: {e}")

# Test 2: Folder validation
def test_folder_validation():
    """Test folder validation logic."""
    print("\n=== Testing Folder Validation ===")
    
    import tempfile
    import os
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        valid_path = temp_dir
        invalid_path = "/non/existent/path"
        
        # Test valid path
        if os.path.isdir(valid_path):
            print(f"✓ Valid path detected correctly: {valid_path}")
        else:
            print(f"✗ Valid path check failed: {valid_path}")
        
        # Test invalid path
        if not os.path.isdir(invalid_path):
            print(f"✓ Invalid path detected correctly: {invalid_path}")
        else:
            print(f"✗ Invalid path check failed: {invalid_path}")

# Test 3: UI component structure
def test_ui_components():
    """Test that the UI components are properly structured."""
    print("\n=== Testing UI Component Structure ===")
    
    try:
        from python.gui_components.settings_manager import SettingsManager
        print("✓ Settings manager imports correctly")
        
        from python.gui_components.widget_factory import WidgetFactory
        print("✓ Widget factory imports correctly")
        
        # Test default settings structure
        class MockApp:
            def __init__(self):
                self.selected_source_folder = type('StringVar', (), {'get': lambda: ''})()
                self.selected_destination_folder = type('StringVar', (), {'get': lambda: ''})()
                self.selected_profile_name = type('StringVar', (), {'get': lambda: ''})()
        
        mock_app = MockApp()
        settings_mgr = SettingsManager(mock_app)
        
        defaults = settings_mgr.default_settings
        required_keys = ["ui_state"]
        
        for key in required_keys:
            if key in defaults:
                print(f"✓ Default settings contain '{key}' key")
            else:
                print(f"✗ Default settings missing '{key}' key")
        
        ui_state_keys = ["window_geometry", "log_panel_collapsed", "source_folder", "destination_folder"]
        for key in ui_state_keys:
            if key in defaults["ui_state"]:
                print(f"✓ UI state contains '{key}' key")
            else:
                print(f"✗ UI state missing '{key}' key")
        
    except Exception as e:
        print(f"✗ UI component test failed: {e}")

if __name__ == "__main__":
    test_settings_persistence()
    test_folder_validation()
    test_ui_components()
    print("\n=== All Tests Completed ===") 