import React, { useEffect, useRef } from 'react';
import { IconChevronDown, IconTrash, IconDownload } from '@tabler/icons-react';
import { useAppStore } from '../store';
import { LogEntry } from '../types';

const LogWindow: React.FC = () => {
  const { 
    logs, 
    progressState, 
    isLogWindowOpen, 
    setLogWindowOpen, 
    clearLogs 
  } = useAppStore();
  
  // Debug logging
  console.log('LogWindow render - isLogWindowOpen:', isLogWindowOpen, 'logs.length:', logs.length);
  
  const logContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = React.useState(true);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const getLogIcon = (level: LogEntry['level']): string => {
    switch (level) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  };

  const getLogColor = (level: LogEntry['level']): string => {
    switch (level) {
      case 'success': return '#90ee90';
      case 'warning': return '#ffd700';
      case 'error': return '#ff6b6b';
      default: return '#87ceeb';
    }
  };

  const exportLogs = () => {
    const logText = logs.map(log => 
      `[${formatTime(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}${log.details ? ` - ${log.details}` : ''}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vfx-normalizer-logs-${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleScroll = () => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setAutoScroll(isAtBottom);
    }
  };

  if (!isLogWindowOpen) {
    return null;
  }

  return (
    <div className="log-window">
      <div className="log-header">
        <div className="log-title">
          <span>Activity Log</span>
          {logs.length > 0 && (
            <span className="log-count">{logs.length} entries</span>
          )}
        </div>
        
        <div className="log-actions">
          <button 
            className="log-action-button"
            onClick={exportLogs}
            title="Export logs"
            disabled={logs.length === 0}
          >
            <IconDownload size={14} />
          </button>
          <button 
            className="log-action-button"
            onClick={clearLogs}
            title="Clear logs"
            disabled={logs.length === 0}
          >
            <IconTrash size={14} />
          </button>
          <button 
            className="log-action-button"
            onClick={() => setLogWindowOpen(false)}
            title="Hide log window"
          >
            <IconChevronDown size={16} />
          </button>
        </div>
      </div>



      {/* Log Entries */}
      <div 
        className="log-content"
        ref={logContainerRef}
        onScroll={handleScroll}
      >
        {logs.length === 0 ? (
          <div className="log-empty">
            <p>No activity yet. Start by scanning a folder to see logs here.</p>
          </div>
        ) : (
          <div className="log-entries">
            {logs.map((log) => (
              <div 
                key={log.id} 
                className={`log-entry log-${log.level}`}
              >
                <div className="log-entry-header">
                  <span className="log-icon">{getLogIcon(log.level)}</span>
                  <span className="log-time">{formatTime(log.timestamp)}</span>
                  <span 
                    className="log-level"
                    style={{ color: getLogColor(log.level) }}
                  >
                    {log.level.toUpperCase()}
                  </span>
                </div>
                
                <div className="log-message">{log.message}</div>
                
                {log.details && (
                  <div className="log-details">{log.details}</div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {!autoScroll && (
          <button 
            className="scroll-to-bottom"
            onClick={() => {
              setAutoScroll(true);
              if (logContainerRef.current) {
                logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
              }
            }}
          >
            Scroll to bottom
          </button>
        )}
      </div>
    </div>
  );
};

export default LogWindow; 