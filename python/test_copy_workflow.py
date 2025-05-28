"""
Complete copy workflow test script.
This tests the entire pipeline including mapping generation and file copying.
"""
import os
import sys
import json
import uuid
import time
import shutil
from typing import Dict, Any, List

# Import the necessary modules using direct imports to avoid module issues
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add script directory to path for imports
sys.path.insert(0, script_dir)

# Import our modules directly
from fileops import FileOperations
from mapping import MappingGenerator

def main():
    """Test the complete file mapping and copy workflow"""
    print("\n=== COMPLETE COPY WORKFLOW TEST ===\n")
    
    # Create test directory structure
    base_dir = r"z:\DEMO\workflow_test"
    src_dir = os.path.join(base_dir, "source")
    vfx_dir = os.path.join(base_dir, "vfx_projects")
    
    # Clean up previous test directories if they exist
    if os.path.exists(base_dir):
        print(f"Cleaning up previous test directory: {base_dir}")
        try:
            shutil.rmtree(base_dir)
            print("Previous test directory removed")
        except Exception as e:
            print(f"Warning: Failed to clean up previous directory: {e}")
    
    # Create test directories
    print(f"Creating test directories")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(vfx_dir, exist_ok=True)
    
    # Create test shot structure
    shot_dir = os.path.join(src_dir, "SHOT001")
    comp_dir = os.path.join(shot_dir, "comp")
    render_dir = os.path.join(shot_dir, "render")
    
    os.makedirs(comp_dir, exist_ok=True)
    os.makedirs(render_dir, exist_ok=True)
    
    # Create test files
    print(f"Creating test files")
    comp_file = os.path.join(comp_dir, "SHOT001_comp_v001.exr")
    render_file = os.path.join(render_dir, "SHOT001_beauty_v001.exr")
    
    # Write some test data to files
    with open(comp_file, "wb") as f:
        f.write(b"TESTDATA" * 1000)  # 8KB
    
    with open(render_file, "wb") as f:
        f.write(b"RENDERDATA" * 1000)  # 10KB
    
    print(f"Created test file: {comp_file} ({os.path.getsize(comp_file)} bytes)")
    print(f"Created test file: {render_file} ({os.path.getsize(render_file)} bytes)")
    
    # Create a test profile
    test_profile = {
        "name": "Test Profile",
        "vfxRootPath": vfx_dir,
        "projectType": "internal",
        "shotPattern": r"SHOT\d+",
        "taskPattern": {
            "comp": ["comp"],
            "render": ["beauty"]
        }
    }
    
    # Create test tree structure
    test_tree = {
        "name": "workflow_test",
        "path": src_dir,
        "type": "folder",
        "children": [
            {
                "name": "SHOT001",
                "path": shot_dir,
                "type": "folder",
                "children": [
                    {
                        "name": "comp",
                        "path": comp_dir,
                        "type": "folder",
                        "children": [
                            {
                                "name": "SHOT001_comp_v001.exr",
                                "path": comp_file,
                                "type": "file",
                                "size": os.path.getsize(comp_file),
                                "extension": ".exr"
                            }
                        ]
                    },
                    {
                        "name": "render",
                        "path": render_dir,
                        "type": "folder",
                        "children": [
                            {
                                "name": "SHOT001_beauty_v001.exr",
                                "path": render_file,
                                "type": "file",
                                "size": os.path.getsize(render_file),
                                "extension": ".exr"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Step 1: Generate mappings
    print("\n=== STEP 1: Generating Mappings ===")
    generator = MappingGenerator()
    mappings = generator.generate_mappings(test_tree, test_profile)
    
    print(f"Generated {len(mappings)} mappings:")
    for i, mapping in enumerate(mappings):
        src = mapping.get("sourcePath")
        dst = mapping.get("targetPath")
        print(f"  Mapping {i+1}: {os.path.basename(src)} -> {dst}")
    
    # Step 2: Apply mappings with copy operation
    print("\n=== STEP 2: Applying Copy Operations ===")
    batch_id = f"test-copy-{uuid.uuid4()}"
    
    # Initialize FileOperations with our optimized settings
    ops = FileOperations(start_websocket=False, debug_mode=True)
    
    # Apply the mappings with copy operation
    start_time = time.time()
    result = ops.apply_mappings_multithreaded(
        mappings,
        operation_type="copy",  # Explicitly set to copy
        batch_id=batch_id,
        max_workers=2,
        file_workers=2
    )
    elapsed = time.time() - start_time
    
    print(f"\nCopy operation completed in {elapsed:.2f} seconds")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Step 3: Verify the results
    print("\n=== STEP 3: Verifying Results ===")
    success_count = 0
    fail_count = 0
    
    for mapping in mappings:
        src = mapping.get("sourcePath")
        dst = mapping.get("targetPath")
        
        # Normalize paths
        src = os.path.normpath(src)
        dst = os.path.normpath(dst)
        
        if os.path.exists(dst):
            src_size = os.path.getsize(src)
            dst_size = os.path.getsize(dst)
            
            if src_size == dst_size:
                print(f"✓ SUCCESS: {os.path.basename(src)} copied successfully ({dst_size} bytes)")
                success_count += 1
            else:
                print(f"✗ FAILURE: {os.path.basename(src)} size mismatch - src: {src_size}, dst: {dst_size}")
                fail_count += 1
        else:
            print(f"✗ FAILURE: {os.path.basename(src)} destination file not found: {dst}")
            fail_count += 1
    
    # Final summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total mappings: {len(mappings)}")
    print(f"Successful copies: {success_count}")
    print(f"Failed copies: {fail_count}")
    
    if fail_count == 0 and success_count == len(mappings):
        print("\n✓ ALL TESTS PASSED! The copy workflow is working correctly.")
    else:
        print("\n✗ TESTS FAILED! Some files were not copied correctly.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n=== TEST FAILED WITH EXCEPTION ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
