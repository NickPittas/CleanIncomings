# WebSocket Troubleshooting Guide

## Common Issues and Solutions

### 1. WebSocket Connection Refused (Error: net::ERR_CONNECTION_REFUSED)

**Problem:** The ScanProgressModal shows "Using polling mode (no real-time updates)" and console shows connection errors.

**Possible Causes and Solutions:**

- **WebSocket Server Not Running:**
  - Run `python/progress_server.py start` manually to start the server
  - Check if port 8765 (or other port used) is already in use by another application
  - Check for error messages in the console/terminal

- **Port Conflicts:**
  - The WebSocket server automatically tries alternate ports if the default (8765) is taken
  - Check `python/_progress/websocket_port.txt` to see which port is actually being used
  - Make sure the frontend is connecting to the correct port

- **Firewall Issues:**
  - Check if your firewall is blocking WebSocket connections on the port
  - Add an exception for the application in your firewall settings

### 2. Windows PATH Issues

**Problem:** Cannot start the application with npm/Node.js commands.

**Solution:**
- Run `start-app.bat` which attempts to set up the PATH correctly
- Install Node.js if not already installed:
  ```
  winget install --id OpenJS.NodeJS
  ```
- Make sure npm is in your PATH:
  - Add `C:\Program Files\nodejs` to your PATH (or wherever Node.js is installed)
  - Restart your terminal after changing PATH

### 3. Python Module Issues

**Problem:** Errors related to WebSocket modules not found.

**Solution:**
- Install required Python packages:
  ```
  pip install websockets
  ```

### 4. Testing WebSocket Connectivity

To test if the WebSocket server is running correctly:

1. Start the server: `python/progress_server.py start`
2. Check the port: `python/progress_server.py get_port`
3. Verify status: `python/progress_server.py status`

### 5. Manual WebSocket Connection Test

You can use the included `websocket_test.html` to manually test WebSocket connectivity:

1. Open the file in a browser
2. Enter the WebSocket server port (from step 2 above)
3. Click "Connect" and check if the connection succeeds

## Error Messages and Their Meaning

- `WebSocket connection failed: Error in connection establishment: net::ERR_CONNECTION_REFUSED` - The server is not running or not accessible
- `WebSocket error: Event {isTrusted: true, type: 'error', ...}` - Generic WebSocket error, often related to connection issues
- `Port already in use (error 10048)` - Another application is using the port, the server will try to find an alternative

## Contact Support

If you continue to experience issues after trying these solutions, please report the problem with:

1. Your exact error message
2. Operating system and version
3. Console logs showing the error
4. Steps to reproduce the issue 