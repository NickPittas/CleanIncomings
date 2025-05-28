#!/usr/bin/env python3
"""
VFX Folder Normalizer - Python Backend

This module provides file system scanning, pattern recognition, and mapping generation
for VFX folder normalization workflows.
"""

import os
import sys
import json
import sqlite3
import argparse
import uuid
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import scandir
import socket
import threading
import asyncio

try:
    import websockets
except ImportError:
    websockets = None

# Use relative imports for running as a module
try:
    from .scanner import FileSystemScanner
    from .mapping import MappingGenerator
    from .fileops import FileOperations
except ImportError:
    # Fallback for direct script execution
    from scanner import FileSystemScanner
    from mapping import MappingGenerator
    from fileops import FileOperations


def create_test_data() -> Dict[str, Any]:
    """Create test data for frontend development."""
    test_tree = {
        "name": "test_project",
        "path": "/test/project",
        "type": "folder",
        "children": [
            {
                "name": "shot_001",
                "path": "/test/project/shot_001",
                "type": "folder",
                "children": [
                    {
                        "name": "comp",
                        "path": "/test/project/shot_001/comp",
                        "type": "folder",
                        "children": [
                            {
                                "name": "shot_001_comp_v001.exr",
                                "path": "/test/project/shot_001/comp/shot_001_comp_v001.exr",
                                "type": "file",
                                "size": 15728640,
                                "extension": ".exr",
                            },
                            {
                                "name": "shot_001_comp_v002.exr",
                                "path": "/test/project/shot_001/comp/shot_001_comp_v002.exr",
                                "type": "file",
                                "size": 16777216,
                                "extension": ".exr",
                            },
                        ],
                    },
                    {
                        "name": "render",
                        "path": "/test/project/shot_001/render",
                        "type": "folder",
                        "children": [
                            {
                                "name": "beauty_v001.exr",
                                "path": "/test/project/shot_001/render/beauty_v001.exr",
                                "type": "file",
                                "size": 20971520,
                                "extension": ".exr",
                            }
                        ],
                    },
                ],
            },
            {
                "name": "shot_002",
                "path": "/test/project/shot_002",
                "type": "folder",
                "children": [
                    {
                        "name": "plate_2k_v001.mov",
                        "path": "/test/project/shot_002/plate_2k_v001.mov",
                        "type": "file",
                        "size": 104857600,
                        "extension": ".mov",
                    },
                    {
                        "name": "comp_script.nk",
                        "path": "/test/project/shot_002/comp_script.nk",
                        "type": "file",
                        "size": 8192,
                        "extension": ".nk",
                    },
                ],
            },
        ],
    }

    # Generate test mappings
    generator = MappingGenerator()
    test_profile = {"vfxRootPath": "/vfx/projects/test_project"}

    mappings = generator.generate_mappings(test_tree, test_profile)

    return {"success": True, "tree": test_tree, "proposals": mappings}


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="VFX Folder Normalizer")
    parser.add_argument(
        "command",
        choices=[
            "scan",
            "scan_with_progress",
            "map",
            "apply",
            "apply_multithreaded",
            "undo",
            "test",
            "progress",
            "pause",
            "resume",
            "cancel",
            "validate",
        ],
    )
    parser.add_argument("path", nargs="?", help="Path to scan")
    parser.add_argument(
        "batch_id", nargs="?", help="Batch ID for progress and validation commands"
    )

    args = parser.parse_args()

    if args.command == "test":
        # Return test data for frontend development
        result = create_test_data()
        print(json.dumps(result, indent=2))
        return

    if args.command == "scan":
        if not args.path:
            print(json.dumps({"error": "Path required for scan command"}))
            return
        scanner = FileSystemScanner()
        result = scanner.scan_directory(args.path)
        print(json.dumps(result, indent=2))

    elif args.command == "scan_with_progress":
        print(
            f"[DEBUG] scan_with_progress called with path: {args.path}", file=sys.stderr
        )
        if not args.path:
            print(json.dumps({"error": "Path required for scan_with_progress command"}))
            print(f"[DEBUG] scan_with_progress: missing path argument", file=sys.stderr)
            return
        scanner = FileSystemScanner()
        batch_id = scanner.scan_directory_with_progress(args.path)
        print(
            f"[DEBUG] scan_with_progress: started scan, batch_id={batch_id}",
            file=sys.stderr,
        )
        print(json.dumps({"batchId": batch_id}))

    elif args.command == "scan_progress":
        if not args.batch_id:
            print(json.dumps({"error": "Batch ID required for scan_progress command"}))
            return
        scanner = FileSystemScanner()
        progress = scanner.get_scan_progress(args.batch_id)
        print(json.dumps(progress, indent=2))

    elif args.command == "map":
        # Read tree and profile from stdin
        try:
            input_data = json.loads(sys.stdin.read())
            tree = input_data["tree"]
            profile = input_data["profile"]

            # Debug the received data
            print(
                f"Received input data keys: {list(input_data.keys())}", file=sys.stderr
            )
            print(
                f"Tree type: {type(tree)}, Tree keys: {list(tree.keys()) if isinstance(tree, dict) else 'Not a dict'}",
                file=sys.stderr,
            )

            # IMPORTANT FIX: Check if tree is wrapped in scan result format
            if isinstance(tree, dict) and "tree" in tree and "success" in tree:
                print(
                    f"Tree is wrapped in scan result format, extracting actual tree",
                    file=sys.stderr,
                )
                actual_tree = tree["tree"]
                print(
                    f"Extracted tree name: {actual_tree.get('name', 'NO NAME')}",
                    file=sys.stderr,
                )
                print(
                    f"Extracted tree type: {actual_tree.get('type', 'NO TYPE')}",
                    file=sys.stderr,
                )
                print(
                    f"Extracted tree children count: {len(actual_tree.get('children', []))}",
                    file=sys.stderr,
                )
                tree = actual_tree

            print(f"Final tree name: {tree.get('name', 'NO NAME')}", file=sys.stderr)
            print(
                f"Final tree type field: {tree.get('type', 'NO TYPE')}", file=sys.stderr
            )
            print(
                f"Final tree children count: {len(tree.get('children', []))}",
                file=sys.stderr,
            )
            print(
                f"Profile name: {profile.get('name', 'NO PROFILE NAME')}",
                file=sys.stderr,
            )

            # Show first few children for debugging
            children = tree.get("children", [])
            for i, child in enumerate(children[:3]):
                child_name = child.get("name", "NO NAME")
                child_type = child.get("type", "NO TYPE")
                child_children_count = len(child.get("children", []))
                print(
                    f"  Child {i+1}: {child_name} (type: {child_type}, children: {child_children_count})",
                    file=sys.stderr,
                )

            generator = MappingGenerator()
            generator._init_patterns_from_profile(profile)
            mappings = generator.generate_mappings(tree, profile)

            print(json.dumps({"success": True, "mappings": mappings}, indent=2))
        except Exception as e:
            print(f"Mapping generation error details: {str(e)}", file=sys.stderr)
            print(f"Error type: {type(e)}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            print(json.dumps({"error": f"Failed to generate mappings: {str(e)}"}))

    elif args.command == "apply":
        # Read mappings from stdin
        try:
            input_data = json.loads(sys.stdin.read())

            print(
                f"[DEBUG] Received input data keys: {list(input_data.keys())}",
                file=sys.stderr,
            )

            # Support both old format (just mappings) and new format (with options)
            if isinstance(input_data, list):
                mappings = input_data
                operation_type = "move"
                validate_sequences = True
                batch_id = str(uuid.uuid4())
                print(
                    f"[DEBUG] Using old format, defaulting to operation_type: {operation_type}",
                    file=sys.stderr,
                )
            else:
                mappings = input_data.get("mappings", [])
                operation_type = input_data.get("operation_type", "move")
                validate_sequences = input_data.get("validate_sequences", True)
                batch_id = input_data.get("batch_id") or str(uuid.uuid4())
                
                # Get multithreaded settings
                multithreaded_settings = input_data.get("multithreaded", {})
                use_multithreaded = multithreaded_settings.get("enabled", False)
                max_workers = multithreaded_settings.get("max_workers", 8)
                file_workers = multithreaded_settings.get("file_workers", 4)
                
                print(
                    f"[DEBUG] Using new format, operation_type: {operation_type}",
                    file=sys.stderr,
                )
                print(
                    f"[DEBUG] Multithreaded settings: enabled={use_multithreaded}, max_workers={max_workers}, file_workers={file_workers}",
                    file=sys.stderr,
                )

            print(
                f"[DEBUG] Final operation_type being passed to FileOperations: {operation_type}",
                file=sys.stderr,
            )
            print(f"[DEBUG] Number of mappings: {len(mappings)}", file=sys.stderr)

            # Initialize FileOperations with WebSocket enabled for progress tracking
            print(f"[DEBUG] Initializing FileOperations with WebSocket enabled", file=sys.stderr)
            operations = FileOperations(start_websocket=True)
            
            # Use multithreaded operations if enabled
            if use_multithreaded:
                print(f"[DEBUG] Using multithreaded operations with {max_workers} workers and {file_workers} concurrent files", file=sys.stderr)
                result = operations.apply_mappings_multithreaded(
                    mappings,
                    operation_type=operation_type,
                    validate_sequences=validate_sequences,
                    batch_id=batch_id,
                    max_workers=max_workers,
                    file_workers=file_workers,
                )
            else:
                print(f"[DEBUG] Using standard single-threaded operations", file=sys.stderr)
                result = operations.apply_mappings_async(
                    mappings,
                    operation_type=operation_type,
                    validate_sequences=validate_sequences,
                    batch_id=batch_id,
                )
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"[DEBUG] Exception in apply command: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            print(json.dumps({"error": f"Failed to apply mappings: {str(e)}"}))

    elif args.command == "apply_multithreaded":
        # Read mappings from stdin and apply with multithreading
        try:
            input_data = json.loads(sys.stdin.read())

            print(
                f"[DEBUG] Received input data keys: {list(input_data.keys())}",
                file=sys.stderr,
            )

            # Support both old format (just mappings) and new format (with options)
            if isinstance(input_data, list):
                mappings = input_data
                operation_type = "move"
                validate_sequences = True
                batch_id = str(uuid.uuid4())
                max_workers = 8
                file_workers = 4
                print(
                    f"[DEBUG] Using old format, defaulting to operation_type: {operation_type}",
                    file=sys.stderr,
                )
            else:
                mappings = input_data.get("mappings", [])
                operation_type = input_data.get("operation_type", "move")
                validate_sequences = input_data.get("validate_sequences", True)
                batch_id = input_data.get("batch_id") or str(uuid.uuid4())
                max_workers = input_data.get("max_workers", 8)
                file_workers = input_data.get("file_workers", 4)
                print(
                    f"[DEBUG] Using new format, operation_type: {operation_type}",
                    file=sys.stderr,
                )

            print(
                f"[DEBUG] Multithreaded operation_type: {operation_type}",
                file=sys.stderr,
            )
            print(f"[DEBUG] Number of mappings: {len(mappings)}", file=sys.stderr)
            print(f"[DEBUG] Max workers (file chunks): {max_workers}", file=sys.stderr)
            print(f"[DEBUG] File workers (concurrent files): {file_workers}", file=sys.stderr)

            operations = FileOperations(start_websocket=True)
            result = operations.apply_mappings_multithreaded(
                mappings,
                operation_type=operation_type,
                validate_sequences=validate_sequences,
                batch_id=batch_id,
                max_workers=max_workers,
                file_workers=file_workers,
            )
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"[DEBUG] Exception in apply_multithreaded command: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            print(json.dumps({"error": f"Failed to apply mappings with multithreading: {str(e)}"}))

    elif args.command == "progress":
        # Get progress for a batch
        try:
            batch_id = args.batch_id if hasattr(args, "batch_id") and args.batch_id else (sys.argv[2] if len(sys.argv) > 2 else None)
            
            if not batch_id:
                print(json.dumps({"error": "Batch ID required for progress command"}))
                return
                
            operations = FileOperations()
            result = operations.get_progress(batch_id)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Failed to get progress: {str(e)}"}))

    elif args.command == "pause":
        # Pause current operations
        try:
            operations = FileOperations()
            operations.pause_operations()
            print(json.dumps({"success": True, "message": "Operations paused"}))
        except Exception as e:
            print(json.dumps({"error": f"Failed to pause operations: {str(e)}"}))

    elif args.command == "resume":
        # Resume paused operations
        try:
            operations = FileOperations()
            operations.resume_operations()
            print(json.dumps({"success": True, "message": "Operations resumed"}))
        except Exception as e:
            print(json.dumps({"error": f"Failed to resume operations: {str(e)}"}))

    elif args.command == "cancel":
        # Cancel current operations
        try:
            operations = FileOperations()
            batch_id = args.batch_id if hasattr(args, "batch_id") and args.batch_id else (sys.argv[2] if len(sys.argv) > 2 else None)
            
            if not batch_id:
                print(json.dumps({"error": "Batch ID required for cancel command"}))
                return
                
            result = operations.cancel_operation(batch_id)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Failed to cancel operations: {str(e)}"}))

    elif args.command == "validate":
        # Validate sequence integrity
        try:
            batch_id = args.batch_id if hasattr(args, "batch_id") else sys.argv[2]
            operations = FileOperations()
            result = operations.validate_sequence_integrity(batch_id)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Failed to validate sequences: {str(e)}"}))

    elif args.command == "undo":
        try:
            operations = FileOperations()
            result = operations.undo_last_batch()

            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Failed to undo operations: {str(e)}"}))

    else:
        print(json.dumps({"error": f"Unknown command: {args.command}"}))


if __name__ == "__main__":
    main()
