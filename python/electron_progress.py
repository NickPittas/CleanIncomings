"""
Electron Progress Module

This module provides functions to communicate with the Electron WebSocket server
for progress updates through IPC or filesystem-based communication.
"""
import os
import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional

# Directory for progress data and port info
def get_progress_dir() -> str:
    """Get the directory for progress data"""
    progress_dir = os.path.join(os.path.dirname(__file__), "_progress")
    os.makedirs(progress_dir, exist_ok=True)
    return progress_dir

def get_websocket_port() -> Optional[int]:
    """Read WebSocket port from file written by Electron"""
    try:
        port_file = os.path.join(get_progress_dir(), "websocket_port.txt")
        if os.path.exists(port_file):
            with open(port_file, "r") as f:
                port = int(f.read().strip())
                return port
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read WebSocket port: {e}", file=sys.stderr)
        return None

def check_server_health() -> Dict[str, Any]:
    """Check WebSocket server health"""
    port = get_websocket_port()
    if port is None:
        return {"running": False, "message": "No port file found"}
    return {"running": True, "port": port}

def send_progress_update(
    batch_id: str,
    files_processed: int,
    total_files: int,
    current_file: str = "",
    status: str = "running"
) -> bool:
    """
    Send progress update via filesystem for Electron to pick up and forward to WebSocket.
    
    This is a compatible replacement for the WebSocket-based function
    from progress_server.py, but uses the built-in Electron WebSocket server.
    """
    try:
        # Calculate percentage with safeguards
        percentage = 0
        if total_files > 0:
            percentage = min(100.0, (files_processed / total_files) * 100)
        
        # Force 100% for completed status
        if status == "completed":
            percentage = 100.0

        # Format current file to be more user-friendly
        if current_file and len(current_file) > 60:
            parts = current_file.split(os.sep)
            if len(parts) > 3:
                current_file = os.path.join(parts[0], '...', parts[-1])

        # Create progress data
        progress_data = {
            "type": "progress",
            "batch_id": batch_id,
            "filesProcessed": files_processed,
            "totalFiles": total_files,
            "progressPercentage": round(percentage, 1),
            "currentFile": current_file,
            "status": status,
            "timestamp": int(time.time() * 1000),
            "operationType": batch_id.split('-')[0] if '-' in batch_id else "unknown"
        }
        
        # Write progress to file for polling fallback
        progress_file = os.path.join(get_progress_dir(), f"progress_{batch_id}.json")
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f)
        
        # Write to a special "latest.json" file for quick access
        latest_file = os.path.join(get_progress_dir(), "latest_progress.json")
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f)
        
        # Log occasionally to avoid spamming
        if files_processed % 500 == 0 or status == "completed" or status == "failed":
            print(f"[DEBUG] Progress update for {batch_id}: {files_processed}/{total_files} - {status}", file=sys.stderr)
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send progress update: {e}", file=sys.stderr)
        return False

def start_progress_server() -> bool:
    """
    Dummy function to maintain compatibility with the original progress_server.py.
    The actual WebSocket server is now managed by Electron.
    """
    print("[INFO] Using Electron-managed WebSocket server", file=sys.stderr)
    return True

# For backwards compatibility
WEBSOCKET_AVAILABLE = True
SERVER_STARTED = True

# Print startup message
print(f"[INFO] Electron progress module loaded", file=sys.stderr)
