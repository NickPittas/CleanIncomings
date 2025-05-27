import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store';

interface ProgressData {
  batch_id: string;
  filesProcessed: number;
  totalFiles: number;
  progressPercentage: number;
  currentFile: string;
  status: string;
  timestamp: number;
}

interface WebSocketProgressBarProps {
  className?: string;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

export const WebSocketProgressBar: React.FC<WebSocketProgressBarProps> = ({ 
  className = '', 
  isMinimized = false, 
  onToggleMinimize 
}) => {
  const { progressState, finishProgress } = useAppStore();
  const [wsProgress, setWsProgress] = useState<ProgressData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [isCancelling, setIsCancelling] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const [websocketPort, setWebsocketPort] = useState<number>(8765);

  // Function to get the WebSocket port
  const getWebSocketPort = async () => {
    try {
      if (window.electronAPI && 'getWebSocketPort' in window.electronAPI) {
        const getPort = window.electronAPI.getWebSocketPort as () => Promise<number | null>;
        const port = await getPort();
        if (port && port > 0) {
          // Only log port discovery if it's different from current port
          if (port !== websocketPort) {
            console.log(`📡 Discovered WebSocket port from API: ${port}`);
          }
          setWebsocketPort(port);
          return port;
        }
      }
      return 8765; // Default fallback
    } catch (err) {
      console.error('Failed to get WebSocket port:', err);
      return 8765; // Default fallback
    }
  };

  // Function to connect to WebSocket with connection management
  const connectWebSocket = useCallback((port: number) => {
    // Avoid connecting if we already have an active connection
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        return; // Already connected and open
      } else if (wsRef.current.readyState === WebSocket.CONNECTING) {
        return; // Already in the process of connecting
      }
      // If we have a closing or closed connection, we'll clean it up below
    }

    try {
      // Only update status if we're not already connecting or connected
      if (connectionStatus !== 'connecting' && connectionStatus !== 'connected') {
        setConnectionStatus('connecting');
      }
      
      // Create WebSocket
      console.log(`Attempting WebSocket connection for operation progress on port ${port}`);
      const ws = new WebSocket(`ws://localhost:${port}`);
      
      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.log('WebSocket connection timeout, closing connection attempt');
          try {
            ws.close();
          } catch (e) {
            // Ignore errors during close
          }
        }
      }, 5000); // 5 second timeout
      
      ws.onopen = () => {
        // Only log on first successful connection
        if (connectionStatus !== 'connected') {
          console.log(`WebSocket connected for operation progress updates on port ${port}`);
        }
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        
        // Clear the connection timeout
        clearTimeout(connectionTimeout);
        
        // Start heartbeat when connected - use longer interval to reduce traffic
        const heartbeatInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            try {
              ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
            } catch (e) {
              // Ignore errors during ping
            }
          }
        }, 15000); // Even less frequent heartbeat (15 seconds) to reduce traffic
        
        // Send an initial message to register this client for the specific batch
        if (wsProgress?.batch_id) {
          try {
            ws.send(JSON.stringify({ 
              type: 'register', 
              batch_id: wsProgress.batch_id,
              client_type: 'operation_progress'
            }));
          } catch (err) {
            console.error('Failed to register for batch updates:', err);
          }
        }
        
        // Clean up interval on close
        ws.onclose = () => {
          clearInterval(heartbeatInterval);
        };
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'progress' && data.batch_id === wsProgress?.batch_id) {
            // Only log significant updates to reduce console spam
            if (data.status === 'completed' || data.status === 'failed' || 
                data.filesProcessed % 100 === 0) {
              console.log(`Progress: ${data.filesProcessed}/${data.totalFiles} files (${data.progressPercentage.toFixed(1)}%)`);
            }
            
            // Update progress data immediately
            const newProgress = {
              batch_id: data.batch_id,
              filesProcessed: data.filesProcessed || 0,
              totalFiles: data.totalFiles || 0,
              progressPercentage: data.progressPercentage || 0,
              currentFile: data.currentFile || '',
              status: data.status || 'running',
              timestamp: data.timestamp || Date.now()
            };
            
            setWsProgress(newProgress);
            
            // Check if operation is completed or failed - handle with a small delay to ensure UI updates first
            if (data.status === 'completed') {
              console.log('Operation completed successfully');
              // Use setTimeout to ensure the UI updates before calling finishProgress
              setTimeout(() => finishProgress(), 100);
            } else if (data.status === 'failed') {
              console.error('Operation failed:', data.error);
            }
          }
          // Don't log pong messages
        } catch (err) {
          // Silence parsing errors to reduce console spam
        }
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Attempt to reconnect if not a clean close and we haven't exceeded max attempts
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts.current), 10000); // Exponential backoff, max 10s
          console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            // Try to get the latest port before reconnecting
            getWebSocketPort().then(port => {
              connectWebSocket(port);
            });
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

      wsRef.current = ws;
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  }, [connectionStatus, wsProgress]);

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  };

  const handleCancel = async () => {
    if (!wsProgress?.batch_id || isCancelling) return;
    
    setIsCancelling(true);
    
    try {
      console.log('🛑 Cancelling operation:', wsProgress.batch_id);
      
      // Call the backend to cancel the operation
      const response = await window.electronAPI.cancelOperation(wsProgress.batch_id);
      console.log('🔍 Cancel response:', response);
      
      if (response && (response.success || response.message?.includes('cancelled'))) {
        console.log('✅ Operation cancelled successfully');
        // Force update the status immediately
        setWsProgress(prev => prev ? { ...prev, status: 'cancelled' } : null);
      } else {
        console.error('❌ Failed to cancel operation:', response);
        setIsCancelling(false);
      }
    } catch (error) {
      console.error('❌ Error cancelling operation:', error);
      setIsCancelling(false);
    }
  };

  const handleClose = () => {
    console.log('🗙 Manually closing progress bar');
    finishProgress();
    setWsProgress(null);
    setIsCancelling(false);
    disconnectWebSocket();
  };

  // Connect when component mounts or when progress becomes active
  useEffect(() => {
    if (progressState.isActive) {
      // Get the WebSocket port and then connect
      getWebSocketPort().then(port => {
        connectWebSocket(port);
      });
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [progressState.isActive]);

  // Show progress bar if either store state is active OR we have WebSocket data
  const shouldShow = progressState.isActive || wsProgress !== null;
  
  if (!shouldShow) {
    return null;
  }

  // Use WebSocket data if available, otherwise fall back to store state
  const displayData = wsProgress || {
    batch_id: progressState.batchId || 'unknown',
    filesProcessed: progressState.current || 0,
    totalFiles: progressState.total || 0,
    progressPercentage: progressState.percentage || 0,
    currentFile: progressState.currentFile || '',
    status: progressState.isActive ? 'running' : 'starting',
    timestamp: Date.now()
  };

  // Debug logging
  console.log('🔍 WebSocketProgressBar render:', {
    shouldShow,
    progressStateActive: progressState.isActive,
    wsProgressExists: wsProgress !== null,
    displayData,
    progressState
  });

  const getStatusIcon = () => {
    if (displayData.status === 'completed') return '✅';
    if (displayData.status === 'cancelled') return '🛑';
    if (displayData.status === 'running') return '🔄';
    if (connectionStatus === 'connecting') return '⏳';
    if (connectionStatus === 'disconnected') return '⚠️';
    return '📊';
  };

  const getStatusText = () => {
    if (displayData.status === 'completed') return 'Completed';
    if (displayData.status === 'cancelled') return 'Cancelled';
    if (isCancelling) return 'Cancelling...';
    if (displayData.status === 'running') return 'Processing';
    if (connectionStatus === 'connecting') return 'Connecting...';
    if (connectionStatus === 'disconnected') return 'Disconnected';
    return 'Starting...';
  };

  const getCurrentFileName = () => {
    if (!displayData.currentFile) return '';
    const fileName = displayData.currentFile.split(/[/\\]/).pop() || '';
    return fileName.length > 40 ? `...${fileName.slice(-37)}` : fileName;
  };

  const canCancel = displayData.status === 'running' && !isCancelling && displayData.batch_id !== 'unknown';

  if (isMinimized) {
    return (
      <div className="progress-overlay minimized" onClick={onToggleMinimize}>
        <div className="progress-header">
          <span className="progress-operation">{getStatusText()}</span>
          <span className="progress-percentage">{displayData.progressPercentage.toFixed(1)}%</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${Math.min(displayData.progressPercentage, 100)}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`progress-container ${className}`}>
      {/* Header with Status and Controls */}
      <div className="progress-header">
        <div className="progress-info">
          <span className="progress-operation">
            {getStatusIcon()} {getStatusText()}
          </span>
          <span className="progress-stats">
            Batch: {displayData.batch_id.slice(0, 8)}...
          </span>
          {connectionStatus === 'disconnected' && progressState.isActive && (
            <span className="progress-stats offline">(Offline Mode)</span>
          )}
        </div>
        
        <div className="progress-controls">
          {/* Minimize Button */}
          {onToggleMinimize && (
            <button
              onClick={onToggleMinimize}
              className="button small secondary"
              title="Minimize progress bar"
            >
              −
            </button>
          )}
          
          {/* Cancel Button */}
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={isCancelling}
              className="button small danger"
              title="Cancel operation"
            >
              {isCancelling ? 'Cancelling...' : 'Cancel'}
            </button>
          )}
          
          {/* Close Button */}
          <button
            onClick={handleClose}
            className="button small secondary"
            title="Close progress bar"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Visual Progress Bar Container */}
      <div className="progress-visual-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${Math.min(displayData.progressPercentage, 100)}%` }}
          />
        </div>
        
        <div className="progress-percentage">
          {displayData.progressPercentage.toFixed(1)}%
        </div>
      </div>
      
      {/* Progress Details */}
      <div className="progress-details">
        <div className="progress-stats">
          {displayData.filesProcessed} of {displayData.totalFiles} files processed
        </div>
        
        {displayData.currentFile && (
          <div className="progress-current-file">
            <span className="progress-file-label">Currently Processing:</span>
            <span className="progress-file-name">
              {getCurrentFileName()}
            </span>
          </div>
        )}
      </div>

      {/* Connection Status */}
      {connectionStatus !== 'connected' && progressState.isActive && wsProgress === null && (
        <div className="progress-connection-status">
          ⚡ {connectionStatus === 'connecting' 
            ? 'Establishing real-time connection...' 
            : 'Using fallback mode - progress may be delayed'
          }
        </div>
      )}
    </div>
  );
}; 