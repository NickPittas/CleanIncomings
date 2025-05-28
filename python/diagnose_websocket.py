"""
Diagnostic script to check WebSocket and HTTP server connections
"""
import os
import sys
import socket
import time
import webbrowser
import subprocess

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def print_status(message, success=True):
    """Print a status message with color"""
    if success:
        print(f"\033[92m✓ {message}\033[0m")
    else:
        print(f"\033[91m✗ {message}\033[0m")

def main():
    print("\n=== WebSocket Progress System Diagnostics ===\n")
    
    # Check if WebSocket server is running on port 8765
    websocket_running = check_port_in_use(8765)
    print_status("WebSocket Server (Port 8765)", websocket_running)
    
    # Check if HTTP server is running on port 8080
    http_running = check_port_in_use(8080)
    print_status("HTTP Server (Port 8080)", http_running)
    
    # Check if progress viewer HTML exists
    html_path = os.path.join(os.path.dirname(__file__), "static", "progress_viewer.html")
    html_exists = os.path.exists(html_path)
    print_status("Progress Viewer HTML", html_exists)
    
    print("\n=== Troubleshooting Steps ===\n")
    
    if not websocket_running:
        print("Starting WebSocket server...")
        # Start the robust WebSocket server
        subprocess.Popen([sys.executable, "-c", 
                          "from robust_websocket import start_server; start_server(); import time; time.sleep(3600)"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        if check_port_in_use(8765):
            print_status("WebSocket server started successfully")
        else:
            print_status("Failed to start WebSocket server", False)
    
    if not http_running:
        print("Starting HTTP server...")
        # Start the HTTP server
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "serve_progress_page.py")],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        if check_port_in_use(8080):
            print_status("HTTP server started successfully")
        else:
            print_status("Failed to start HTTP server", False)
    
    # Check if both servers are running now
    websocket_running = check_port_in_use(8765)
    http_running = check_port_in_use(8080)
    
    if websocket_running and http_running:
        print("\n✅ Both servers are running! Opening browser...")
        webbrowser.open("http://localhost:8080")
        print("\nIf the browser doesn't connect to the WebSocket, try manually refreshing the page.")
    else:
        print("\n❌ Not all servers are running. Check the output above for details.")
    
    print("\nPress Ctrl+C to exit this diagnostic script")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting diagnostic script")

if __name__ == "__main__":
    main()
