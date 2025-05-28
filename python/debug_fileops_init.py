"""
Debug script to isolate issues with FileOperations initialization
"""
import os
import sys
import traceback

def main():
    """Test the FileOperations initialization in isolation"""
    print("[1] Starting FileOperations initialization debug")
    
    # Step 1: Basic imports
    print("[2] Importing basic modules")
    import importlib.util
    print("[3] Basic imports successful")
    
    # Step 2: Import FileOperations class definition only (not instantiating yet)
    try:
        print("[4] Importing FileOperations class")
        module_path = os.path.join(os.path.dirname(__file__), "fileops.py")
        print(f"[5] Module path: {module_path}")
        
        # Check if the file exists
        if os.path.exists(module_path):
            print(f"[6] Module file exists: {os.path.getsize(module_path)} bytes")
        else:
            print(f"[6] ERROR: Module file not found!")
            return
        
        # Import the module
        print("[7] Creating spec from file location")
        spec = importlib.util.spec_from_file_location("fileops", module_path)
        print("[8] Creating module from spec")
        fileops = importlib.util.module_from_spec(spec)
        print("[9] Executing module")
        spec.loader.exec_module(fileops)
        print("[10] Module imported successfully")
        
        # Get the FileOperations class
        print("[11] Getting FileOperations class")
        FileOperations = fileops.FileOperations
        print("[12] FileOperations class retrieved")
        
        # Check class attributes
        print("[13] Checking FileOperations class attributes")
        print(f"[14] Class attributes: {dir(FileOperations)}")
        
        # Step 3: Create an instance of FileOperations with detailed debugging
        print("\n[15] Creating FileOperations instance")
        print("[16] Calling FileOperations constructor with start_websocket=False and debug_mode=True")
        ops = FileOperations(start_websocket=False, debug_mode=True)
        print("[17] FileOperations instance created successfully")
        
        # Step 4: Check instance attributes
        print("[18] Checking instance attributes")
        print(f"[19] Instance has these attributes: {dir(ops)}")
        
        print("\n[20] All initialization steps completed successfully")
        
    except Exception as e:
        print(f"\n[ERROR] Failed during FileOperations initialization: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
        print("\n[END] Script completed normally")
    except Exception as e:
        print(f"\n[CRITICAL] Unhandled exception: {e}")
        traceback.print_exc()
        print("\n[END] Script failed with errors")
