"""
Test script for file copy operations.
This script will test the copy functionality with detailed logging.
"""
import os
import sys
import json

# Try different import approaches to handle module structure
try:
    from .fileops import FileOperations
except ImportError:
    try:
        from fileops import FileOperations
    except ImportError:
        # Use absolute path for import if module imports fail
        import importlib.util
        import os
        
        # Get the absolute path to the fileops.py module
        module_path = os.path.join(os.path.dirname(__file__), "fileops.py")
        spec = importlib.util.spec_from_file_location("fileops", module_path)
        fileops = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fileops)
        FileOperations = fileops.FileOperations

def main():
    """Test the file copy operation directly"""
    print("[TEST] Starting copy operation test...", file=sys.stderr)
    
    # Define test paths
    src_dir = os.path.join(os.path.dirname(__file__), "test_data")
    dst_dir = os.path.join(os.path.dirname(__file__), "test_output")
    
    # Create test directories
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)
    
    # Create a test file
    test_file = os.path.join(src_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file for copy operation debugging.")
    
    print(f"[TEST] Created test file: {test_file}", file=sys.stderr)
    
    # Define the destination path
    dst_file = os.path.join(dst_dir, "test_file_copied.txt")
    
    # Create a mapping for the test file
    mapping = {
        "id": "test-copy-1",
        "sourcePath": test_file,
        "targetPath": dst_file,
        "type": "file"
    }
    
    # Initialize FileOperations
    operations = FileOperations()
    
    # Test both direct copy and multithreaded copy
    print("[TEST] Testing direct file copy...", file=sys.stderr)
    try:
        # First test with standard copy
        result = operations.apply_mappings(
            [mapping],
            operation_type="copy",
            batch_id="test-copy-direct"
        )
        print(f"[TEST] Direct copy result: {json.dumps(result, indent=2)}", file=sys.stderr)
        
        # Check if file was copied
        if os.path.exists(dst_file):
            print(f"[TEST] SUCCESS: File copied to {dst_file}", file=sys.stderr)
            # Remove the file for the next test
            os.remove(dst_file)
        else:
            print(f"[TEST] FAILURE: File not copied to {dst_file}", file=sys.stderr)
    
    except Exception as e:
        print(f"[TEST] ERROR during direct copy: {e}", file=sys.stderr)
    
    print("[TEST] Testing multithreaded copy...", file=sys.stderr)
    try:
        # Then test with multithreaded copy
        result = operations.apply_mappings_multithreaded(
            [mapping],
            operation_type="copy",
            batch_id="test-copy-multi",
            max_workers=2,
            file_workers=1
        )
        print(f"[TEST] Multithreaded copy result: {json.dumps(result, indent=2)}", file=sys.stderr)
        
        # Check if file was copied
        if os.path.exists(dst_file):
            print(f"[TEST] SUCCESS: File copied to {dst_file} using multithreaded copy", file=sys.stderr)
        else:
            print(f"[TEST] FAILURE: File not copied to {dst_file} using multithreaded copy", file=sys.stderr)
    
    except Exception as e:
        print(f"[TEST] ERROR during multithreaded copy: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
