"""
Simple HTTP server to serve the progress viewer HTML page.
This script only serves the HTML page and does not start another WebSocket server.
"""
import os
import sys
import http.server
import socketserver
import webbrowser
import threading
import time

# Define the port to serve on
PORT = 8080

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Translate URL path to file system path in static directory"""
        path = super().translate_path(path)
        # Redirect root path to progress_viewer.html
        if path.endswith('/'):
            return os.path.join(self.static_dir, "progress_viewer.html")
        return os.path.join(self.static_dir, os.path.basename(path))
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def open_browser():
    """Open the browser after a short delay"""
    time.sleep(1)
    url = f"http://localhost:{PORT}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

def main():
    # Change to the directory where this script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a simple HTTP server
    handler = SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    print(f"Serving progress viewer at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        httpd.shutdown()

if __name__ == "__main__":
    main()
