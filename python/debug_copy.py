"""
Debug script for file copy operations with timeout protection.
This will help identify where the copy operation is hanging.
"""
import os
import sys
import time
import threading
import shutil
import traceback

def main():
    """Test basic file operations with timeout protection"""
    print("=== DEBUG COPY TEST ===")
    
    # Define test paths
    src_dir = r"z:\DEMO\src_test"
    dst_dir = r"z:\DEMO\dst_test"
    
    # Create test directories if they don't exist
    try:
        print(f"Creating source directory: {src_dir}")
        os.makedirs(src_dir, exist_ok=True)
        print(f"Creating destination directory: {dst_dir}")
        os.makedirs(dst_dir, exist_ok=True)
    except Exception as e:
        print(f"ERROR creating directories: {e}")
        return

    # Create a test file (small size for quick testing)
    test_file = os.path.join(src_dir, "test_file.txt")
    dst_file = os.path.join(dst_dir, "copied_file.txt")
    
    try:
        print(f"Creating test file: {test_file}")
        with open(test_file, "w") as f:
            f.write("Test content for copy operation\n" * 100)
        print(f"Test file created. Size: {os.path.getsize(test_file)} bytes")
    except Exception as e:
        print(f"ERROR creating test file: {e}")
        return
    
    # Remove destination file if it exists
    if os.path.exists(dst_file):
        try:
            os.remove(dst_file)
            print(f"Removed existing destination file")
        except Exception as e:
            print(f"ERROR removing destination file: {e}")
    
    # Test direct copy with timeout protection
    print("\n=== TESTING DIRECT COPY WITH TIMEOUT ===")
    success = False
    
    def copy_with_timeout():
        nonlocal success
        try:
            print(f"Starting copy from {test_file} to {dst_file}")
            shutil.copy2(test_file, dst_file)
            print(f"Copy completed successfully")
            success = True
        except Exception as e:
            print(f"COPY ERROR: {e}")
            traceback.print_exc()
    
    # Start copy in a separate thread
    copy_thread = threading.Thread(target=copy_with_timeout)
    copy_thread.daemon = True  # Allow program to exit if thread hangs
    
    print("Starting copy thread...")
    start_time = time.time()
    copy_thread.start()
    
    # Wait with timeout
    timeout = 10  # 10 seconds should be more than enough for a small file
    print(f"Waiting for copy to complete (timeout: {timeout} seconds)...")
    
    copy_thread.join(timeout)
    elapsed = time.time() - start_time
    
    if copy_thread.is_alive():
        print(f"ERROR: Copy operation TIMED OUT after {elapsed:.2f} seconds!")
        print("The copy operation is hanging and did not complete in the expected time.")
    else:
        print(f"Copy thread completed in {elapsed:.2f} seconds")
    
    # Verify results
    if os.path.exists(dst_file):
        dst_size = os.path.getsize(dst_file)
        src_size = os.path.getsize(test_file)
        print(f"Destination file exists. Size: {dst_size} bytes")
        
        if dst_size == src_size:
            print("SUCCESS: File sizes match!")
        else:
            print(f"WARNING: Size mismatch! Source: {src_size} bytes, Destination: {dst_size} bytes")
    else:
        print("ERROR: Destination file was not created!")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
