import React, { useState } from 'react';
import { IconFolder, IconFolderOpen, IconFile, IconChevronRight, IconChevronDown } from '@tabler/icons-react';
import { FileSystemNode } from '../types';
import { useAppStore } from '../store';

interface IncomingTreeProps {
  tree: FileSystemNode | null;
}

interface TreeNodeProps {
  node: FileSystemNode;
  level: number;
  onFolderSelect: (folderPath: string) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({ node, level, onFolderSelect }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // Auto-expand first 2 levels

  const hasChildren = node.children && node.children.length > 0;
  const isFolder = node.type === 'folder';

  const handleToggle = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleFolderClick = () => {
    if (isFolder) {
      onFolderSelect(node.path);
    }
  };

  const indent = level * 16;

  return (
    <div className="tree-node">
      <div 
        className={`tree-node-content ${isFolder ? 'folder' : 'file'}`}
        style={{ paddingLeft: `${indent}px` }}
        onClick={isFolder ? handleFolderClick : undefined}
      >
        {hasChildren && (
          <button 
            className="tree-toggle"
            onClick={handleToggle}
          >
            {isExpanded ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}
          </button>
        )}
        
        {!hasChildren && <div className="tree-spacer" />}
        
        <div className="tree-icon">
          {isFolder ? (
            isExpanded ? <IconFolderOpen size={14} /> : <IconFolder size={14} />
          ) : (
            <IconFile size={14} />
          )}
        </div>
        
        <span className="tree-label" title={node.path}>
          {node.name}
        </span>
        
        {node.type === 'sequence' && node.frame_count && (
          <span className="sequence-info">
            ({node.frame_count} frames)
          </span>
        )}
      </div>
      
      {hasChildren && isExpanded && (
        <div className="tree-children">
          {node.children!.map((child, index) => (
            <TreeNode
              key={`${child.path}-${index}`}
              node={child}
              level={level + 1}
              onFolderSelect={onFolderSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const IncomingTree: React.FC<IncomingTreeProps> = ({ tree }) => {
  const { proposals, setSelectedProposalIds, addLog } = useAppStore();

  const handleFolderSelect = (folderPath: string) => {
    if (!proposals || proposals.length === 0) {
      addLog('warning', 'No proposals available', 'Scan a folder first to see proposals.');
      return;
    }

    // Find all proposals that belong to this folder or its subfolders
    const selectedIds = proposals
      .filter(proposal => {
        // Check if the proposal's source path starts with the selected folder path
        return proposal.sourcePath.startsWith(folderPath);
      })
      .map(proposal => proposal.id);

    if (selectedIds.length === 0) {
      addLog('info', 'No files in folder', `No mappings found for folder: ${folderPath}`);
      return;
    }

    setSelectedProposalIds(selectedIds);
    addLog('success', 'Folder selected', `Selected ${selectedIds.length} files/sequences from: ${folderPath}`);
  };

  if (!tree) {
    return (
      <div className="empty-state">
        <IconFolder size={48} />
        <p>Select a folder to begin</p>
      </div>
    );
  }

  return (
    <div className="tree-content">
      <TreeNode
        node={tree}
        level={0}
        onFolderSelect={handleFolderSelect}
      />
    </div>
  );
};

export default IncomingTree; 