"""
Demo script showing how to use the integrated progress monitoring system.

This script demonstrates:
1. Creating test files for demonstration
2. Starting the progress monitoring server
3. Performing a file copy operation with real-time progress updates
4. Viewing the progress in a browser

Usage:
    python demo_progress.py
"""
import os
import sys
import time
import uuid
import random
import argparse
from pathlib import Path
from fileops import FileOperations

def create_test_files(source_dir, num_files=10, min_size_mb=1, max_size_mb=10):
    """Create test files for copy demonstration"""
    print(f"Creating {num_files} test files in {source_dir}")
    
    os.makedirs(source_dir, exist_ok=True)
    files_created = []
    total_size = 0
    
    for i in range(num_files):
        size_mb = random.randint(min_size_mb, max_size_mb)
        filename = f"test_file_{i+1}_{size_mb}MB.dat"
        file_path = os.path.join(source_dir, filename)
        
        print(f"Generating {filename} ({size_mb} MB)")
        
        # Create file with random data
        with open(file_path, 'wb') as f:
            for _ in range(size_mb):
                f.write(os.urandom(1024 * 1024))  # Write 1MB chunks
        
        file_size = os.path.getsize(file_path)
        files_created.append((file_path, file_size))
        total_size += file_size
    
    print(f"Created {num_files} files with total size: {total_size / (1024*1024):.2f} MB")
    return files_created

def prepare_mapping(files, dest_dir):
    """Prepare mapping for FileOperations"""
    mappings = []
    
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Demo of the progress monitoring system")
    parser.add_argument("--files", type=int, default=10, help="Number of test files to create")
    parser.add_argument("--min-size", type=int, default=5, help="Minimum file size in MB")
    parser.add_argument("--max-size", type=int, default=20, help="Maximum file size in MB")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test files after completion")
    args = parser.parse_args()
    
    # Set up test directories
    script_dir = Path(__file__).parent
    source_dir = script_dir / "_demo_source"
    dest_dir = script_dir / "_demo_dest"
    
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    
    try:
        # Create test files
        files = create_test_files(
            source_dir,
            num_files=args.files,
            min_size_mb=args.min_size,
            max_size_mb=args.max_size
        )
        
        # Prepare mapping for FileOperations
        mappings = prepare_mapping(files, dest_dir)
        
        # Initialize FileOperations with progress monitoring
        print("\nInitializing FileOperations with progress monitoring...")
        fileops = FileOperations(
            start_websocket=True,   # Start the WebSocket server
            debug_mode=True,        # Enable debug logging
            show_progress=True      # Open the progress viewer in browser
        )
        
        # Generate a unique batch ID
        batch_id = f"copy-{uuid.uuid4()}"
        print(f"Operation batch ID: {batch_id}")
        
        # Start copy operation
        print("\nStarting file copy operation...")
        fileops.apply_mappings(
            mappings=mappings,
            operation_type="copy",
            batch_id=batch_id
        )
        
        print("\nCopy operation completed successfully!")
        print(f"Files copied: {len(files)}")
        print(f"Total size: {sum(size for _, size in files) / (1024*1024):.2f} MB")
        
        # Keep the progress viewer running for a while
        print("\nProgress viewer will remain open. Press Ctrl+C to exit...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Clean up if requested
        if args.cleanup:
            print("\nCleaning up test files...")
            import shutil
            for dir_path in (source_dir, dest_dir):
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
            print("Cleanup completed")

if __name__ == "__main__":
    main()
