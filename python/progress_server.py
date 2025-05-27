import asyncio
import websockets
import json
import threading
import time
from typing import Dict, Set
import logging
import traceback
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for singleton management
_server_lock = threading.Lock()
_instance = None
_server_port = None
_server_thread = None
_shutdown_event = threading.Event()

# Create progress directory if it doesn't exist
progress_dir = os.path.join(os.path.dirname(__file__), "_progress")
os.makedirs(progress_dir, exist_ok=True)

class ProgressServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.progress_data: Dict[str, dict] = {}
        self.server = None
        self.running = False
        self.connection_errors = 0
        self.max_connection_errors = 5
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send current progress data to new client
            for batch_id, data in self.progress_data.items():
                await websocket.send(json.dumps({
                    'type': 'progress',
                    'batch_id': batch_id,
                    **data
                }))
        except Exception as e:
            logger.error(f"Error sending initial data to client: {e}")
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_progress(self, batch_id: str, progress_data: dict):
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
        
        # Send to all clients - with better targeting for registered clients
        disconnected = set()
        sent_count = 0
        
        for client in self.clients:
            try:
                # Check if client is registered for a specific batch_id
                client_batch_id = getattr(client, 'batch_id', None)
                client_type = getattr(client, 'client_type', None)
                
                # If client has registered for this specific batch_id or doesn't have a batch_id filter
                if client_batch_id is None or client_batch_id == batch_id:
                    await client.send(message)
                    sent_count += 1
                # Special case for scan progress - only send to scan clients if it's their batch
                elif client_type == 'scan_progress' and client_batch_id != batch_id:
                    # Skip sending to scan progress clients for other batches
                    pass
                else:
                    # For other client types, send anyway as before
                    await client.send(message)
                    sent_count += 1
                    
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
                logger.debug(f"Client connection closed during broadcast")
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
            
        # Log broadcast summary occasionally to reduce spam
        if len(self.progress_data) % 10 == 0:
            logger.debug(f"Broadcast progress for batch {batch_id} to {sent_count} clients (filtered from {len(self.clients)} total)")
    
    async def handle_client(self, websocket, path=None):
        """Handle WebSocket client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                # Handle incoming messages if needed
                try:
                    data = json.loads(message)
                    logger.info(f"Received message: {data}")
                    
                    # Handle ping/pong for connection health checks
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': time.time()
                        }))
                    
                    # Handle client registration for specific batch_id
                    elif data.get('type') == 'register':
                        batch_id = data.get('batch_id')
                        client_type = data.get('client_type', 'unknown')
                        
                        if batch_id:
                            # Store client registration info
                            websocket.batch_id = batch_id
                            websocket.client_type = client_type
                            logger.info(f"Client registered for batch_id: {batch_id}, type: {client_type}")
                            
                            # Send acknowledgment
                            await websocket.send(json.dumps({
                                'type': 'register_ack',
                                'batch_id': batch_id,
                                'status': 'success',
                                'timestamp': time.time()
                            }))
                            
                            # Send latest progress data if available for this batch
                            if batch_id in self.progress_data:
                                await websocket.send(json.dumps({
                                    'type': 'progress',
                                    'batch_id': batch_id,
                                    **self.progress_data[batch_id]
                                }))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Client connection closed normally")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            logger.debug(traceback.format_exc())
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Reset connection error count on restart
        self.connection_errors = 0
        
        # Try starting with increasing port numbers until one works
        max_port = self.port + 100  # Don't try forever
        current_port = self.port
        
        while current_port < max_port:
            try:
                # Store the event loop for cross-thread communication
                self._loop = asyncio.get_running_loop()
                
                self.server = await websockets.serve(
                    self.handle_client,
                    self.host,
                    current_port
                )
                
                self.port = current_port  # Update to actual port used
                self.running = True
                logger.info(f"WebSocket server started successfully on port {self.port}")
                
                # Write port to file so frontend can find it
                self._write_port_to_file(self.port)
                
                # Reset error count on successful start
                self.connection_errors = 0
                return
                
            except OSError as e:
                # Port might be in use
                self.connection_errors += 1
                logger.warning(f"Failed to start WebSocket server on port {current_port}: {e}")
                current_port += 1
            except Exception as e:
                logger.error(f"Unexpected error starting WebSocket server: {e}")
                logger.debug(traceback.format_exc())
                break
        
        # If we get here, we failed to start on any port
        self.running = False
        logger.error(f"Failed to start WebSocket server after trying ports {self.port}-{current_port}")
    
    def _write_port_to_file(self, port):
        """Write port to a file that frontend can read"""
        try:
            port_file = os.path.join(progress_dir, "websocket_port.txt")
            with open(port_file, "w") as f:
                f.write(str(port))
            logger.info(f"WebSocket port {port} written to {port_file}")
        except Exception as e:
            logger.error(f"Failed to write port to file: {e}")
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("WebSocket server stopped")
    
    def update_progress(self, batch_id: str, progress_data: dict):
        """Update progress (thread-safe)"""
        # Always store progress data
        self.progress_data[batch_id] = progress_data
        
        if self.running and self.clients:
            # Try to schedule broadcast if we have an event loop
            try:
                # Try to get the event loop from the server thread
                if hasattr(self, '_loop') and self._loop and not self._loop.is_closed():
                    # Schedule the broadcast in the server's event loop
                    future = asyncio.run_coroutine_threadsafe(
                        self.broadcast_progress(batch_id, progress_data), 
                        self._loop
                    )
                    # Don't wait for completion to avoid blocking
                else:
                    logger.debug("No event loop available for immediate WebSocket broadcast")
            except Exception as e:
                logger.warning(f"Failed to schedule WebSocket broadcast: {e}")
        else:
            logger.debug(f"WebSocket server not running or no clients connected")

def get_progress_server():
    """Get or create the global progress server instance (thread-safe singleton)"""
    global _instance
    with _server_lock:
        if _instance is None:
            _instance = ProgressServer()
        return _instance

def get_websocket_port():
    """Get the port that the WebSocket server is running on"""
    global _server_port
    
    # Try to read from port file first
    try:
        port_file = os.path.join(progress_dir, "websocket_port.txt")
        if os.path.exists(port_file):
            with open(port_file, "r") as f:
                port = int(f.read().strip())
                return port
    except Exception:
        pass
        
    # Fall back to stored port if available
    if _server_port:
        return _server_port
        
    # Default fallback
    return 8765

def start_progress_server():
    """Start the progress server in a background thread if not already running"""
    global _server_thread, _server_port, _shutdown_event
    
    # Don't start if already running
    if _server_thread and _server_thread.is_alive():
        logger.info("WebSocket server already running")
        return True
    
    # Reset shutdown event
    _shutdown_event.clear()
    
    def run_server():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            server = get_progress_server()
            loop.run_until_complete(server.start_server())
            
            # Store the port globally
            global _server_port
            _server_port = server.port
            
            try:
                # Run until shutdown event is set
                while not _shutdown_event.is_set():
                    loop.run_until_complete(asyncio.sleep(0.1))
            except KeyboardInterrupt:
                pass
            except Exception as e:
                logger.error(f"Error in WebSocket server loop: {e}")
                logger.debug(traceback.format_exc())
            finally:
                loop.run_until_complete(server.stop_server())
                loop.close()
        except Exception as e:
            logger.error(f"Failed to start WebSocket server thread: {e}")
            logger.debug(traceback.format_exc())
    
    with _server_lock:
        if _server_thread and _server_thread.is_alive():
            logger.info("WebSocket server already running")
            return True
            
        _server_thread = threading.Thread(target=run_server, daemon=True)
        _server_thread.start()
        
        # Give server time to start
        time.sleep(0.5)
        
        # Check if server is running
        server = get_progress_server()
        logger.info(f"Progress server started in background thread on port {server.port}")
        return server.running

def stop_progress_server():
    """Stop the progress server if it's running"""
    global _server_thread, _shutdown_event
    
    if _server_thread and _server_thread.is_alive():
        _shutdown_event.set()
        _server_thread.join(timeout=2.0)
        logger.info("WebSocket server stopped")
        return True
    return False

def send_progress_update(batch_id: str, files_processed: int, total_files: int, 
                        current_file: str = "", status: str = "running"):
    """Send a progress update to all connected clients"""
    try:
        server = get_progress_server()
        if server is None:
            logger.warning("No WebSocket server available for progress update")
            return False

        # Calculate percentage - prevent division by zero and ensure valid percentage
        percentage = 0
        if total_files > 0:
            percentage = min(100.0, (files_processed / total_files) * 100)
        
        # Special case: if status is 'completed', force 100%
        if status == 'completed':
            percentage = 100.0

        # Format current file to be more user-friendly
        if current_file:
            # Shorten path for display if it's too long
            if len(current_file) > 60:
                current_file_parts = current_file.split(os.sep)
                if len(current_file_parts) > 3:
                    current_file = os.path.join(
                        current_file_parts[0], 
                        "...", 
                        current_file_parts[-1]
                    )

        # Create progress data
        progress_data = {
            "filesProcessed": files_processed,
            "totalFiles": total_files,
            "progressPercentage": round(percentage, 1),
            "currentFile": current_file,
            "status": status,
            "timestamp": time.time()
        }

        # Add operation type field for scan progress identification
        if batch_id.startswith('scan-'):
            progress_data['operationType'] = 'scan'
        
        # Add batch_id type hint for clients
        if '-' in batch_id:
            operation_type = batch_id.split('-')[0]
            if operation_type in ['copy', 'move', 'scan', 'organize']:
                progress_data['operationType'] = operation_type

        # Update progress
        server.update_progress(batch_id, progress_data)
        return True
    except Exception as e:
        logger.error(f"Error sending progress update: {e}")
        logger.debug(traceback.format_exc())
        return False

def check_server_health():
    """Check if the WebSocket server is running properly"""
    server = get_progress_server()
    return {
        'running': server.running,
        'clients': len(server.clients),
        'port': server.port,
        'batches': len(server.progress_data),
    }

if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "get_port":
            # Get current WebSocket port and print it to stdout
            port = get_websocket_port()
            print(port)
            sys.exit(0)
            
        elif command == "start":
            # Start the WebSocket server
            start_progress_server()
            
            # Print server health after startup
            health = check_server_health()
            print(json.dumps(health))
            sys.exit(0)
            
        elif command == "stop":
            # Stop the WebSocket server
            stopped = stop_progress_server()
            print(json.dumps({"stopped": stopped}))
            sys.exit(0)
            
        elif command == "status":
            # Get server health status
            health = check_server_health()
            print(json.dumps(health))
            sys.exit(0)
    else:
        # Test the server
        start_progress_server()
        
        # Print server health after startup
        health = check_server_health()
        print(f"Server health: {health}")
        
        # Simulate progress updates
        batch_id = "test-batch-123"
        
        for i in range(11):
            send_progress_update(
                batch_id=batch_id,
                files_processed=i,
                total_files=10,
                current_file=f"test_file_{i}.png",
                status="running" if i < 10 else "completed"
            )
            time.sleep(1)
            
        # Stop the server
        stop_progress_server() 