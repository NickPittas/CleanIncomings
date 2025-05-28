"""
New WebSocket progress server with different ports to avoid conflicts.
Uses port 9080 for HTTP and 9765 for WebSocket.
"""
import os
import sys
import time
import asyncio
import threading
import webbrowser
import json
import websockets
import http.server
import socketserver
from threading import Thread
from functools import partial
from pathlib import Path

# Global settings - USING DIFFERENT PORTS TO AVOID CONFLICTS
WEBSOCKET_PORT = 9765  # Changed from 8765
HTTP_PORT = 9080       # Changed from 8080
clients = set()
progress_data = {}
script_dir = Path(__file__).parent
static_dir = script_dir / "static"

# Ensure progress directory exists
progress_dir = script_dir / "_progress"
progress_dir.mkdir(exist_ok=True)

# Configure cross-thread communication
message_queue = []
queue_lock = threading.Lock()

def print_with_timestamp(message):
    """Print a message with a timestamp"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {message}")

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves files from the static directory"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Map request paths to the static directory"""
        # Redirect root path to enhanced_progress.html
        if path == '/' or path == '':
            enhanced_path = os.path.join(static_dir, "enhanced_progress.html")
            if os.path.exists(enhanced_path):
                return enhanced_path
            return os.path.join(static_dir, "progress_viewer.html")
        return os.path.join(static_dir, os.path.basename(path))
    
    def log_message(self, format, *args):
        """Override to use our custom logging"""
        print_with_timestamp(f"HTTP: {format % args}")

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    print_with_timestamp(f"WebSocket: Client connected")
    clients.add(websocket)
    
    # Send all current progress data to the new client
    try:
        for batch_id, data in progress_data.items():
            await websocket.send(json.dumps({
                'type': 'progress',
                'batch_id': batch_id,
                **data
            }))
    except Exception as e:
        print_with_timestamp(f"WebSocket: Error sending initial data: {e}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Handle ping messages
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time()
                    }))
            except json.JSONDecodeError:
                print_with_timestamp(f"WebSocket: Invalid message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print_with_timestamp("WebSocket: Client disconnected normally")
    except Exception as e:
        print_with_timestamp(f"WebSocket: Error: {e}")
    finally:
        clients.remove(websocket)

async def process_queue():
    """Process messages from the queue and send to WebSocket clients"""
    while True:
        # Check if there are messages to process
        with queue_lock:
            if message_queue:
                message = message_queue.pop(0)
            else:
                message = None
        
        if message:
            batch_id, data = message
            progress_data[batch_id] = data
            
            if clients:
                message_json = json.dumps({
                    'type': 'progress',
                    'batch_id': batch_id,
                    **data
                })
                
                # Send to all clients
                disconnected = set()
                for client in clients:
                    try:
                        await client.send(message_json)
                    except:
                        disconnected.add(client)
                
                # Remove disconnected clients
                for client in disconnected:
                    clients.discard(client)
        
        # Sleep briefly to prevent high CPU usage
        await asyncio.sleep(0.05)

def send_progress_update(batch_id, files_processed, total_files, current_file="", status="running"):
    """Send a progress update (can be called from other threads/processes)"""
    # Calculate percentage
    percentage = 0
    if total_files > 0:
        percentage = min(100.0, (files_processed / total_files) * 100)
    
    # Prepare progress data
    data = {
        'filesProcessed': files_processed,
        'totalFiles': total_files,
        'progressPercentage': percentage,
        'currentFile': current_file,
        'status': status,
        'timestamp': time.time()
    }
    
    # Add batch_id type hint for clients
    if '-' in batch_id:
        operation_type = batch_id.split('-')[0]
        if operation_type in ['copy', 'move', 'scan', 'organize']:
            data['operationType'] = operation_type
    
    # Add to queue for processing
    with queue_lock:
        message_queue.append((batch_id, data))
    
    # Also save to disk for recovery
    try:
        save_path = progress_dir / f"progress_{batch_id}.json"
        with open(save_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print_with_timestamp(f"Error saving progress to disk: {e}")
    
    return True

def start_http_server():
    """Start the HTTP server in a separate thread"""
    print_with_timestamp(f"Starting HTTP server on port {HTTP_PORT}...")
    
    # Ensure the static directory exists
    if not static_dir.exists():
        static_dir.mkdir(exist_ok=True)
    
    handler = partial(SimpleHTTPRequestHandler, directory=str(static_dir))
    
    try:
        httpd = socketserver.ThreadingTCPServer(("", HTTP_PORT), handler)
        
        def run_server():
            print_with_timestamp(f"HTTP server running at http://localhost:{HTTP_PORT}")
            httpd.serve_forever()
        
        thread = Thread(target=run_server, daemon=True)
        thread.start()
        return httpd, thread
    except Exception as e:
        print_with_timestamp(f"Error starting HTTP server: {e}")
        return None, None

async def start_websocket_server():
    """Start the WebSocket server"""
    print_with_timestamp(f"Starting WebSocket server on port {WEBSOCKET_PORT}...")
    
    # Start the server
    try:
        server = await websockets.serve(websocket_handler, "localhost", WEBSOCKET_PORT)
        print_with_timestamp(f"WebSocket server running on ws://localhost:{WEBSOCKET_PORT}")
        
        # Start the queue processor
        asyncio.create_task(process_queue())
        
        return server
    except Exception as e:
        print_with_timestamp(f"Error starting WebSocket server: {e}")
        return None

def open_browser():
    """Open the browser to view the progress page"""
    url = f"http://localhost:{HTTP_PORT}"
    print_with_timestamp(f"Opening browser at {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print_with_timestamp(f"Error opening browser: {e}")
        print_with_timestamp(f"Please manually open: {url}")

async def main():
    """Main function"""
    print_with_timestamp("Starting WebSocket Progress System on alternate ports")
    print_with_timestamp(f"HTTP: {HTTP_PORT}, WebSocket: {WEBSOCKET_PORT}")
    
    # Update the WebSocket URL in enhanced_progress.html
    enhanced_path = static_dir / "enhanced_progress.html"
    if enhanced_path.exists():
        try:
            with open(enhanced_path, 'r') as f:
                content = f.read()
            
            # Replace WebSocket port
            content = content.replace("ws://localhost:8765", f"ws://localhost:{WEBSOCKET_PORT}")
            
            with open(enhanced_path, 'w') as f:
                f.write(content)
            
            print_with_timestamp(f"Updated WebSocket URL in enhanced_progress.html")
        except Exception as e:
            print_with_timestamp(f"Error updating WebSocket URL: {e}")
    
    # Start HTTP server
    http_server, http_thread = start_http_server()
    if not http_server:
        print_with_timestamp("Failed to start HTTP server")
        return
    
    # Start WebSocket server
    websocket_server = await start_websocket_server()
    if not websocket_server:
        print_with_timestamp("Failed to start WebSocket server")
        if http_server:
            http_server.shutdown()
        return
    
    # Open browser
    threading.Timer(1, open_browser).start()
    
    # Demo progress updates
    print_with_timestamp("Sending demo progress updates...")
    demo_batch_id = f"demo-{int(time.time())}"
    total_files = 5
    
    for i in range(total_files + 1):
        # For each file, send multiple updates to show filename changes
        if i < total_files:
            file_steps = 10  # Show 10 updates per file
            for step in range(1, file_steps + 1):
                percent_done = (step / file_steps) * 100
                current_file = f"demo_file_{i+1}.txt ({percent_done:.0f}%)"
                
                # Calculate overall progress
                overall_progress = i + (step / file_steps)
                
                send_progress_update(
                    batch_id=demo_batch_id,
                    files_processed=overall_progress,
                    total_files=total_files,
                    current_file=current_file,
                    status="running"
                )
                await asyncio.sleep(0.2)  # Update every 200ms
        else:
            # Final update
            send_progress_update(
                batch_id=demo_batch_id,
                files_processed=total_files,
                total_files=total_files,
                current_file="",
                status="completed"
            )
    
    print_with_timestamp("Demo progress updates complete")
    print_with_timestamp("Servers are running. Press Ctrl+C to stop.")
    print_with_timestamp(f"View progress at: http://localhost:{HTTP_PORT}")
    
    try:
        # Keep the server running until interrupted
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # Close the WebSocket server
        websocket_server.close()
        await websocket_server.wait_closed()
        
        # Stop the HTTP server
        http_server.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_with_timestamp("Shutting down...")
    except Exception as e:
        print_with_timestamp(f"Error: {e}")
    finally:
        print_with_timestamp("Server stopped")
