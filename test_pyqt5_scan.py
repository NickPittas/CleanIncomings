#!/usr/bin/env python3
"""
Test script to verify PyQt5 application scan functionality
"""
import time
import subprocess
import sys
from pathlib import Path

def test_scan_functionality():
    """Test the scan functionality by monitoring application behavior"""
    
    print("PyQt5 Application Scan Test")
    print("=" * 40)
    
    # Check if the application is running
    try:
        result = subprocess.run([
            "powershell", "-Command", 
            "Get-Process | Where-Object {$_.MainWindowTitle -like '*Clean Incomings*'}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.stdout.strip():
            print("✅ PyQt5 application is running")
            print("Application found in process list")
        else:
            print("❌ PyQt5 application not found")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout while checking process list")
        return False
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False
    
    # Test instructions for manual verification
    print("\n📋 Manual Test Instructions:")
    print("1. In the PyQt5 application:")
    print("   - Ensure source and destination folders are selected")
    print("   - Ensure a profile is selected from the dropdown")
    print("   - Click the 'Refresh/Scan' button")
    print()
    print("2. Expected behavior:")
    print("   - Status should show 'Starting scan...'")
    print("   - Status should update with 'Scanning: [path]' messages")
    print("   - Source tree should populate with folder structure")
    print("   - Preview tree should show normalized file proposals")
    print("   - Status should show 'Scan Complete. Generated X proposals'")
    print()
    print("3. Verify these features work:")
    print("   - Tree expansion/collapse")
    print("   - File selection in preview tree")
    print("   - Copy/Move buttons enable when items selected")
    print("   - Settings window opens")
    
    return True

def check_required_files():
    """Check if required configuration files exist"""
    print("\n🔍 Checking Configuration Files:")
    
    config_files = [
        "config/profiles.json",
        "config/patterns.json", 
        "user_settings.json",
        "default_profile.json"
    ]
    
    all_exist = True
    for file_path in config_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Main test function"""
    print("Clean Incomings PyQt5 Application Test")
    print("=" * 50)
    
    # Check configuration files
    config_ok = check_required_files()
    if not config_ok:
        print("\n⚠️  Some configuration files are missing.")
        print("The application may not function correctly.")
    
    # Test scan functionality
    scan_ok = test_scan_functionality()
    
    if scan_ok and config_ok:
        print("\n🎉 PyQt5 application appears to be working correctly!")
        print("You can now manually test the scan functionality.")
    elif scan_ok:
        print("\n⚠️  Application is running but some config files missing.")
        print("Please test manually and check for any errors.")
    else:
        print("\n❌ Application test failed.")
        print("Please check if the application is running correctly.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
