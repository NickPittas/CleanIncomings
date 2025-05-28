"""
Robust WebSocket server for progress updates.
This module provides a standalone WebSocket server for real-time progress updates
that can be started independently from the main application.
"""
import os
import sys
import json
import time
import asyncio
import threading
import websockets
from typing import Dict, Any, Set, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s',
                   datefmt='%H:%M:%S')
logger = logging.getLogger("websocket")

# Global server instance and control variables
_server = None
_server_lock = threading.Lock()
_server_thread = None
_shutdown_event = threading.Event()

# Store port number in a file for clients to discover
_port_file_path = os.path.join(os.path.dirname(__file__), "_progress", "websocket_port.txt")

class ProgressServer:
    """WebSocket server for progress updates that doesn't block the main application"""
    
    def __init__(self, host='localhost', port=8765):
        """Initialize the WebSocket server"""
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.progress_data: Dict[str, Dict[str, Any]] = {}
        self.server = None
        self.running = False
        
        # Create progress directory if it doesn't exist
        progress_dir = os.path.dirname(_port_file_path)
        os.makedirs(progress_dir, exist_ok=True)
        
        # Write the port number to a file
        with open(_port_file_path, "w") as f:
            f.write(str(self.port))
        
        logger.info(f"WebSocket server configured on {self.host}:{self.port}")
    
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send all current progress data to the new client
        try:
            for batch_id, data in self.progress_data.items():
                await websocket.send(json.dumps({
                    'type': 'progress',
                    'batch_id': batch_id,
                    **data
                }))
        except Exception as e:
            logger.error(f"Error sending initial data to client: {e}")
    
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_progress(self, batch_id: str, progress_data: Dict[str, Any]):
        """Broadcast progress update to all connected clients"""
        if not self.clients:
            return
            
        message = json.dumps({
            'type': 'progress',
            'batch_id': batch_id,
            **progress_data
        })
        
        # Store progress data
        self.progress_data[batch_id] = progress_data
        
        # Send to all clients
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
    
    async def handle_client(self, websocket, path=None):
        """Handle a client WebSocket connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle ping messages for connection health checks
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': time.time()
                        }))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Client connection closed normally")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client, 
                self.host, 
                self.port
            )
            self.running = True
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            
            # Keep the server running until shutdown
            await _shutdown_event.wait()
            logger.info("Server shutdown requested")
            
            # Close all client connections
            for client in list(self.clients):
                await client.close(1001, "Server shutting down")
            
            # Close the server
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            self.running = False
    
    def update_progress(self, batch_id: str, progress_data: Dict[str, Any]):
        """Update progress for a batch (non-async version)"""
        if not self.running:
            return False
            
        asyncio.run_coroutine_threadsafe(
            self.broadcast_progress(batch_id, progress_data),
            asyncio.get_event_loop()
        )
        return True

def get_server() -> Optional[ProgressServer]:
    """Get the global WebSocket server instance"""
    return _server

def get_websocket_port() -> Optional[int]:
    """Get the WebSocket server port from the port file"""
    try:
        if os.path.exists(_port_file_path):
            with open(_port_file_path, "r") as f:
                return int(f.read().strip())
    except Exception as e:
        logger.error(f"Error reading WebSocket port file: {e}")
    return None

def _run_server_in_thread(host='localhost', port=8765):
    """Run the WebSocket server in a separate thread"""
    global _server
    
    logger.info(f"Starting WebSocket server thread on {host}:{port}")
    
    # Create the server instance
    _server = ProgressServer(host, port)
    
    # Create and run the asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the server
        loop.run_until_complete(_server.start_server())
    except Exception as e:
        logger.error(f"WebSocket server thread error: {e}")
    finally:
        # Clean up
        loop.close()
        logger.info("WebSocket server thread stopped")

def start_server(host='localhost', port=8765) -> bool:
    """Start the WebSocket server in a separate thread"""
    global _server, _server_thread, _shutdown_event
    
    with _server_lock:
        if _server is not None and _server.running:
            logger.info("WebSocket server is already running")
            return True
        
        # Reset shutdown event
        _shutdown_event.clear()
        
        # Start server in a separate thread
        _server_thread = threading.Thread(
            target=_run_server_in_thread,
            args=(host, port),
            daemon=True  # Make thread daemon so it doesn't block application exit
        )
        _server_thread.start()
        
        # Wait a moment for the server to start
        time.sleep(0.5)
        
        # Check if server started successfully
        if _server is not None and _server.running:
            logger.info("WebSocket server started successfully")
            return True
        else:
            logger.error("Failed to start WebSocket server")
            return False

def stop_server():
    """Stop the WebSocket server"""
    global _server, _server_thread, _shutdown_event
    
    with _server_lock:
        if _server is None or not _server.running:
            logger.info("WebSocket server is not running")
            return
        
        # Signal server to shut down
        _shutdown_event.set()
        
        # Wait for server thread to exit (with timeout)
        if _server_thread is not None and _server_thread.is_alive():
            _server_thread.join(timeout=5.0)
            if _server_thread.is_alive():
                logger.warning("WebSocket server thread did not exit cleanly")
        
        _server_thread = None
        _server = None
        logger.info("WebSocket server stopped")

def send_progress_update(
    batch_id: str,
    files_processed: int,
    total_files: int,
    current_file: str = "",
    status: str = "running"
) -> bool:
    """Send a progress update to all connected clients"""
    server = get_server()
    if server is None:
        logger.warning("No WebSocket server available for progress update")
        return False

    # Calculate percentage - prevent division by zero and ensure valid percentage
    percentage = 0
    if total_files > 0:
        percentage = min(100.0, (files_processed / total_files) * 100)
    
    # Prepare progress data
    progress_data = {
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
            progress_data['operationType'] = operation_type

    # Update progress
    return server.update_progress(batch_id, progress_data)

# Simple test function
def test_server():
    """Test the WebSocket server with some sample progress updates"""
    print("Starting WebSocket server test...")
    
    # Start server
    if not start_server():
        print("Failed to start WebSocket server")
        return
    
    try:
        # Simulate some progress updates
        batch_id = f"test-{int(time.time())}"
        total_files = 100
        
        for i in range(total_files + 1):
            # Send progress update
            send_progress_update(
                batch_id=batch_id,
                files_processed=i,
                total_files=total_files,
                current_file=f"file_{i}.txt" if i < total_files else "",
                status="running" if i < total_files else "completed"
            )
            
            # Sleep to simulate processing time
            time.sleep(0.1)
            
            # Print progress
            if i % 10 == 0:
                print(f"Progress: {i}/{total_files} ({i/total_files*100:.1f}%)")
        
        print("Test completed successfully")
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        # Stop server
        stop_server()

if __name__ == "__main__":
    # Run test if script is executed directly
    test_server()
