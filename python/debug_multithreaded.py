"""
Debug script for the multithreaded copy operation with timeout protection
"""
import os
import sys
import time
import json
import uuid
import threading
import traceback

# Import FileOperations using direct path
module_path = os.path.join(os.path.dirname(__file__), "fileops.py")
import importlib.util
spec = importlib.util.spec_from_file_location("fileops", module_path)
fileops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fileops)
FileOperations = fileops.FileOperations

def main():
    """Test the multithreaded copy with timeout protection"""
    print("=== MULTITHREADED COPY DEBUG TEST ===")
    
    # Setup test directories
    src_dir = r"z:\DEMO\mt_src"
    dst_dir = r"z:\DEMO\mt_dst"
    
    try:
        print(f"Creating source directory: {src_dir}")
        os.makedirs(src_dir, exist_ok=True)
        print(f"Creating destination directory: {dst_dir}")
        os.makedirs(dst_dir, exist_ok=True)
    except Exception as e:
        print(f"ERROR creating directories: {e}")
        return
    
    # Create a test file (small size for quick testing)
    test_file = os.path.join(src_dir, "test_mt_file.txt")
    dst_file = os.path.join(dst_dir, "copied_mt_file.txt")
    
    try:
        print(f"Creating test file: {test_file}")
        with open(test_file, "w") as f:
            f.write("Test content for multithreaded copy operation\n" * 1000)
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
    
    # Create mapping for the test
    mapping = {
        "id": str(uuid.uuid4()),
        "sourcePath": test_file,
        "targetPath": dst_file,
        "type": "file"
    }
    
    # Initialize FileOperations
    ops = FileOperations()
    
    # Define timeout function
    def run_with_timeout():
        try:
            # Test the multithreaded copy operation
            print("\n=== TESTING MULTITHREADED COPY ===")
            batch_id = f"copy-{uuid.uuid4()}"
            
            # Execute the copy operation
            print(f"Starting multithreaded copy operation...")
            result = ops.apply_mappings_multithreaded(
                [mapping],
                operation_type="copy",  # Explicitly set to copy
                batch_id=batch_id,
                max_workers=2,
                file_workers=1
            )
            
            print(f"Multithreaded copy completed")
            print(f"Result: {json.dumps(result, indent=2)}")
            
            # Verify the copy was successful
            if os.path.exists(dst_file):
                src_size = os.path.getsize(test_file)
                dst_size = os.path.getsize(dst_file)
                print(f"Destination file exists. Size: {dst_size} bytes")
                
                if dst_size == src_size:
                    print("SUCCESS: File sizes match!")
                else:
                    print(f"WARNING: Size mismatch! Source: {src_size}, Destination: {dst_size}")
            else:
                print("ERROR: Destination file was not created!")
        
        except Exception as e:
            print(f"ERROR in multithreaded copy: {e}")
            traceback.print_exc()
    
    # Run with timeout
    print("\nStarting multithreaded copy with timeout protection...")
    thread = threading.Thread(target=run_with_timeout)
    thread.daemon = True
    
    start_time = time.time()
    thread.start()
    
    # Wait with timeout
    timeout = 30  # 30 seconds should be plenty
    print(f"Waiting for operation to complete (timeout: {timeout} seconds)...")
    
    thread.join(timeout)
    elapsed = time.time() - start_time
    
    if thread.is_alive():
        print(f"\nERROR: Operation TIMED OUT after {elapsed:.2f} seconds!")
        print("The multithreaded copy operation is hanging and did not complete.")
        
        # Try to get some additional diagnostic information
        print("\n=== DIAGNOSTIC INFORMATION ===")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Source file exists: {os.path.exists(test_file)}")
        print(f"Destination directory exists: {os.path.exists(os.path.dirname(dst_file))}")
        print(f"Destination file exists: {os.path.exists(dst_file)}")
        
        # Check for any partial output files
        dst_dir_contents = os.listdir(os.path.dirname(dst_file))
        print(f"Destination directory contents: {dst_dir_contents}")
        
        # Check for chunk files that might indicate partial completion
        chunk_files = [f for f in dst_dir_contents if f.startswith(os.path.basename(dst_file) + ".chunk_")]
        if chunk_files:
            print(f"Found partial chunk files: {chunk_files}")
    else:
        print(f"\nOperation completed in {elapsed:.2f} seconds")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
