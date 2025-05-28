"""
Test script to demonstrate WebSocket progress updates with file copy operations.

This script performs a file copy operation while sending progress updates to
the WebSocket server. Run this script in one terminal, and then open the
progress_viewer.html in a web browser to see real-time progress updates.

Usage:
    python test_websocket_progress.py [source_dir] [dest_dir] [num_files]
"""
import os
import sys
import time
import shutil
import random
import uuid
import argparse
from fileops import FileOperations
import threading

def generate_test_file(path, size_mb=10):
    """Generate a test file with random data of specified size"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Create file with random data
    with open(path, 'wb') as f:
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))
    
    return os.path.getsize(path)

def create_test_files(source_dir, num_files=10, min_size_mb=1, max_size_mb=50):
    """Create a set of test files with varying sizes"""
    files_created = []
    total_size = 0
    
    print(f"Creating {num_files} test files in {source_dir}...")
    
    # Create source directory if it doesn't exist
    os.makedirs(source_dir, exist_ok=True)
    
    for i in range(num_files):
        # Random file size between min and max
        size_mb = random.randint(min_size_mb, max_size_mb)
        
        # Create random filename
        filename = f"test_file_{i+1}_{size_mb}MB.dat"
        file_path = os.path.join(source_dir, filename)
        
        # Generate the file
        print(f"Generating {filename} ({size_mb} MB)...")
        file_size = generate_test_file(file_path, size_mb)
        
        files_created.append((file_path, file_size))
        total_size += file_size
    
    print(f"Created {num_files} test files with total size: {total_size / (1024*1024):.2f} MB")
    return files_created

def prepare_copy_mappings(files, dest_dir):
    """Prepare copy mapping for FileOperations"""
    mappings = []
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    for src_path, file_size in files:
        filename = os.path.basename(src_path)
        dst_path = os.path.join(dest_dir, filename)
        
        mapping = {
            "id": str(uuid.uuid4()),
            "source": src_path,
            "target": dst_path,
            "type": "file",
            "size": file_size
        }
        mappings.append(mapping)
    
    return mappings

def start_browser_thread():
    """Start a separate thread to open the progress viewer"""
    def run_browser():
        time.sleep(2)  # Give the server time to start
        
        # Try to open the browser using Python's webbrowser module
        import webbrowser
        try:
            print("Opening progress viewer in your browser...")
            webbrowser.open("http://localhost:8080")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print("Please open http://localhost:8080 in your browser to view progress")
    
    browser_thread = threading.Thread(target=run_browser)
    browser_thread.daemon = True
    browser_thread.start()

def main():
    """Main function to run the test"""
    parser = argparse.ArgumentParser(description="Test WebSocket progress updates with file copy operations")
    parser.add_argument("--source", default="_test_source", help="Source directory for test files")
    parser.add_argument("--dest", default="_test_dest", help="Destination directory for copied files")
    parser.add_argument("--files", type=int, default=5, help="Number of test files to create")
    parser.add_argument("--min-size", type=int, default=5, help="Minimum size of test files in MB")
    parser.add_argument("--max-size", type=int, default=20, help="Maximum size of test files in MB")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test files after completion")
    
    args = parser.parse_args()
    
    # Use absolute paths
    source_dir = os.path.abspath(args.source)
    dest_dir = os.path.abspath(args.dest)
    
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Start the progress server in a separate process
    import subprocess
    print("Starting progress monitor...")
    monitor_proc = subprocess.Popen([sys.executable, "start_progress_monitor.py"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    
    # Start a thread to open the browser
    start_browser_thread()
    
    try:
        # Create test files
        files = create_test_files(
            source_dir, 
            num_files=args.files, 
            min_size_mb=args.min_size, 
            max_size_mb=args.max_size
        )
        
        # Prepare file mappings
        mappings = prepare_copy_mappings(files, dest_dir)
        
        # Initialize FileOperations with WebSocket enabled
        print("Initializing FileOperations with WebSocket enabled...")
        fileops = FileOperations(start_websocket=True, debug_mode=True)
        
        # Start copy operation
        print("Starting file copy operation...")
        batch_id = f"copy-{uuid.uuid4()}"
        fileops.apply_mappings(
            mappings=mappings,
            operation_type="copy",
            batch_id=batch_id
        )
        
        print(f"Copy operation completed successfully! Batch ID: {batch_id}")
        
    except KeyboardInterrupt:
        print("Operation interrupted by user")
    except Exception as e:
        print(f"Error during operation: {e}")
    finally:
        # Clean up if requested
        if args.cleanup:
            print("Cleaning up test files...")
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
        
        # Wait for user to press Enter before terminating
        input("Press Enter to terminate the progress monitor and exit...")
        
        # Terminate the progress monitor process
        monitor_proc.terminate()
        try:
            monitor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            monitor_proc.kill()
        
        print("Test completed.")

if __name__ == "__main__":
    main()
