import { WebSocketServer } from 'ws';
import * as fs from 'fs';
import * as path from 'path';
import { app } from 'electron';

// WebSocket server instance
let wss: WebSocketServer | null = null;
let serverPort = 8765; // Default port
const clients = new Set<any>();
const progressData: Record<string, any> = {};

// Directory for progress data and port info
const getProgressDir = () => {
  const pythonDir = path.join(app.getAppPath(), 'python');
  const progressDir = path.join(pythonDir, '_progress');
  
  // Create directory if it doesn't exist
  if (!fs.existsSync(progressDir)) {
    try {
      fs.mkdirSync(progressDir, { recursive: true });
    } catch (e) {
      console.error('[WEBSOCKET] Failed to create progress directory:', e);
    }
  }
  
  return progressDir;
};

// Write the WebSocket port to a file for discovery
const writePortToFile = (port: number) => {
  try {
    const progressDir = getProgressDir();
    const portFile = path.join(progressDir, 'websocket_port.txt');
    fs.writeFileSync(portFile, port.toString());
    console.log(`[WEBSOCKET] Port ${port} written to ${portFile}`);
  } catch (e) {
    console.error('[WEBSOCKET] Failed to write port to file:', e);
  }
};

// Start the WebSocket server
export const startWebSocketServer = () => {
  if (wss) {
    console.log('[WEBSOCKET] Server already running on port', serverPort);
    return { port: serverPort, running: true };
  }

  // Try ports starting from default
  const tryPort = (port: number, maxAttempts = 100): { port: number, running: boolean } => {
    try {
      wss = new WebSocketServer({ port });
      serverPort = port;
      
      console.log(`[WEBSOCKET] Server started on port ${port}`);
      writePortToFile(port);
      
      // Handle connections
      wss.on('connection', (ws) => {
        console.log('[WEBSOCKET] Client connected');
        clients.add(ws);
        
        // Send existing progress data to new client
        Object.entries(progressData).forEach(([batchId, data]) => {
          ws.send(JSON.stringify({
            type: 'progress',
            batch_id: batchId,
            ...data
          }));
        });
        
        // Handle messages from client
        ws.on('message', (message) => {
          try {
            const data = JSON.parse(message.toString());
            console.log('[WEBSOCKET] Received message:', data);
            
            // Handle ping/pong for connection health checks
            if (data.type === 'ping') {
              ws.send(JSON.stringify({
                type: 'pong',
                timestamp: Date.now()
              }));
            }
            
            // Handle client registration for specific batch_id
            if (data.type === 'register') {
              const batchId = data.batch_id;
              const clientType = data.client_type || 'unknown';
              
              if (batchId) {
                // Store client registration info
                (ws as any).batch_id = batchId;
                (ws as any).client_type = clientType;
                console.log(`[WEBSOCKET] Client registered for batch_id: ${batchId}, type: ${clientType}`);
                
                // Send acknowledgment
                ws.send(JSON.stringify({
                  type: 'register_ack',
                  batch_id: batchId,
                  status: 'success',
                  timestamp: Date.now()
                }));
                
                // Send latest progress data if available for this batch
                if (progressData[batchId]) {
                  ws.send(JSON.stringify({
                    type: 'progress',
                    batch_id: batchId,
                    ...progressData[batchId]
                  }));
                }
              }
            }
          } catch (e) {
            console.error('[WEBSOCKET] Error processing message:', e);
          }
        });
        
        // Handle disconnection
        ws.on('close', () => {
          console.log('[WEBSOCKET] Client disconnected');
          clients.delete(ws);
        });
      });
      
      return { port, running: true };
    } catch (e) {
      console.log(`[WEBSOCKET] Port ${port} is in use, trying next port...`);
      if (maxAttempts > 0) {
        return tryPort(port + 1, maxAttempts - 1);
      } else {
        console.error('[WEBSOCKET] Failed to find an available port');
        return { port: -1, running: false };
      }
    }
  };
  
  return tryPort(serverPort);
};

// Stop the WebSocket server
export const stopWebSocketServer = () => {
  if (wss) {
    wss.close();
    wss = null;
    clients.clear();
    console.log('[WEBSOCKET] Server stopped');
    return true;
  }
  return false;
};

// Get WebSocket server port
export const getWebSocketPort = (): number => {
  if (wss) {
    return serverPort;
  }
  
  // Try to read from port file
  try {
    const progressDir = getProgressDir();
    const portFile = path.join(progressDir, 'websocket_port.txt');
    if (fs.existsSync(portFile)) {
      const port = parseInt(fs.readFileSync(portFile, 'utf8').trim(), 10);
      if (!isNaN(port)) {
        return port;
      }
    }
  } catch (e) {
    console.error('[WEBSOCKET] Failed to read port from file:', e);
  }
  
  return serverPort; // Return default
};

// Send progress update to all connected clients
export const sendProgressUpdate = (
  batchId: string,
  filesProcessed: number,
  totalFiles: number,
  currentFile: string = "",
  status: string = "running"
) => {
  if (!wss) {
    return false;
  }

  // Calculate percentage with safeguards
  let percentage = 0;
  if (totalFiles > 0) {
    percentage = Math.min(100.0, (filesProcessed / totalFiles) * 100);
  }
  
  // Force 100% for completed status
  if (status === 'completed') {
    percentage = 100.0;
  }

  // Format current file to be more user-friendly
  if (currentFile && currentFile.length > 60) {
    const parts = currentFile.split(path.sep);
    if (parts.length > 3) {
      currentFile = path.join(parts[0], '...', parts[parts.length - 1]);
    }
  }

  // Create progress data
  const progressInfo = {
    filesProcessed,
    totalFiles,
    progressPercentage: Math.round(percentage * 10) / 10, // Round to 1 decimal place
    currentFile,
    status,
    timestamp: Date.now()
  };

  // Add operation type field for scan progress identification
  if (batchId.startsWith('scan-')) {
    (progressInfo as any).operationType = 'scan';
  }
  
  // Add batch_id type hint for clients
  if (batchId.includes('-')) {
    const operationType = batchId.split('-')[0];
    if (['copy', 'move', 'scan', 'organize'].includes(operationType)) {
      (progressInfo as any).operationType = operationType;
    }
  }

  // Store progress data
  progressData[batchId] = progressInfo;

  // Create message
  const message = JSON.stringify({
    type: 'progress',
    batch_id: batchId,
    ...progressInfo
  });

  // Don't send if no clients
  if (clients.size === 0) {
    return true; // Still return success since we stored the progress data
  }

  // Send to all clients with targeting
  let sentCount = 0;
  const disconnected = new Set();

  for (const client of clients) {
    try {
      // Check if client is registered for a specific batch_id
      const clientBatchId = (client as any).batch_id;
      const clientType = (client as any).client_type;
      
      // Determine if this client should receive this batch update
      let shouldSend = false;
      
      // Case 1: Client has no batch filter - send everything
      if (!clientBatchId) {
        shouldSend = true;
      }
      // Case 2: Client is registered for this specific batch
      else if (clientBatchId === batchId) {
        shouldSend = true;
      }
      // Case 3: Client is registered for "initializing" but we have real data
      else if (clientBatchId === 'initializing' && clientType === 'scan_progress') {
        shouldSend = true;
        // Update the client's batch_id to this real batch_id
        (client as any).batch_id = batchId;
        console.log(`[WEBSOCKET] Updated client from 'initializing' to batch_id: ${batchId}`);
      }
      
      if (shouldSend) {
        client.send(message);
        sentCount++;
      }
    } catch (e) {
      console.error('[WEBSOCKET] Error sending to client:', e);
      disconnected.add(client);
    }
  }

  // Remove disconnected clients
  for (const client of disconnected) {
    clients.delete(client);
  }

  // Log broadcast summary
  if (sentCount > 0) {
    console.log(`[WEBSOCKET] Sent ${status} progress for batch ${batchId}: ${filesProcessed}/${totalFiles} to ${sentCount} clients`);
  }

  return true;
};

// Get server status
export const getServerStatus = () => {
  return {
    running: wss !== null,
    clients: clients.size,
    port: serverPort,
    batches: Object.keys(progressData).length
  };
};

// Clear progress data for a batch
export const clearProgressData = (batchId: string) => {
  if (progressData[batchId]) {
    delete progressData[batchId];
    return true;
  }
  return false;
};
