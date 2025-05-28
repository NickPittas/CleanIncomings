"""
Simple test script for debugging file copy operations.
"""
import os
import sys
import shutil

def main():
    """Test basic file copying mechanisms"""
    print("=== Simple Copy Test ===")
    
    # Create test directories
    src_dir = os.path.join(os.path.dirname(__file__), "test_src")
    dst_dir = os.path.join(os.path.dirname(__file__), "test_dst")
    
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)
    
    # Create a test file
    test_file = os.path.join(src_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file for copy operation debugging.\n" * 100)
    
    print(f"Created test file: {test_file}")
    print(f"File size: {os.path.getsize(test_file)} bytes")
    
    # Define destination path
    dst_file = os.path.join(dst_dir, "copied_file.txt")
    
    # Remove destination if it exists
    if os.path.exists(dst_file):
        os.remove(dst_file)
        print(f"Removed existing destination file: {dst_file}")
    
    print("\n=== Testing Direct Python Copy ===")
    try:
        print(f"Copying from {test_file} to {dst_file}")
        shutil.copy2(test_file, dst_file)
        print(f"Copy completed. Destination exists: {os.path.exists(dst_file)}")
        print(f"Destination size: {os.path.getsize(dst_file)} bytes")
    except Exception as e:
        print(f"Copy failed with error: {e}")
    
    # Cleanup
    try:
        if os.path.exists(dst_file):
            os.remove(dst_file)
            print(f"Cleaned up destination file")
    except Exception as e:
        print(f"Cleanup failed: {e}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
