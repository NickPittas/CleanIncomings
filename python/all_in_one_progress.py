"""
All-in-one file copy with progress monitoring.
This script:
1. Starts an HTTP server and WebSocket server
2. Creates test files
3. Performs a copy operation
4. Shows real-time progress in the browser

Just run this script and everything will be set up automatically.
"""
import os
import sys
import time
import json
import shutil
import random
import asyncio
import threading
import webbrowser
import uuid
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websockets

# Fixed ports that won't conflict
HTTP_PORT = 7800

# Global state
clients = set()
script_dir = Path(__file__).parent
source_dir = script_dir / "_test_source"
dest_dir = script_dir / "_test_dest"
html_file = """<!DOCTYPE html>
<html>
<head>
    <title>File Copy Progress</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f8fa;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        h1 {
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
    </style>
</head>
<body>
    <div class="card">
        <h1>File Copy Progress</h1>
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
        <h2>Activity Log</h2>
        <div id="log" class="log"></div>
    </div>
    
    <script>
        let ws = null;
        let reconnectAttempts = 0;
        
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
        
        function connect() {
            log('Connecting to WebSocket server...');
            
            const status = document.getElementById('status');
            status.textContent = 'Connecting...';
            status.className = 'status connecting';
            
            ws = new WebSocket('ws://localhost:PORT_PLACEHOLDER');
            
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
                        // Update progress bar
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
""".replace("PORT_PLACEHOLDER", str(HTTP_PORT))

def log(message):
    """Print message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def generate_test_file(path, size_mb):
    """Generate a test file with specified size"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'wb') as f:
        for _ in range(size_mb):
            f.write(os.urandom(1024 * 1024))  # 1MB chunk
    
    return os.path.getsize(path)

def create_test_files(source_dir, num_files=5, min_size_mb=1, max_size_mb=10):
    """Create test files for copying"""
    files = []
    total_size = 0
    
    log(f"Creating {num_files} test files in {source_dir}")
    os.makedirs(source_dir, exist_ok=True)
    
    for i in range(num_files):
        size_mb = random.randint(min_size_mb, max_size_mb)
        filename = f"test_file_{i+1}_{size_mb}MB.dat"
        file_path = os.path.join(source_dir, filename)
        
        log(f"Generating {filename} ({size_mb} MB)")
        file_size = generate_test_file(file_path, size_mb)
        files.append((file_path, file_size))
        total_size += file_size
    
    log(f"Created {num_files} files with total size: {total_size / (1024*1024):.2f} MB")
    return files

class ProgressHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves our HTML file"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_file.encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """Customize logging"""
        log(f"HTTP: {format % args}")

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    log(f"WebSocket client connected")
    clients.add(websocket)
    
    try:
        async for message in websocket:
            # Just echo back for testing
            await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        log(f"WebSocket client disconnected")
    finally:
        clients.remove(websocket)

async def broadcast_progress(data):
    """Send progress updates to all clients"""
    if not clients:
        return
    
    message = json.dumps(data)
    disconnected = set()
    
    for client in clients:
        try:
            await client.send(message)
        except:
            disconnected.add(client)
    
    # Remove disconnected clients
    for client in disconnected:
        clients.remove(client)

async def start_servers():
    """Start the HTTP and WebSocket servers"""
    # Start HTTP server
    http_server = HTTPServer(('', HTTP_PORT), ProgressHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    log(f"HTTP server started on port {HTTP_PORT}")
    
    # Start WebSocket server
    ws_server = await websockets.serve(websocket_handler, 'localhost', HTTP_PORT)
    log(f"WebSocket server started on port {HTTP_PORT}")
    
    return http_server, ws_server

async def copy_with_progress(files, dest_dir, batch_id="copy-test"):
    """Copy files with progress updates"""
    total_files = len(files)
    total_size = sum(size for _, size in files)
    processed_size = 0
    files_processed = 0
    start_time = time.time()
    
    log(f"Starting copy operation: {total_files} files, {total_size / (1024*1024):.2f} MB")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Initial progress update
    await broadcast_progress({
        'type': 'progress',
        'batch_id': batch_id,
        'filesProcessed': 0,
        'totalFiles': total_files,
        'progressPercentage': 0,
        'currentFile': "",
        'status': "starting"
    })
    
    for src_path, file_size in files:
        filename = os.path.basename(src_path)
        dst_path = os.path.join(dest_dir, filename)
        
        # Simulate multiple progress updates per file
        file_size_mb = file_size / (1024 * 1024)
        update_steps = max(5, min(20, int(file_size_mb * 2)))  # More updates for larger files
        
        for step in range(update_steps):
            # Calculate progress within the current file
            step_progress = (step + 1) / update_steps
            current_progress = files_processed + step_progress / update_steps
            percent_done = (current_progress / total_files) * 100
            
            # Simulate partial file copy
            current_name = f"{filename} ({int(step_progress * 100)}%)"
            
            # Calculate speed
            elapsed = time.time() - start_time
            current_speed = (processed_size + file_size * step_progress / update_steps) / elapsed if elapsed > 0 else 0
            
            # Send progress update
            await broadcast_progress({
                'type': 'progress',
                'batch_id': batch_id,
                'filesProcessed': current_progress,
                'totalFiles': total_files,
                'progressPercentage': percent_done,
                'currentFile': current_name,
                'speed': current_speed / (1024 * 1024),  # MB/s
                'status': "running"
            })
            
            # Delay to simulate copy progress
            await asyncio.sleep(0.2)
        
        # Actually copy the file
        try:
            log(f"Copying {filename} ({file_size / (1024*1024):.2f} MB)")
            shutil.copy2(src_path, dst_path)
            
            # Update progress
            files_processed += 1
            processed_size += file_size
            
            # Calculate speed
            elapsed = time.time() - start_time
            speed = processed_size / elapsed if elapsed > 0 else 0
            
            # Send complete file progress
            await broadcast_progress({
                'type': 'progress',
                'batch_id': batch_id,
                'filesProcessed': files_processed,
                'totalFiles': total_files,
                'progressPercentage': (files_processed / total_files) * 100,
                'currentFile': filename,
                'speed': speed / (1024 * 1024),  # MB/s
                'status': "running"
            })
            
            log(f"Progress: {files_processed}/{total_files} files - "
                f"Speed: {speed / (1024*1024):.2f} MB/s")
            
        except Exception as e:
            log(f"Error copying {src_path}: {e}")
    
    # Final progress update
    elapsed = time.time() - start_time
    speed = total_size / elapsed if elapsed > 0 else 0
    
    await broadcast_progress({
        'type': 'progress',
        'batch_id': batch_id,
        'filesProcessed': total_files,
        'totalFiles': total_files,
        'progressPercentage': 100,
        'currentFile': "",
        'speed': speed / (1024 * 1024),  # MB/s
        'status': "completed"
    })
    
    log(f"Copy completed in {elapsed:.2f} seconds - "
        f"Average speed: {speed / (1024*1024):.2f} MB/s")

async def open_browser():
    """Open browser after a short delay"""
    await asyncio.sleep(1)
    url = f"http://localhost:{HTTP_PORT}"
    log(f"Opening browser at {url}")
    webbrowser.open(url)

async def main():
    """Main function"""
    try:
        # Clean up old test directories
        for dir_path in [source_dir, dest_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        # Start servers
        http_server, ws_server = await start_servers()
        
        # Open browser
        asyncio.create_task(open_browser())
        
        # Create test files
        files = create_test_files(
            source_dir,
            num_files=10,  # Number of files
            min_size_mb=1,  # Minimum size per file
            max_size_mb=5   # Maximum size per file
        )
        
        # Perform copy with progress
        await copy_with_progress(files, dest_dir)
        
        # Keep server running
        log("Copy completed. Keeping servers running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        log("Interrupted by user")
    except Exception as e:
        log(f"Error: {e}")
    finally:
        log("Shutting down")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
