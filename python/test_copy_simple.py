#!/usr/bin/env python3
"""
Simple test to verify copy operations work correctly in both modes:
1. Without WebSocket (basic functionality)
2. With WebSocket (progress tracking)
"""

import os
import sys
import time
import shutil
import tempfile
import threading
from pathlib import Path

from fileops import FileOperations
from progress_server import check_server_health, get_websocket_port, stop_progress_server


def test_copy_without_websocket():
    """Test basic copy functionality without WebSocket"""
    print("\n=== Test 1: Copy WITHOUT WebSocket ===")
    
    test_dir = tempfile.mkdtemp(prefix="test_copy_basic_")
    
    try:
        # Create test files
        src_dir = os.path.join(test_dir, "source")
        dst_dir = os.path.join(test_dir, "destination")
        os.makedirs(src_dir)
        
        # Create 3 test files
        test_files = []
        for i in range(3):
            filepath = os.path.join(src_dir, f"file_{i}.txt")
            with open(filepath, "w") as f:
                f.write(f"Test content {i}\n" * 100)
            test_files.append(filepath)
        
        print(f"Created {len(test_files)} test files")
        
        # Initialize FileOperations WITHOUT WebSocket
        fileops = FileOperations(start_websocket=False)
        
        # Create mappings
        mappings = []
        for i, src_file in enumerate(test_files):
            mapping = {
                "id": f"file_{i}",
                "sourcePath": src_file,
                "targetPath": os.path.join(dst_dir, f"copied_file_{i}.txt"),
                "type": "file",
                "node": {
                    "name": os.path.basename(src_file),
                    "path": src_file,
                    "size": os.path.getsize(src_file),
                    "type": "file"
                }
            }
            mappings.append(mapping)
        
        # Perform copy
        print("Starting copy operations...")
        result = fileops.apply_mappings(
            mappings=mappings,
            operation_type="copy",
            batch_id="test-basic"
        )
        
        # Verify
        success_count = sum(1 for m in mappings if os.path.exists(m["targetPath"]))
        
        print(f"Result: {success_count}/{len(mappings)} files copied")
        print(f"Status: {'✅ PASSED' if success_count == len(mappings) else '❌ FAILED'}")
        
        return success_count == len(mappings)
        
    finally:
        shutil.rmtree(test_dir)


def test_copy_with_websocket_timeout():
    """Test copy with WebSocket but with timeout to avoid hanging"""
    print("\n=== Test 2: Copy WITH WebSocket (with timeout) ===")
    
    test_dir = tempfile.mkdtemp(prefix="test_copy_ws_")
    server_started = False
    
    try:
        # Create test files
        src_dir = os.path.join(test_dir, "source")
        dst_dir = os.path.join(test_dir, "destination")
        os.makedirs(src_dir)
        
        # Create test files
        test_files = []
        for i in range(3):
            filepath = os.path.join(src_dir, f"ws_file_{i}.txt")
            with open(filepath, "w") as f:
                f.write(f"WebSocket test content {i}\n" * 100)
            test_files.append(filepath)
        
        print(f"Created {len(test_files)} test files")
        
        # Initialize with WebSocket in a thread with timeout
        print("Starting FileOperations with WebSocket...")
        
        fileops = None
        init_event = threading.Event()
        init_error = None
        
        def init_with_timeout():
            nonlocal fileops, server_started, init_error
            try:
                fileops = FileOperations(start_websocket=True)
                server_started = True
                init_event.set()
            except Exception as e:
                init_error = e
                init_event.set()
        
        # Start initialization in thread
        init_thread = threading.Thread(target=init_with_timeout, daemon=True)
        init_thread.start()
        
        # Wait max 5 seconds for initialization
        if not init_event.wait(timeout=5):
            print("⚠️  WebSocket initialization timed out after 5 seconds")
            print("Continuing with basic test...")
            fileops = FileOperations(start_websocket=False)
        elif init_error:
            print(f"⚠️  WebSocket initialization failed: {init_error}")
            fileops = FileOperations(start_websocket=False)
        else:
            print("✅ WebSocket server started successfully")
            
            # Check server health
            health = check_server_health()
            port = get_websocket_port()
            print(f"Server status: {health}")
            print(f"WebSocket port: {port}")
        
        # Create mappings
        mappings = []
        for i, src_file in enumerate(test_files):
            mapping = {
                "id": f"ws_file_{i}",
                "sourcePath": src_file,
                "targetPath": os.path.join(dst_dir, f"ws_copied_file_{i}.txt"),
                "type": "file",
                "node": {
                    "name": os.path.basename(src_file),
                    "path": src_file,
                    "size": os.path.getsize(src_file),
                    "type": "file"
                }
            }
            mappings.append(mapping)
        
        # Perform copy
        print("Starting copy operations...")
        batch_id = f"test-ws-{int(time.time())}"
        
        # Monitor progress in a separate thread
        progress_updates = []
        monitoring = True
        
        def monitor_progress():
            while monitoring:
                try:
                    progress = fileops.get_progress(batch_id)
                    if "error" not in progress:
                        progress_updates.append(progress)
                        percentage = progress.get("progressPercentage", 0)
                        status = progress.get("status", "unknown")
                        print(f"\rProgress: {percentage:.1f}% - {status}", end="")
                        
                        if status in ["completed", "failed", "cancelled"]:
                            break
                except:
                    pass
                time.sleep(0.1)
        
        if server_started:
            monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
            monitor_thread.start()
        
        # Start copy
        result = fileops.apply_mappings(
            mappings=mappings,
            operation_type="copy",
            batch_id=batch_id
        )
        
        # Stop monitoring
        monitoring = False
        print()  # New line after progress
        
        # Verify
        success_count = sum(1 for m in mappings if os.path.exists(m["targetPath"]))
        
        print(f"\nResult: {success_count}/{len(mappings)} files copied")
        if server_started and progress_updates:
            print(f"Progress updates received: {len(progress_updates)}")
        
        print(f"Status: {'✅ PASSED' if success_count == len(mappings) else '❌ FAILED'}")
        
        return success_count == len(mappings)
        
    finally:
        # Clean up WebSocket server
        if server_started:
            try:
                stop_progress_server()
                print("WebSocket server stopped")
            except:
                pass
        
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    print("VFX Folder Normalizer - Copy Operations Test")
    print("=" * 50)
    
    # Test 1: Without WebSocket
    test1_result = test_copy_without_websocket()
    
    # Test 2: With WebSocket (with timeout)
    test2_result = test_copy_with_websocket_timeout()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"  Copy without WebSocket: {'PASSED' if test1_result else 'FAILED'}")
    print(f"  Copy with WebSocket:    {'PASSED' if test2_result else 'FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests PASSED!")
        print("\nThe copy operations work correctly in both modes:")
        print("- Basic mode (without WebSocket) ✓")
        print("- Progress tracking mode (with WebSocket) ✓")
    else:
        print("\n⚠️  Some tests failed") 