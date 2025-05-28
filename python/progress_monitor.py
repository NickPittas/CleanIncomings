"""
WebSocket progress monitoring system for real-time file operation updates.

This module provides an integrated progress monitoring system for file operations
with both WebSocket updates and browser-based visualization.
"""
import os
import sys
import time
import json
import asyncio
import threading
import webbrowser
import logging
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("progress_monitor")

# Fixed ports to avoid conflicts
HTTP_PORT = 7800
WS_PORT = 7801

# Global state
_clients = set()
_active_operations = {}
_is_running = False
_http_server = None
_ws_server = None
_server_thread = None
_shutdown_event = threading.Event()

# HTML template for the progress viewer
_html_template = """<!DOCTYPE html>
<html>
<head>
    <title>File Operation Progress</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f8fa;
            color: #333;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        h1, h2 {
            color: #2c3e50;
            margin-top: 0;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
        .connecting { background-color: #fff3cd; color: #856404; }
        
        .progress-bar {
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background-color: #007bff;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-size: 12px;
            line-height: 20px;
            transition: width 0.3s;
        }
        .file-container {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 10px;
            margin: 10px 0;
            border-radius: 0 4px 4px 0;
        }
        .file-name {
            font-family: monospace;
            word-break: break-all;
            padding: 5px 0;
        }
        .highlight {
            animation: flash 1s;
        }
        @keyframes flash {
            0% { background-color: #fffacd; }
            100% { background-color: transparent; }
        }
        .stats {
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
        }
        .stat-box {
            text-align: center;
            flex: 1;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            margin: 0 5px;
        }
        .stat-value {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            font-size: 12px;
            color: #7f8c8d;
        }
        .operation-badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: #007bff;
            border-radius: 12px;
            margin-left: 10px;
        }
        .operation-badge.copy { background-color: #007bff; }
        .operation-badge.move { background-color: #6f42c1; }
        .operation-badge.scan { background-color: #fd7e14; }
        
        .log {
            height: 200px;
            overflow-y: auto;
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 10px;
            font-family: monospace;
            border-radius: 4px;
        }
        .log-entry {
            margin-bottom: 5px;
            border-bottom: 1px solid #34495e;
            padding-bottom: 5px;
        }
        .log-time {
            color: #f1c40f;
            margin-right: 5px;
        }
        .active-operations {
            margin-top: 20px;
        }
        .operation-item {
            padding: 10px;
            margin-bottom: 5px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }
        .operation-item.completed { border-left-color: #28a745; }
        .operation-item.error { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <div class="card">
        <h1>File Operation Progress <span id="operationBadge" class="operation-badge">copy</span></h1>
        <div id="status" class="status disconnected">Disconnected</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value" id="fileCount">0/0</div>
                <div class="stat-label">Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="percentage">0%</div>
                <div class="stat-label">Complete</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="copySpeed">0 MB/s</div>
                <div class="stat-label">Speed</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div id="progressFill" class="progress-fill" style="width: 0%">0%</div>
        </div>
        
        <div class="file-container">
            <div>Current File:</div>
            <div id="currentFile" class="file-name">-</div>
        </div>
    </div>
    
    <div class="card">
        <h2>Active Operations</h2>
        <div id="operations" class="active-operations">
            <div class="operation-item">No active operations</div>
        </div>
    </div>
    
    <div class="card">
        <h2>Activity Log</h2>
        <div id="log" class="log"></div>
    </div>
    
    <script>
        let ws = null;
        let reconnectAttempts = 0;
        let operations = {};
        
        function log(message) {
            const logElem = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const time = document.createElement('span');
            time.className = 'log-time';
            time.textContent = new Date().toLocaleTimeString();
            
            entry.appendChild(time);
            entry.appendChild(document.createTextNode(message));
            
            logElem.appendChild(entry);
            logElem.scrollTop = logElem.scrollHeight;
        }
        
        function updateOperations() {
            const container = document.getElementById('operations');
            container.innerHTML = '';
            
            if (Object.keys(operations).length === 0) {
                const div = document.createElement('div');
                div.className = 'operation-item';
                div.textContent = 'No active operations';
                container.appendChild(div);
                return;
            }
            
            for (const [batchId, data] of Object.entries(operations)) {
                const div = document.createElement('div');
                div.className = `operation-item ${data.status}`;
                div.id = `operation-${batchId}`;
                
                let opType = 'Unknown';
                if (batchId.startsWith('copy-')) opType = 'Copy';
                else if (batchId.startsWith('move-')) opType = 'Move';
                else if (batchId.startsWith('scan-')) opType = 'Scan';
                
                const progress = data.progressPercentage || 0;
                const fileCount = data.filesProcessed ? Math.floor(data.filesProcessed) : 0;
                const totalFiles = data.totalFiles || 0;
                
                div.innerHTML = `
                    <strong>${opType} Operation:</strong> ${batchId}
                    <div>Status: ${data.status.toUpperCase()}</div>
                    <div>Progress: ${progress.toFixed(1)}% (${fileCount}/${totalFiles} files)</div>
                `;
                
                container.appendChild(div);
            }
        }
        
        function connect() {
            log('Connecting to WebSocket server...');
            
            const status = document.getElementById('status');
            status.textContent = 'Connecting...';
            status.className = 'status connecting';
            
            ws = new WebSocket('ws://localhost:WS_PORT_PLACEHOLDER');
            
            ws.onopen = function() {
                log('WebSocket connected');
                status.textContent = 'Connected';
                status.className = 'status connected';
                reconnectAttempts = 0;
            };
            
            ws.onclose = function() {
                log('WebSocket disconnected');
                status.textContent = 'Disconnected';
                status.className = 'status disconnected';
                
                if (reconnectAttempts < 5) {
                    reconnectAttempts++;
                    const delay = 1000 * Math.min(Math.pow(2, reconnectAttempts), 10);
                    log(`Reconnecting in ${delay/1000} seconds...`);
                    setTimeout(connect, delay);
                }
            };
            
            ws.onerror = function() {
                log('WebSocket error occurred');
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'progress') {
                        // Store operation data
                        operations[data.batch_id] = data;
                        updateOperations();
                        
                        // Update progress bar for the current operation
                        const percent = data.progressPercentage || 0;
                        const progressFill = document.getElementById('progressFill');
                        progressFill.style.width = `${percent}%`;
                        progressFill.textContent = `${percent.toFixed(1)}%`;
                        
                        // Update percentage display
                        document.getElementById('percentage').textContent = `${percent.toFixed(1)}%`;
                        
                        // Update file count
                        document.getElementById('fileCount').textContent = 
                            `${Math.floor(data.filesProcessed || 0)}/${data.totalFiles || 0}`;
                        
                        // Update speed if available
                        if (data.speed) {
                            document.getElementById('copySpeed').textContent = 
                                `${data.speed.toFixed(1)} MB/s`;
                        }
                        
                        // Update operation badge
                        const opType = data.operationType || 'copy';
                        const badge = document.getElementById('operationBadge');
                        badge.textContent = opType;
                        badge.className = `operation-badge ${opType}`;
                        
                        // Update current file with highlight
                        const fileElem = document.getElementById('currentFile');
                        if (data.currentFile && fileElem.textContent !== data.currentFile) {
                            fileElem.classList.remove('highlight');
                            void fileElem.offsetWidth; // Force reflow
                            fileElem.textContent = data.currentFile;
                            fileElem.classList.add('highlight');
                            log(`Processing: ${data.currentFile}`);
                        }
                    } else {
                        log(`Received: ${JSON.stringify(data)}`);
                    }
                } catch (error) {
                    log(`Error parsing message: ${error.message}`);
                }
            };
        }
        
        window.onload = function() {
            log('Page loaded');
            connect();
        };
    </script>
</body>
</html>
""".replace("WS_PORT_PLACEHOLDER", str(WS_PORT))

class ProgressHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the progress viewer page"""
    
    def do_GET(self):
        """Handle GET requests by serving the progress viewer HTML"""
        if self.path == '/' or self.path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(_html_template.encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(f"HTTP: {format % args}")

async def _websocket_handler(websocket):
    """Handle WebSocket connections"""
    logger.info(f"WebSocket client connected")
    _clients.add(websocket)
    
    # Send current operation data to the new client
    for batch_id, data in _active_operations.items():
        try:
            await websocket.send(json.dumps({
                'type': 'progress',
                'batch_id': batch_id,
                **data
            }))
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
    
    try:
        async for message in websocket:
            # Just echo back pings for testing
            try:
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time()
                    }))
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket client disconnected")
    finally:
        _clients.remove(websocket)

async def _broadcast_progress(data):
    """Send progress updates to all connected clients"""
    if not _clients:
        return
    
    batch_id = data.get('batch_id')
    if not batch_id:
        return
    
    # Store operation data
    _active_operations[batch_id] = data
    
    # Remove completed operations after a while
    if data.get('status') in ('completed', 'error', 'failed'):
        def _remove_later():
            time.sleep(300)  # Keep completed operations visible for 5 minutes
            if batch_id in _active_operations:
                del _active_operations[batch_id]
        
        threading.Thread(target=_remove_later, daemon=True).start()
    
    # Send to all clients
    message = json.dumps({'type': 'progress', **data})
    disconnected = set()
    
    for client in _clients:
        try:
            await client.send(message)
        except Exception:
            disconnected.add(client)
    
    # Remove disconnected clients
    for client in disconnected:
        _clients.discard(client)

def send_progress_update(batch_id, files_processed, total_files, current_file="", status="running", **kwargs):
    """
    Send a progress update via WebSocket
    
    Args:
        batch_id (str): Unique ID for the operation batch
        files_processed (int/float): Number of files processed (can be fractional for partial progress)
        total_files (int): Total number of files to process
        current_file (str): Name of the file currently being processed
        status (str): Status of the operation (running, completed, error, etc.)
        **kwargs: Additional data to include in the progress update
    
    Returns:
        bool: True if the update was sent, False otherwise
    """
    if not _is_running:
        logger.debug(f"Progress server not running, update not sent")
        return False
    
    # Calculate percentage
    percentage = 0
    if total_files > 0:
        percentage = min(100.0, (files_processed / total_files) * 100)
    
    # Prepare progress data
    data = {
        'batch_id': batch_id,
        'filesProcessed': files_processed,
        'totalFiles': total_files,
        'progressPercentage': percentage,
        'currentFile': current_file,
        'status': status,
        'timestamp': time.time(),
        **kwargs
    }
    
    # Add operation type hint based on batch_id
    if '-' in batch_id:
        operation_type = batch_id.split('-')[0]
        if operation_type in ('copy', 'move', 'scan', 'organize'):
            data['operationType'] = operation_type
    
    # Send via WebSocket (using asyncio.run_coroutine_threadsafe)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(_broadcast_progress(data), loop)
            return True
    except Exception as e:
        logger.error(f"Error sending progress update: {e}")
    
    return False

async def _start_websocket_server():
    """Start the WebSocket server"""
    try:
        server = await websockets.serve(_websocket_handler, 'localhost', WS_PORT)
        logger.info(f"WebSocket server started on port {WS_PORT}")
        return server
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        return None

def _start_http_server():
    """Start the HTTP server"""
    try:
        server = HTTPServer(('', HTTP_PORT), ProgressHTTPHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"HTTP server started on port {HTTP_PORT}")
        return server
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        return None

async def _server_main():
    """Main server function"""
    global _http_server, _ws_server, _is_running
    
    # Start HTTP server
    _http_server = _start_http_server()
    if not _http_server:
        return
    
    # Start WebSocket server
    _ws_server = await _start_websocket_server()
    if not _ws_server:
        return
    
    _is_running = True
    
    # Wait for shutdown signal
    while not _shutdown_event.is_set():
        await asyncio.sleep(0.5)
    
    # Shutdown
    if _ws_server:
        _ws_server.close()
        await _ws_server.wait_closed()
    
    if _http_server:
        _http_server.shutdown()
    
    _is_running = False
    logger.info("Progress servers stopped")

def _run_server_thread():
    """Run the server in a thread"""
    asyncio.run(_server_main())

def start_progress_server():
    """
    Start the progress monitoring server
    
    Returns:
        bool: True if server started successfully, False otherwise
    """
    global _server_thread, _shutdown_event, _is_running
    
    if _is_running:
        logger.info("Progress server is already running")
        return True
    
    # Reset shutdown event
    _shutdown_event.clear()
    
    # Start server in a thread
    _server_thread = threading.Thread(target=_run_server_thread, daemon=True)
    _server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(1.0)
    
    # Open browser
    if _is_running:
        open_progress_viewer()
        return True
    
    logger.error("Failed to start progress server")
    return False

def stop_progress_server():
    """
    Stop the progress monitoring server
    
    Returns:
        bool: True if server stopped successfully, False otherwise
    """
    global _server_thread, _shutdown_event, _is_running
    
    if not _is_running:
        logger.info("Progress server is not running")
        return True
    
    # Signal server to stop
    _shutdown_event.set()
    
    # Wait for server thread to exit
    if _server_thread and _server_thread.is_alive():
        _server_thread.join(timeout=5.0)
    
    _is_running = False
    logger.info("Progress server stopped")
    return True

def open_progress_viewer():
    """Open the progress viewer in a web browser"""
    url = f"http://localhost:{HTTP_PORT}"
    logger.info(f"Opening progress viewer at {url}")
    
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        logger.info(f"Please manually open {url} in your browser")

def is_server_running():
    """Check if the progress server is running"""
    return _is_running

if __name__ == "__main__":
    # If run directly, start the server and keep it running
    logger.info("Starting progress monitoring server...")
    
    if start_progress_server():
        logger.info(f"Progress viewer available at http://localhost:{HTTP_PORT}")
        logger.info("Press Ctrl+C to stop the server")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping server...")
            stop_progress_server()
    else:
        logger.error("Failed to start server")
