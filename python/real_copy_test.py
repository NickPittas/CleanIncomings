"""
Real-world file copy test with WebSocket progress updates.
Copies files from a specified source to destination with real-time progress tracking.

Usage:
    python real_copy_test.py [source_dir] [dest_dir]
"""
import os
import sys
import time
import uuid
import json
import shutil
import argparse
from pathlib import Path
import threading

# Import function to send progress updates
try:
    from simple_progress_server import send_progress_update
except ImportError:
    # Fallback to direct implementation if module not found
    def send_progress_update(batch_id, files_processed, total_files, current_file="", status="running"):
        """Fallback implementation that writes to a JSON file"""
        progress_dir = Path(__file__).parent / "_progress"
        progress_dir.mkdir(exist_ok=True)
        
        # Calculate percentage
        percentage = 0
        if total_files > 0:
            percentage = min(100.0, (files_processed / total_files) * 100)
        
        # Prepare progress data
        data = {
            'filesProcessed': files_processed,
            'totalFiles': total_files,
            'progressPercentage': percentage,
            'currentFile': current_file,
            'status': status,
            'timestamp': time.time()
        }
        
        # Save to disk
        try:
            save_path = progress_dir / f"progress_{batch_id}.json"
            with open(save_path, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving progress to disk: {e}")
            return False

def collect_files(source_dir):
    """Collect all files in the source directory recursively"""
    print(f"Scanning source directory: {source_dir}")
    
    files = []
    total_size = 0
    
    try:
        for root, _, filenames in os.walk(source_dir):
            for filename in filenames:
                source_path = os.path.join(root, filename)
                rel_path = os.path.relpath(source_path, source_dir)
                
                try:
                    file_size = os.path.getsize(source_path)
                    files.append((source_path, rel_path, file_size))
                    total_size += file_size
                except Exception as e:
                    print(f"Error getting size for {source_path}: {e}")
    except Exception as e:
        print(f"Error scanning directory {source_dir}: {e}")
    
    print(f"Found {len(files)} files with total size: {total_size / (1024*1024):.2f} MB")
    return files

def copy_files(files, source_dir, dest_dir, batch_id):
    """Copy files with progress updates"""
    total_files = len(files)
    files_processed = 0
    processed_size = 0
    total_size = sum(size for _, _, size in files)
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
    
    for source_path, rel_path, file_size in files:
        # Create destination path
        dest_path = os.path.join(dest_dir, rel_path)
        dest_dir_path = os.path.dirname(dest_path)
        
        # Send progress update for current file
        send_progress_update(
            batch_id=batch_id,
            files_processed=files_processed,
            total_files=total_files,
            current_file=rel_path,
            status="running"
        )
        
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(dest_dir_path, exist_ok=True)
            
            # Copy the file
            print(f"Copying: {rel_path} ({file_size / (1024*1024):.2f} MB)")
            shutil.copy2(source_path, dest_path)
            
            # Update progress
            files_processed += 1
            processed_size += file_size
            
            # Calculate and display progress
            percent = (files_processed / total_files) * 100
            elapsed = time.time() - start_time
            speed = processed_size / elapsed if elapsed > 0 else 0
            
            print(f"Progress: {files_processed}/{total_files} files ({percent:.1f}%) - "
                  f"Speed: {speed / (1024*1024):.2f} MB/s")
            
        except Exception as e:
            print(f"Error copying {source_path}: {e}")
    
    # Send final progress update
    send_progress_update(
        batch_id=batch_id,
        files_processed=files_processed,
        total_files=total_files,
        current_file="",
        status="completed"
    )
    
    # Calculate and display final statistics
    elapsed = time.time() - start_time
    speed = total_size / elapsed if elapsed > 0 else 0
    
    print(f"\nCopy operation completed in {elapsed:.1f} seconds")
    print(f"Copied {files_processed}/{total_files} files ({total_size / (1024*1024):.2f} MB)")
    print(f"Average speed: {speed / (1024*1024):.2f} MB/s")
    
    return files_processed, total_size, elapsed

def ensure_progress_server_running():
    """Make sure the progress server is running"""
    # Check if WebSocket server is running
    import socket
    ws_running = False
    http_running = False
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        ws_running = s.connect_ex(('localhost', 8765)) == 0
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        http_running = s.connect_ex(('localhost', 8080)) == 0
    
    if not ws_running or not http_running:
        print("Starting progress server...")
        import subprocess
        
        # Start the server in a separate process
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
    else:
        print("Progress server is already running")
        print("View progress at http://localhost:8080")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Real-world file copy with progress updates")
    parser.add_argument("source", nargs="?", default="Z:\\196799130_PREVIZ_v022\\196799406_PREVIZ_v022\\imags\\Z\\4k", 
                        help="Source directory")
    parser.add_argument("dest", nargs="?", default="Z:\\DEMO", 
                        help="Destination directory")
    args = parser.parse_args()
    
    # Convert to absolute paths
    source_dir = os.path.abspath(args.source)
    dest_dir = os.path.abspath(args.dest)
    
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Verify source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory does not exist: {source_dir}")
        return
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Make sure progress server is running
    ensure_progress_server_running()
    
    # Generate unique batch ID for this operation
    batch_id = f"copy-{uuid.uuid4()}"
    
    try:
        # Collect files to copy
        files = collect_files(source_dir)
        
        if not files:
            print("No files found to copy")
            return
        
        # Copy files with progress updates
        copy_files(files, source_dir, dest_dir, batch_id)
        
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
    
    print("\nOperation complete")
    print("You can close the progress viewer window")

if __name__ == "__main__":
    main()
