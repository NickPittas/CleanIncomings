"""
Start the progress monitoring system - both web server and WebSocket server.
This script serves the HTML progress viewer and starts the WebSocket server
for real-time progress updates during file operations.
"""
import os
import sys
import time
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s',
                   datefmt='%H:%M:%S')
logger = logging.getLogger("progress_monitor")

# Import our robust WebSocket server
try:
    from robust_websocket import start_server, stop_server, get_websocket_port
    WEBSOCKET_AVAILABLE = True
except ImportError:
    logger.warning("WebSocket module not available. Progress updates will be limited.")
    WEBSOCKET_AVAILABLE = False

class StaticFileHandler(SimpleHTTPRequestHandler):
    """Simple HTTP handler that serves static files"""
    
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
        """Override log_message to use our logger"""
        logger.info(format % args)

def start_http_server(port=8000):
    """Start the HTTP server to serve the progress viewer HTML"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, StaticFileHandler)
        logger.info(f"Starting HTTP server on port {port}")
        
        # Start server in a thread
        server_thread = threading.Thread(
            target=httpd.serve_forever,
            daemon=True
        )
        server_thread.start()
        return httpd, server_thread
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        return None, None

def open_browser(url):
    """Open the progress viewer in the default browser"""
    try:
        logger.info(f"Opening browser at {url}")
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        print(f"Please open this URL in your browser: {url}")

def main():
    """Start the progress monitoring system"""
    # Start WebSocket server
    if WEBSOCKET_AVAILABLE:
        if start_server():
            websocket_port = get_websocket_port()
            logger.info(f"WebSocket server started on port {websocket_port}")
        else:
            logger.error("Failed to start WebSocket server")
            return
    else:
        logger.warning("WebSocket functionality not available")
    
    # Start HTTP server for the progress viewer
    http_port = 8080
    httpd, http_thread = start_http_server(http_port)
    if not httpd:
        logger.error("Failed to start HTTP server")
        if WEBSOCKET_AVAILABLE:
            stop_server()
        return
    
    # Open browser
    url = f"http://localhost:{http_port}"
    logger.info(f"Progress monitor available at {url}")
    
    try:
        open_browser(url)
        
        # Keep running until user interrupts
        logger.info("Press Ctrl+C to stop the servers")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    finally:
        # Clean up
        if httpd:
            logger.info("Stopping HTTP server")
            httpd.shutdown()
        
        if WEBSOCKET_AVAILABLE:
            logger.info("Stopping WebSocket server")
            stop_server()
        
        logger.info("All servers stopped")

if __name__ == "__main__":
    main()
