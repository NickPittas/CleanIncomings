"""
Local file copy test with WebSocket progress updates.
Creates test files locally and copies them while showing progress.
"""
import os
import sys
import time
import uuid
import random
import json
import shutil
import threading
from pathlib import Path

# Import function to send progress updates
try:
    from simple_progress_server import send_progress_update
except ImportError:
    # Fallback implementation
    def send_progress_update(batch_id, files_processed, total_files, current_file="", status="running"):
        print(f"Progress: {files_processed}/{total_files} - {current_file} - {status}")
        return True

def generate_test_file(path, size_mb=10):
    """Generate a test file with random data of specified size"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Create file with random data
    with open(path, 'wb') as f:
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))
    
    return os.path.getsize(path)

def create_test_files(source_dir, num_files=10, min_size_mb=1, max_size_mb=10):
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

def ensure_progress_server_running():
    """Make sure the progress server is running"""
    # Check if WebSocket server is running
    import socket
    ws_running = False
    http_running = False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            ws_running = s.connect_ex(('localhost', 8765)) == 0
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            http_running = s.connect_ex(('localhost', 8080)) == 0
    except Exception as e:
        print(f"Error checking server status: {e}")
        ws_running = False
        http_running = False
    
    if not ws_running or not http_running:
        print("Starting progress server...")
        import subprocess
        
        # Start the server in a separate process
        try:
            subprocess.Popen(
                [sys.executable, os.path.join(os.path.dirname(__file__), "simple_progress_server.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for servers to start
            time.sleep(2)
            
            # Open browser
            try:
                import webbrowser
                webbrowser.open("http://localhost:8080")
            except Exception as e:
                print(f"Error opening browser: {e}")
                print("Please manually open http://localhost:8080 to view progress")
        except Exception as e:
            print(f"Error starting progress server: {e}")
    else:
        print("Progress server is already running")
        print("View progress at http://localhost:8080")

def copy_files_with_progress(files, dest_dir, batch_id):
    """Copy files with progress updates"""
    total_files = len(files)
    files_processed = 0
    total_size = sum(size for _, size in files)
    processed_size = 0
    start_time = time.time()
    
    print(f"Starting copy operation with batch ID: {batch_id}")
    print(f"Copying {total_files} files ({total_size / (1024*1024):.2f} MB)")
    
    # Send initial progress update
    send_progress_update(
        batch_id=batch_id,
        files_processed=0,
        total_files=total_files,
        status="running"
    )
    
    for src_path, file_size in files:
        # Create destination path
        filename = os.path.basename(src_path)
        dst_path = os.path.join(dest_dir, filename)
        
        # Send progress update for current file
        send_progress_update(
            batch_id=batch_id,
            files_processed=files_processed,
            total_files=total_files,
            current_file=filename,
            status="running"
        )
        
        try:
            # Copy the file
            print(f"Copying: {filename} ({file_size / (1024*1024):.2f} MB)")
            shutil.copy2(src_path, dst_path)
            
            # Update progress
            files_processed += 1
            processed_size += file_size
            
            # Calculate progress percentage
            percent = (files_processed / total_files) * 100
            
            # Calculate speed
            elapsed = time.time() - start_time
            speed = processed_size / elapsed if elapsed > 0 else 0
            
            print(f"Progress: {files_processed}/{total_files} files ({percent:.1f}%) - "
                  f"Speed: {speed / (1024*1024):.2f} MB/s")
            
            # Send intermediate progress updates during file copy
            # This simulates a large file copy with multiple progress updates per file
            file_size_mb = file_size / (1024 * 1024)
            steps = max(5, int(file_size_mb * 2))  # More updates for larger files
            
            for step in range(1, steps + 1):
                # Update for partial file progress
                percent_done = (step / steps) * 100
                current_name = f"{filename} ({percent_done:.0f}%)"
                
                # Send a progress update with the updated filename
                send_progress_update(
                    batch_id=batch_id,
                    files_processed=files_processed + (step / steps),
                    total_files=total_files,
                    current_file=current_name,
                    status="running"
                )
                
                # Simulate processing time
                time.sleep(0.2)
            
        except Exception as e:
            print(f"Error copying {src_path}: {e}")
    
    # Send final progress update
    send_progress_update(
        batch_id=batch_id,
        files_processed=files_processed,
        total_files=total_files,
        current_file="",
        status="completed"
    )
    
    # Calculate final statistics
    elapsed = time.time() - start_time
    speed = total_size / elapsed if elapsed > 0 else 0
    
    print(f"\nCopy operation completed in {elapsed:.1f} seconds")
    print(f"Copied {files_processed}/{total_files} files ({total_size / (1024*1024):.2f} MB)")
    print(f"Average speed: {speed / (1024*1024):.2f} MB/s")

def main():
    """Main function"""
    # Define source and destination directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(script_dir, "_test_source")
    dest_dir = os.path.join(script_dir, "_test_dest")
    
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Make sure directories exist
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Make sure progress server is running
    ensure_progress_server_running()
    
    # Generate unique batch ID for this operation
    batch_id = f"copy-{uuid.uuid4()}"
    
    try:
        # Create test files
        files = create_test_files(
            source_dir, 
            num_files=10,  # Number of files to create
            min_size_mb=1,  # Minimum file size in MB
            max_size_mb=5   # Maximum file size in MB
        )
        
        # Copy files with progress updates
        copy_files_with_progress(files, dest_dir, batch_id)
        
        print("\nTest completed successfully")
        print(f"Source: {source_dir}")
        print(f"Destination: {dest_dir}")
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        # Send interrupted status
        send_progress_update(
            batch_id=batch_id,
            files_processed=0,
            total_files=1,
            status="interrupted"
        )
    except Exception as e:
        print(f"\nError during operation: {e}")
        # Send error status
        send_progress_update(
            batch_id=batch_id,
            files_processed=0,
            total_files=1,
            status="error"
        )
    
    user_input = input("\nDo you want to clean up test files? (y/n): ")
    if user_input.lower() == 'y':
        print("Cleaning up test files...")
        try:
            if os.path.exists(source_dir):
                shutil.rmtree(source_dir)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            print("Cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
