/**
 * Progress Monitor Integration
 * 
 * This module integrates the Python WebSocket progress monitoring system
 * with the Electron/React frontend by providing bridge functions and utilities.
 */

// Disable TypeScript checking for this file since we're in a Google Drive environment
// without access to proper type definitions
// @ts-nocheck

// WebSocket server is always 127.0.0.1:8765, HTTP config is 127.0.0.1:7800

// Default ports for the WebSocket and HTTP servers
const DEFAULT_WS_PORT = 8765;
const DEFAULT_HTTP_PORT = 7800;

/**
 * Check if the progress monitoring server is running
 */
export async function isProgressServerRunning(): Promise<boolean> {
  try {
    // Try to fetch config from the HTTP server
    const response = await fetch(`http://127.0.0.1:${DEFAULT_HTTP_PORT}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(2000) // 2 second timeout
    });

    if (response.ok) {
      const data = await response.json();
      return data.status === 'running';
    }
    return false;
  } catch (error) {
    console.error('Error checking progress server:', error);
    return false;
  }
}

/**
 * Start the progress monitoring server
 */
export async function startProgressServer(): Promise<boolean> {
  try {
    // Use IPC to ask the main process to start the progress server
    if (electronAPI && electronAPI.invoke) {
      const result = await electronAPI.invoke('start-progress-server');
      return result.success;
    }
    console.warn('IPC bridge not available');
    return false;
  } catch (error) {
    console.error('Failed to start progress server:', error);
    return false;
  }
}

/**
 * Open the progress viewer in a browser window
 */
export async function openProgressViewer(): Promise<void> {
  try {
    // Use IPC to ask the main process to open the progress viewer
    if (electronAPI && electronAPI.invoke) {
      await electronAPI.invoke('open-progress-viewer');
    } else {
      // Fallback: try to open in browser directly
      window.open(`http://127.0.0.1:${DEFAULT_HTTP_PORT}`, '_blank');
    }
  } catch (error) {
    console.error('Failed to open progress viewer:', error);
    // Fallback: try to open in browser directly
    window.open(`http://127.0.0.1:${DEFAULT_HTTP_PORT}`, '_blank');
  }
}

/**
 * Add additional functions to the electronAPI global
 */
export function setupProgressMonitoring(): void {
  // Add to window.electronAPI if it exists
  if (window.electronAPI) {
    // Type assertion to avoid TypeScript errors
    const api = window.electronAPI as any;
    
    // Add our progress monitoring functions
    api.isProgressServerRunning = isProgressServerRunning;
    api.startProgressServer = startProgressServer;
    api.openProgressViewer = openProgressViewer;
    
    console.log('Progress monitoring integration initialized');
  } else {
    console.warn('window.electronAPI not available, progress monitoring integration disabled');
  }
}

// Export a default function to initialize the integration
export default function initProgressMonitoring(): void {
  setupProgressMonitoring();
}
