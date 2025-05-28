"""
All-in-one script to start the WebSocket progress system.

This script:
1. Checks if required servers are already running
2. Starts the WebSocket server if needed
3. Starts the HTTP server if needed
4. Opens the browser to display the progress viewer

Usage:
    python start_progress_system.py
"""
import os
import sys
import socket
import time
import webbrowser
import subprocess
import threading
import atexit
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("progress_system")

# Global variables
WEBSOCKET_PORT = 8765
HTTP_PORT = 8080
processes = []

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def print_status(message, success=True):
    """Print a status message with color"""
    if success:
        logger.info(f"✓ {message}")
    else:
        logger.warning(f"✗ {message}")

def start_websocket_server():
    """Start the WebSocket server if it's not already running"""
    if check_port_in_use(WEBSOCKET_PORT):
        print_status(f"WebSocket Server (Port {WEBSOCKET_PORT}) already running")
        return True

    logger.info("Starting WebSocket server...")
    
    # Find the robust_websocket.py file
    script_dir = Path(__file__).parent
    websocket_path = script_dir / "robust_websocket.py"
    
    if not websocket_path.exists():
        logger.error(f"Cannot find {websocket_path}")
        return False
    
    # Start the server as a separate process
    try:
        # Using the robust_websocket directly with its built-in test mode
        process = subprocess.Popen(
            [sys.executable, str(websocket_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        processes.append(process)
        
        # Wait for the server to start (up to 5 seconds)
        for _ in range(10):
            if check_port_in_use(WEBSOCKET_PORT):
                print_status(f"WebSocket Server started on port {WEBSOCKET_PORT}")
                return True
            time.sleep(0.5)
        
        logger.error("WebSocket server didn't start within the timeout period")
        return False
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        return False

def start_http_server():
    """Start the HTTP server if it's not already running"""
    if check_port_in_use(HTTP_PORT):
        print_status(f"HTTP Server (Port {HTTP_PORT}) already running")
        return True

    logger.info("Starting HTTP server...")
    
    # Find the serve_progress_page.py file
    script_dir = Path(__file__).parent
    http_path = script_dir / "serve_progress_page.py"
    
    if not http_path.exists():
        logger.error(f"Cannot find {http_path}")
        return False
    
    # Start the server as a separate process
    try:
        process = subprocess.Popen(
            [sys.executable, str(http_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        processes.append(process)
        
        # Wait for the server to start (up to 5 seconds)
        for _ in range(10):
            if check_port_in_use(HTTP_PORT):
                print_status(f"HTTP Server started on port {HTTP_PORT}")
                return True
            time.sleep(0.5)
        
        logger.error("HTTP server didn't start within the timeout period")
        return False
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        return False

def open_progress_viewer():
    """Open the progress viewer in the default browser"""
    url = f"http://localhost:{HTTP_PORT}"
    logger.info(f"Opening progress viewer at {url}")
    
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        logger.info(f"Please manually open: {url}")

def cleanup():
    """Clean up processes on exit"""
    logger.info("Cleaning up processes...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    logger.info("Interrupt received, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    """Main function"""
    # Register cleanup functions
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=== Starting WebSocket Progress System ===")
    
    # Ensure the static directory exists and has the progress viewer
    static_dir = Path(__file__).parent / "static"
    progress_html = static_dir / "progress_viewer.html"
    
    if not progress_html.exists():
        logger.error(f"Progress viewer HTML not found at: {progress_html}")
        logger.error("Please ensure the static directory is set up correctly")
        return False
    
    # Start servers
    ws_success = start_websocket_server()
    http_success = start_http_server()
    
    if ws_success and http_success:
        logger.info("Both servers started successfully!")
        open_progress_viewer()
        
        logger.info("Servers are running. Press Ctrl+C to stop.")
        try:
            # Keep the script running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        
        return True
    else:
        if not ws_success:
            logger.error("WebSocket server failed to start")
        if not http_success:
            logger.error("HTTP server failed to start")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
