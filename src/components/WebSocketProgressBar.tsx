import React, { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react';
import { useAppStore } from '../store';

interface ProgressData {
  batch_id: string;
  filesProcessed: number;
  totalFiles: number;
  progressPercentage: number;
  currentFile: string;
  status: string;
  timestamp: number;
  speed?: number; // Speed in MB/s
  operationType?: string; // 'copy' or 'move'
}

interface WebSocketProgressBarProps {
  className?: string;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

// ProgressBar context and provider for external control
interface ProgressBarContextType {
  show: () => void;
  hide: () => void;
  isVisible: boolean;
  hidden: boolean;
  isTriggerVisible: boolean;
  progressState: any;
  wsProgress: any;
  setWsProgress: React.Dispatch<React.SetStateAction<any>>;
}
const ProgressBarContext = createContext<ProgressBarContextType>({
  show: () => {},
  hide: () => {},
  isVisible: false,
  hidden: false,
  isTriggerVisible: false,
  progressState: {},
  wsProgress: null,
  setWsProgress: () => {},
});
export const useProgressBarTrigger = () => useContext(ProgressBarContext);

export const ProgressBarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { progressState } = useAppStore();
  const [wsProgress, setWsProgress] = useState<any>(null);
  const [isVisible, setIsVisible] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [lastActive, setLastActive] = useState<number | null>(null);

  // Track when progress is active or recently active
  useEffect(() => {
    if (progressState.isActive || wsProgress) {
      setLastActive(Date.now());
    }
  }, [progressState.isActive, wsProgress]);

  // Auto-show bar on new operation
  useEffect(() => {
    if (progressState.isActive) {
      setIsVisible(true);
      setHidden(false);
      console.log('[ProgressBarProvider] Auto-show on new operation');
    }
  }, [progressState.isActive]);

  // Hide with grace period
  const hide = () => {
    setIsVisible(false);
    setHidden(true);
    console.log('[ProgressBarProvider] Hide called');
  };
  const show = () => {
    setIsVisible(true);
    setHidden(false);
    console.log('[ProgressBarProvider] Show called');
  };

  // Grace period: trigger visible for 10s after last activity
  const isTriggerVisible = hidden && ((progressState.isActive || wsProgress) || (lastActive && Date.now() - lastActive < 10000));

  return (
    <ProgressBarContext.Provider value={{
      show,
      hide,
      isVisible,
      hidden,
      isTriggerVisible,
      progressState,
      wsProgress,
      setWsProgress,
    }}>
      {children}
      {/* Always mount the progress bar globally */}
      <WebSocketProgressBar />
    </ProgressBarContext.Provider>
  );
};

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
  
  // Function to format file names
  const getCurrentFileName = (filename: string) => {
    if (!filename) return '';
    const fileName = filename.split(/[\/\\]/).pop() || '';
    return fileName.length > 40 ? `...${fileName.slice(-37)}` : fileName;
  };
  
  // Function to format speed
  const formatSpeed = (speed?: number) => {
    if (!speed) return '';
    return speed < 1 ? `${(speed * 1000).toFixed(1)} KB/s` : `${speed.toFixed(1)} MB/s`;
  };

  // Use simple Unicode icons instead of react-icons
  const icons = {
    copy: '📋',
    move: '✂️',
    minimize: '_',
    close: '×',
    check: '✓',
    loading: '⟳',
    alert: '⚠️'
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
      const ws = new WebSocket(`ws://127.0.0.1:${port}`);
      
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
        
        // Register for the current batchId only
        const batchId = progressState.batchId || wsProgress?.batch_id || 'unknown';
        console.log(`🔄 Registering WebSocket client for updates: ${batchId}`);
        ws.send(JSON.stringify({
          type: 'register',
          batch_id: batchId,
          client_type: 'operation_progress'
        }));
        
        // Clean up interval on close
        ws.onclose = () => {
          clearInterval(heartbeatInterval);
        };
      };

      ws.onmessage = (event) => {
        // Log every message received
        console.log('[WS DEBUG] Message received:', event.data);
        try {
          // Enhanced debug logging for all incoming messages
          console.log(`📥 WebSocket raw message:`, event.data);
          
          // Try to parse the message as JSON
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (parseError) {
            // Handle the case where the message isn't valid JSON
            console.log('Received non-JSON message:', event.data);
            
            // Try to extract progress information from text message
            // Example format: "[WEBSOCKET] Sending progress update for batch 785d8264-2349-4868-87c3-e76629738a51: 1563/1563 (100.0%)"
            if (typeof event.data === 'string' && event.data.includes('progress update for batch')) {
              try {
                const parts = event.data.split(':');
                const batchInfo = parts[0].split('batch ')[1].trim();
                const progressParts = parts[1].trim().split(' ');
                const [current, total] = progressParts[0].split('/');
                const percentage = parseFloat(progressParts[1].replace('(', '').replace('%)', ''));
                
                data = {
                  type: 'progress',
                  batch_id: batchInfo,
                  filesProcessed: parseInt(current, 10),
                  totalFiles: parseInt(total, 10),
                  progressPercentage: percentage,
                  currentFile: '',
                  status: 'running'
                };
                console.log('Extracted progress data from text message:', data);
              } catch (extractError) {
                console.error('Failed to extract progress from text message:', extractError);
              }
            }
            
            // If we still don't have valid data, return
            if (!data) return;
          }
          
          console.log(`📥 WebSocket parsed data:`, data);
          
          // Accept progress updates for any batch ID initially, or match the current one if we have it
          if (data.type === 'progress' || 
              // Also handle messages without explicit type but with progress data
              (data.progressPercentage !== undefined || 
               (data.filesProcessed !== undefined && data.totalFiles !== undefined))) {
            
            // Log all progress updates during development to debug
            console.log(`📊 WebSocket progress update:`, data);
            
            // Update progress data immediately with defaults for missing fields
            const newProgress = {
              batch_id: data.batch_id || (wsProgress?.batch_id || 'unknown'),
              filesProcessed: typeof data.filesProcessed === 'number' ? data.filesProcessed : 
                             (typeof data.current === 'number' ? data.current : 0),
              totalFiles: typeof data.totalFiles === 'number' ? data.totalFiles : 
                         (typeof data.total === 'number' ? data.total : 0),
              progressPercentage: typeof data.progressPercentage === 'number' ? data.progressPercentage : 
                                  (typeof data.percentage === 'number' ? data.percentage : 
                                  (data.totalFiles > 0 ? (data.filesProcessed / data.totalFiles) * 100 : 
                                  (data.total > 0 ? (data.current / data.total) * 100 : 0))),
              currentFile: data.currentFile || data.fileName || '',
              status: data.status || 'running',
              timestamp: data.timestamp || Date.now(),
              speed: data.speed,
              operationType: data.operationType || 
                            (data.batch_id && data.batch_id.includes('-') ? data.batch_id.split('-')[0] : null)
            };
            
            // Always update the current progress
            console.log('🔄 Updating progress state:', newProgress);
            setWsProgress(newProgress);
            
            // Check if operation is completed or failed
            if (data.status === 'completed' || 
                (newProgress.progressPercentage >= 100 && newProgress.filesProcessed >= newProgress.totalFiles)) {
              console.log('✅ Operation completed successfully');
              setTimeout(() => finishProgress(), 1000);
            } else if (data.status === 'failed') {
              console.error('❌ Operation failed:', data.error);
            }
          } else if (data.type === 'pong') {
            // Just update connection status on pong
            setConnectionStatus('connected');
          } else {
            // Log other message types for debugging
            console.log(`📥 WebSocket message with unknown format:`, data);
          }
        } catch (err) {
          console.error('Error processing WebSocket message:', err, event.data);
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
            connectWebSocket(8765);
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
  }, [connectionStatus, wsProgress, progressState.batchId]);

  // Re-register for new batchId if it changes and WebSocket is open
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const batchId = progressState.batchId || wsProgress?.batch_id || 'unknown';
      console.log(`[WS] Re-registering for new batchId: ${batchId}`);
      wsRef.current.send(JSON.stringify({
        type: 'register',
        batch_id: batchId,
        client_type: 'operation_progress'
      }));
    }
  }, [progressState.batchId]);

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

  // Ensure cancel always works for the current batchId
  const handleCancel = async () => {
    const batchId = progressState.batchId || wsProgress?.batch_id;
    if (!batchId || isCancelling) return;
    setIsCancelling(true);
    try {
      console.log('🛑 Cancelling operation:', batchId);
      const response = await window.electronAPI.cancelOperation(batchId);
      console.log('🔍 Cancel response:', response);
      if (response && (response.success || response.message?.includes('cancelled'))) {
        setWsProgress((prev: ProgressData | null) => prev ? { ...prev, status: 'cancelled' } : null);
      } else {
        setIsCancelling(false);
      }
    } catch (error) {
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
    // Always try to connect when component mounts, regardless of progress state
    // This ensures we can receive updates even before a specific operation starts
    console.log('WebSocketProgressBar mounted or progress state changed:', { 
      isActive: progressState.isActive, 
      wsProgress: wsProgress?.batch_id || 'none' 
    });
    
    // Always attempt to connect to receive any available progress updates
    connectWebSocket(8765);

    // Set up a regular reconnect interval to ensure we maintain connection
    const reconnectInterval = setInterval(() => {
      if (connectionStatus !== 'connected') {
        console.log('Reconnection interval triggered - attempting to reconnect...');
        connectWebSocket(8765);
      }
    }, 10000); // Try reconnecting every 10 seconds if not connected

    return () => {
      clearInterval(reconnectInterval);
      disconnectWebSocket();
    };
  }, [progressState.isActive]);
  
  // Add debugging logging for state changes
  useEffect(() => {
    console.log('Progress state changed:', progressState);
  }, [progressState]);
  
  useEffect(() => {
    if (wsProgress) {
      console.log('WebSocket progress updated:', wsProgress);
    }
  }, [wsProgress]);

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
    if (displayData.status === 'running') return icons.loading;
    if (connectionStatus === 'connecting') return '⏳';
    if (connectionStatus === 'disconnected') return icons.alert;
    return '📊';
  };

  const getStatusText = () => {
    if (displayData.status === 'completed') return 'Completed';
    if (displayData.status === 'cancelled') return 'Cancelled';
    if (isCancelling) return 'Cancelling...';
    if (displayData.status === 'running') return 'Processing';
    if (connectionStatus === 'connecting') return 'Connecting...';
    if (connectionStatus === 'disconnected') return 'Disconnected';
  };

  const canCancel = displayData.status === 'running' && !isCancelling && displayData.batch_id !== 'unknown';

  if (isMinimized) {
    return (
      <div className="progress-overlay minimized" onClick={onToggleMinimize}>
        <div className="progress-header">
          <span className="progress-operation">{getStatusText()}</span>
          <span className="progress-percentage">{displayData.progressPercentage.toFixed(1)}%</span>
        </div>
        <div className="progress-bar" style={{ 
          height: '8px', 
          background: '#333',
          borderRadius: '4px',
          overflow: 'hidden',
          margin: '4px 0',
          position: 'relative'
        }}>
          <div 
            className="progress-fill"
            style={{ 
              width: `${Math.min(displayData.progressPercentage, 100)}%`,
              height: '100%',
              background: '#007ACC',
              transition: 'width 0.3s ease',
              borderRadius: '4px'
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`progress-container ${className}`} style={{ position: 'relative' }}>
      {/* Header with Status and Controls */}
      <div className="progress-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
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
        <div className="progress-controls" style={{ display: 'flex', gap: '8px' }}>
          {onToggleMinimize && (
            <button 
              className="control-button minimize"
              onClick={onToggleMinimize}
              aria-label="Minimize progress bar"
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: '#222',
                color: '#fff',
                border: 'none',
                fontSize: 18,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
                cursor: 'pointer',
                transition: 'background 0.2s',
                marginRight: 2
              }}
              onMouseOver={e => (e.currentTarget.style.background = '#444')}
              onMouseOut={e => (e.currentTarget.style.background = '#222')}
            >
              {/* Modern minimize icon */}
              <span style={{ fontWeight: 700, fontSize: 18, lineHeight: 1 }}>–</span>
            </button>
          )}
          <button 
            className="control-button close"
            onClick={handleClose}
            aria-label="Close progress bar"
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: '#222',
              color: '#fff',
              border: 'none',
              fontSize: 18,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 1px 4px rgba(0,0,0,0.12)',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#c00')}
            onMouseOut={e => (e.currentTarget.style.background = '#222')}
          >
            {/* Modern close icon */}
            <span style={{ fontWeight: 700, fontSize: 18, lineHeight: 1 }}>×</span>
          </button>
        </div>
      </div>

      {/* Progress Bar with Cancel Button overlayed at the end */}
      <div className="progress-bar" style={{ 
        height: '12px', 
        background: '#333',
        borderRadius: '6px',
        overflow: 'hidden',
        margin: '5px 0',
        position: 'relative'
      }}>
        <div 
          className={`progress-fill ${displayData.status === 'completed' ? 'completed' : ''}`}
          style={{ 
            width: `${Math.min(displayData.progressPercentage, 100)}%`,
            height: '100%',
            background: '#007ACC',
            transition: 'width 0.3s ease',
            borderRadius: '6px',
            position: 'relative',
            textAlign: 'center',
            color: '#fff',
            fontSize: '10px',
            lineHeight: '12px'
          }}
        >
          {displayData.progressPercentage.toFixed(1)}%
        </div>
        {/* Small Cancel button at the end of the bar */}
        {canCancel && (
          <button
            className="cancel-button"
            onClick={handleCancel}
            disabled={isCancelling}
            aria-label="Cancel operation"
            style={{
              position: 'absolute',
              right: 4,
              top: '50%',
              transform: 'translateY(-50%)',
              height: 22,
              minWidth: 60,
              padding: '0 10px',
              fontSize: 13,
              background: '#c00',
              color: '#fff',
              border: 'none',
              borderRadius: 11,
              boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
              cursor: 'pointer',
              zIndex: 2,
              transition: 'background 0.2s',
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#a00')}
            onMouseOut={e => (e.currentTarget.style.background = '#c00')}
          >
            {isCancelling ? 'Cancelling...' : 'Cancel'}
          </button>
        )}
      </div>

      {/* File Information - Current File box styled */}
      <div className="progress-details" style={{ display: 'flex', alignItems: 'center', marginTop: 6 }}>
        <div className="file-info" style={{
          background: '#181a1b',
          color: '#fff',
          borderRadius: 6,
          padding: '6px 18px',
          minWidth: 320,
          minHeight: 28,
          fontSize: 15,
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          marginRight: 18,
          boxShadow: '0 1px 4px rgba(0,0,0,0.10)'
        }}>
          {displayData.currentFile && (
            <>
              <span className="file-label" style={{ color: '#aaa', fontWeight: 400, marginRight: 8 }}>Current File:</span>
              <span className="file-name" style={{ color: '#fff', fontWeight: 600 }}>{getCurrentFileName(displayData.currentFile)}</span>
            </>
          )}
        </div>
        <div className="file-counter" style={{ color: '#fff', fontSize: 14, marginRight: 12 }}>
          {displayData.filesProcessed} / {displayData.totalFiles} files
        </div>
        {/* Speed indicator if available */}
        {displayData.speed !== undefined && (
          <div className="file-speed" style={{ color: '#fff', fontSize: 13, marginRight: 12 }}>
            {formatSpeed(displayData.speed)}
          </div>
        )}
      </div>
    </div>
  );
};

export const ProgressBarTrigger: React.FC = () => {
  const { show, isTriggerVisible } = useProgressBarTrigger();
  if (!isTriggerVisible) return null;
  return (
    <button
      style={{
        marginLeft: 8,
        background: '#007ACC',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        padding: '6px 14px',
        fontWeight: 600,
        fontSize: 15,
        cursor: 'pointer',
        boxShadow: '0 1px 4px rgba(0,0,0,0.10)'
      }}
      onClick={show}
      aria-label="Show Progress Bar"
    >
      Show Progress
    </button>
  );
}; 