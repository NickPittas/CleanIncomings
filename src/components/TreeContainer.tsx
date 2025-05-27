import React, { useState, useRef, useCallback } from 'react';
import { useAppStore } from '../store';
import IncomingTree from './IncomingTree';
import PreviewTree from './PreviewTree';

const TreeContainer: React.FC = () => {
  const { incomingTree, proposals } = useAppStore();
  const [leftWidth, setLeftWidth] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - rect.left) / rect.width) * 100;
    
    // Constrain between 20% and 80%
    const constrainedWidth = Math.min(Math.max(newLeftWidth, 20), 80);
    setLeftWidth(constrainedWidth);
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div className="tree-container" ref={containerRef}>
      <div 
        className="tree-panel" 
        style={{ width: `${leftWidth}%` }}
      >
        <div className="tree-header">
          <h4>Incoming Structure</h4>
          <p className="tree-help">Click folders to select all files inside</p>
        </div>
        <div className="tree-content scrollbar">
          {incomingTree ? (
            <IncomingTree tree={incomingTree} />
          ) : (
            <div className="empty-state">
              <p>Select a folder to begin</p>
            </div>
          )}
        </div>
      </div>
      
      <div 
        className={`tree-divider ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
      />
      
      <div className="tree-panel" style={{ width: `${100 - leftWidth}%` }}>
        <div className="tree-header">
          <h4>Preview Structure</h4>
        </div>
        <div className="tree-content scrollbar">
          {proposals.length > 0 ? (
            <PreviewTree proposals={proposals} />
          ) : (
            <div className="empty-state">
              <p>Scan a folder to see preview</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TreeContainer; 