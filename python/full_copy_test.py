"""
Full test script for debugging the FileOperations copy functionality
"""
import os
import sys
import json
import uuid
import time

# Import FileOperations using direct path
module_path = os.path.join(os.path.dirname(__file__), "fileops.py")
import importlib.util
spec = importlib.util.spec_from_file_location("fileops", module_path)
fileops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fileops)
FileOperations = fileops.FileOperations

def main():
    """Run comprehensive tests on the file copy operations"""
    print("\n===== COMPREHENSIVE FILE COPY TEST =====\n", file=sys.stderr)
    
    # Setup test directories
    src_dir = os.path.join(os.path.dirname(__file__), "test_full_src")
    dst_dir = os.path.join(os.path.dirname(__file__), "test_full_dst")
    
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)
    
    # Create a test file
    test_file = os.path.join(src_dir, "test_large_file.dat")
    
    # Create a reasonably sized file to test chunking (15MB)
    file_size = 15 * 1024 * 1024  # 15MB
    
    print(f"Creating test file: {test_file} ({file_size/1024/1024:.2f} MB)", file=sys.stderr)
    with open(test_file, "wb") as f:
        # Create a 15MB file with patterns to verify integrity
        chunk_size = 1024 * 64  # 64KB chunks
        for i in range(0, file_size, chunk_size):
            # Create pattern data - different for each chunk
            pattern = f"CHUNK-{i//chunk_size:04d}-".encode("utf-8")
            remaining = min(chunk_size, file_size - i)
            f.write(pattern * (remaining // len(pattern) + 1))
    
    # Verify the file was created correctly
    actual_size = os.path.getsize(test_file)
    print(f"Test file created. Size: {actual_size/1024/1024:.2f} MB", file=sys.stderr)
    
    # Create destination path
    dst_file = os.path.join(dst_dir, "copied_large_file.dat")
    
    # Remove destination if it exists
    if os.path.exists(dst_file):
        os.remove(dst_file)
        print(f"Removed existing destination file", file=sys.stderr)
    
    # Create mapping for the test
    mapping = {
        "id": str(uuid.uuid4()),
        "sourcePath": test_file,
        "targetPath": dst_file,
        "type": "file"
    }
    
    # Initialize FileOperations
    ops = FileOperations()
    
    # Test multithreaded copy
    print("\n===== TESTING MULTITHREADED COPY =====\n", file=sys.stderr)
    batch_id = f"copy-{uuid.uuid4()}"
    
    try:
        start_time = time.time()
        result = ops.apply_mappings_multithreaded(
            [mapping],
            operation_type="copy",
            batch_id=batch_id,
            max_workers=4,
            file_workers=2
        )
        elapsed = time.time() - start_time
        
        print(f"\nMultithreaded copy completed in {elapsed:.2f} seconds", file=sys.stderr)
        print(f"Result: {json.dumps(result, indent=2)}", file=sys.stderr)
        
        # Verify the copy was successful
        if os.path.exists(dst_file):
            dst_size = os.path.getsize(dst_file)
            print(f"Destination file exists. Size: {dst_size/1024/1024:.2f} MB", file=sys.stderr)
            
            if dst_size == actual_size:
                print("SUCCESS: File sizes match!", file=sys.stderr)
            else:
                print(f"ERROR: File size mismatch! Source: {actual_size} bytes, Destination: {dst_size} bytes", file=sys.stderr)
        else:
            print("ERROR: Destination file was not created!", file=sys.stderr)
    
    except Exception as e:
        print(f"ERROR: Multithreaded copy failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    print("\n===== TEST COMPLETED =====\n", file=sys.stderr)

if __name__ == "__main__":
    main()
