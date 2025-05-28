"""
Small file copy test script for debugging with complete output
"""
import os
import sys
import json
import uuid

# Import FileOperations using direct path
module_path = os.path.join(os.path.dirname(__file__), "fileops.py")
import importlib.util
spec = importlib.util.spec_from_file_location("fileops", module_path)
fileops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fileops)
FileOperations = fileops.FileOperations

def main():
    """Run a copy test with a small file to ensure complete output"""
    print("===== SMALL FILE COPY TEST =====")
    
    # Setup test directories with full access as requested
    src_dir = r"z:\DEMO\test_small_src"
    dst_dir = r"z:\DEMO\test_small_dst"
    
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)
    
    # Create a small test file (500KB)
    test_file = os.path.join(src_dir, "test_small_file.txt")
    file_size = 500 * 1024  # 500KB
    
    print(f"Creating test file: {test_file} ({file_size/1024:.2f} KB)")
    with open(test_file, "w") as f:
        f.write("This is a test file for copy operation debugging.\n" * (file_size // 50))
    
    # Verify the file was created
    actual_size = os.path.getsize(test_file)
    print(f"Test file created. Size: {actual_size/1024:.2f} KB")
    
    # Create destination path
    dst_file = os.path.join(dst_dir, "copied_small_file.txt")
    
    # Remove destination if it exists
    if os.path.exists(dst_file):
        os.remove(dst_file)
        print(f"Removed existing destination file")
    
    # Create mapping for the test
    mapping = {
        "id": str(uuid.uuid4()),
        "sourcePath": test_file,
        "targetPath": dst_file,
        "type": "file"
    }
    
    # Initialize FileOperations
    ops = FileOperations()
    
    # Test copy operation
    print("\n===== TESTING COPY OPERATION =====")
    batch_id = f"copy-{uuid.uuid4()}"
    
    try:
        # Use our enhanced apply_mappings_multithreaded function
        result = ops.apply_mappings_multithreaded(
            [mapping],
            operation_type="copy",  # Explicitly set to copy
            batch_id=batch_id,
            max_workers=2,
            file_workers=1
        )
        
        print(f"\nCopy operation complete")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Verify the copy was successful
        if os.path.exists(dst_file):
            dst_size = os.path.getsize(dst_file)
            print(f"Destination file exists. Size: {dst_size/1024:.2f} KB")
            
            if dst_size == actual_size:
                print("SUCCESS: File sizes match!")
            else:
                print(f"ERROR: File size mismatch! Source: {actual_size} bytes, Destination: {dst_size} bytes")
        else:
            print("ERROR: Destination file was not created!")
    
    except Exception as e:
        print(f"ERROR: Copy operation failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n===== TEST COMPLETED =====")

if __name__ == "__main__":
    main()
