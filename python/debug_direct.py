"""
Direct debug script that tests only the _multithreaded_copy method
with simplified inputs and tight timeout control
"""
import os
import sys
import time
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
    """Test the _multithreaded_copy method directly"""
    print("[MAIN-1] === DIRECT MULTITHREADED COPY TEST ===")
    
    # Setup test paths
    print("[MAIN-2] Setting up test paths")
    src_dir = r"z:\DEMO\direct_src"
    dst_dir = r"z:\DEMO\direct_dst"
    print(f"[MAIN-3] Test paths set: src={src_dir}, dst={dst_dir}")
    
    # Create test directories
    try:
        print(f"[MAIN-4] Creating directories...")
        print(f"[MAIN-5] Creating source directory: {src_dir}")
        os.makedirs(src_dir, exist_ok=True)
        print(f"[MAIN-6] Source directory created")
        print(f"[MAIN-7] Creating destination directory: {dst_dir}")
        os.makedirs(dst_dir, exist_ok=True)
        print(f"[MAIN-8] Destination directory created")
        print(f"[MAIN-9] All directories created successfully")
    except Exception as e:
        print(f"ERROR creating directories: {e}")
        return
    
    # Create a test file (100KB)
    print(f"[MAIN-10] Creating file paths")
    test_file = os.path.join(src_dir, "direct_test.txt")
    print(f"[MAIN-11] Source file path: {test_file}")
    dst_file = os.path.join(dst_dir, "direct_copy.txt")
    print(f"[MAIN-12] Destination file path: {dst_file}")
    
    # Cleanup destination if it exists
    print(f"[MAIN-13] Checking if destination file exists")
    if os.path.exists(dst_file):
        print(f"[MAIN-14] Destination file exists, removing it")
        try:
            os.remove(dst_file)
            print(f"[MAIN-15] Removed existing destination file")
        except Exception as e:
            print(f"[MAIN-16] ERROR removing destination file: {e}")
    else:
        print(f"[MAIN-17] Destination file does not exist, no cleanup needed")
    
    # Create test file
    try:
        print(f"[MAIN-18] Creating test file: {test_file}")
        print(f"[MAIN-19] Opening file for writing")
        with open(test_file, "w") as f:
            print(f"[MAIN-20] Writing 100KB of data to file")
            f.write("X" * 100 * 1024)  # 100KB file
            print(f"[MAIN-21] Data written to file")
        print(f"[MAIN-22] File closed successfully")
        file_size = os.path.getsize(test_file)
        print(f"[MAIN-23] Test file created. Size: {file_size} bytes")
    except Exception as e:
        print(f"ERROR creating test file: {e}")
        return
    
    # Initialize FileOperations with WebSocket disabled and debug mode enabled
    print(f"[MAIN-24] Initializing FileOperations class with WebSocket disabled")
    ops = FileOperations(start_websocket=False, debug_mode=True)
    print(f"[MAIN-25] FileOperations initialized successfully")
    
    # Create batch_id for the operation
    print(f"[MAIN-26] Creating batch ID")
    batch_id = "direct-test"
    print(f"[MAIN-27] Batch ID created: {batch_id}")
    
    # Function to run the direct copy method
    def run_direct_copy():
        try:
            print(f"[DEBUG-1] Starting direct call to _multithreaded_copy...")
            print(f"[DEBUG-2] Source: {test_file}")
            print(f"[DEBUG-3] Destination: {dst_file}")
            
            print(f"[DEBUG-4] About to call _multithreaded_copy...")
            # Call the method directly
            ops._multithreaded_copy(test_file, dst_file, batch_id, max_workers=2)
            print(f"[DEBUG-5] _multithreaded_copy call returned successfully")
            
            print(f"_multithreaded_copy completed successfully")
            
            # Verify result
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
            print(f"ERROR in _multithreaded_copy: {e}")
            traceback.print_exc()
    
    # Run with timeout protection
    print(f"\n[MAIN-28] Starting direct copy test with timeout protection...")
    print(f"[MAIN-29] Creating thread for copy operation")
    thread = threading.Thread(target=run_direct_copy)
    print(f"[MAIN-30] Setting thread as daemon")
    thread.daemon = True
    
    print(f"[MAIN-31] Recording start time")
    start_time = time.time()
    print(f"[MAIN-32] Starting thread")
    thread.start()
    print(f"[MAIN-33] Thread started successfully")
    
    # Wait with timeout
    timeout = 20  # 20 seconds should be enough
    print(f"[MAIN-34] Waiting for operation to complete (timeout: {timeout} seconds)...")
    
    print(f"[MAIN-35] Joining thread with timeout")
    thread.join(timeout)
    print(f"[MAIN-36] Thread join completed (either thread finished or timeout occurred)")
    elapsed = time.time() - start_time
    print(f"[MAIN-37] Elapsed time calculated: {elapsed:.2f} seconds")
    
    if thread.is_alive():
        print(f"\nERROR: Operation TIMED OUT after {elapsed:.2f} seconds!")
        print("The _multithreaded_copy method is hanging and did not complete.")
        
        # Print diagnostic information
        print("\n=== DIAGNOSTIC INFORMATION ===")
        print(f"Source file exists: {os.path.exists(test_file)}")
        print(f"Destination directory exists: {os.path.exists(os.path.dirname(dst_file))}")
        
        # Check for chunk files
        try:
            dst_dir_contents = os.listdir(os.path.dirname(dst_file))
            print(f"Destination directory contents: {dst_dir_contents}")
            
            # Look for chunk files
            chunk_files = [f for f in dst_dir_contents if f.startswith(os.path.basename(dst_file) + ".chunk_")]
            if chunk_files:
                print(f"Found {len(chunk_files)} chunk files: {chunk_files}")
                
                # Check the size of one chunk file for reference
                if chunk_files:
                    chunk_path = os.path.join(dst_dir, chunk_files[0])
                    chunk_size = os.path.getsize(chunk_path)
                    print(f"First chunk file size: {chunk_size} bytes")
        except Exception as e:
            print(f"Error checking directory contents: {e}")
    else:
        print(f"\nOperation completed in {elapsed:.2f} seconds")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    print("[START] Script execution started")
    try:
        main()
        print("[END] Script execution completed normally")
    except Exception as e:
        print(f"[CRITICAL] Script failed with exception: {e}")
        traceback.print_exc()
        print("[END] Script execution completed with errors")
