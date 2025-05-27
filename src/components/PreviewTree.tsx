import React, { useState, useEffect } from 'react';
import { IconFolder, IconFolderOpen, IconFile, IconChevronRight, IconChevronDown, IconCheck, IconX, IconEdit, IconAlertTriangle } from '@tabler/icons-react';
import { MappingProposal } from '../types';
import { useAppStore } from '../store';

interface PreviewTreeProps {
  proposals: MappingProposal[];
}

interface PreviewNodeProps {
  proposal: MappingProposal;
  level: number;
  checked: boolean;
  onCheck: (id: string, checked: boolean) => void;
  onSelect?: (proposal: MappingProposal) => void;
  onEdit?: (proposal: MappingProposal) => void;
}

const PreviewNode: React.FC<PreviewNodeProps> = ({ proposal, level, checked, onCheck, onSelect, onEdit }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = proposal.node.children && proposal.node.children.length > 0;

  const handleToggle = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleSelect = () => {
    onSelect?.(proposal);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(proposal);
  };

  const handleCheck = (e: React.ChangeEvent<HTMLInputElement>) => {
    onCheck(proposal.id, e.target.checked);
  };

  const getStatusIcon = (status: MappingProposal['status']) => {
    switch (status) {
      case 'auto':
        return <IconCheck size={14} className="status-auto" />;
      case 'override':
        return <IconEdit size={14} className="status-override" />;
      case 'unmapped':
        return <IconX size={14} className="status-unmapped" />;
      default:
        return <IconAlertTriangle size={14} className="status-error" />;
    }
  };

  const getStatusClass = (status: MappingProposal['status']) => {
    return `mapping-status-${status}`;
  };

  const getFileTypeIcon = (node: MappingProposal['node']) => {
    if (node.type === 'folder') {
      return isExpanded ? <IconFolderOpen size={16} /> : <IconFolder size={16} />;
    }
    return <IconFile size={16} />;
  };

  const getFileTypeClass = (extension?: string) => {
    if (!extension) return '';
    const ext = extension.toLowerCase();
    if (['.exr', '.dpx', '.tiff', '.tif', '.hdr'].includes(ext)) return 'file-type-image';
    if (['.mov', '.mp4', '.avi', '.mkv', '.r3d', '.braw'].includes(ext)) return 'file-type-video';
    if (['.nk', '.hip', '.ma', '.mb', '.blend', '.c4d', '.aep'].includes(ext)) return 'file-type-project';
    if (['.abc', '.bgeo', '.vdb', '.ass', '.usd'].includes(ext)) return 'file-type-cache';
    return 'file-type-other';
  };

  const formatPath = (path: string) => {
    // Show relative path from VFX root
    const parts = path.split('/');
    return parts.slice(-3).join('/'); // Show last 3 parts
  };

  return (
    <div className="preview-node">
      <div 
        className={`preview-node-content ${getStatusClass(proposal.status)} ${getFileTypeClass(proposal.node.extension)}`}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
        onClick={handleSelect}
      >
        <input
          type="checkbox"
          checked={checked}
          onChange={handleCheck}
          style={{ marginRight: 8 }}
          onClick={e => e.stopPropagation()}
        />
        <div className="preview-node-toggle" onClick={handleToggle}>
          {hasChildren ? (
            isExpanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />
          ) : (
            <span style={{ width: 14, display: 'inline-block' }} />
          )}
        </div>
        
        <div className="preview-node-status">
          {getStatusIcon(proposal.status)}
        </div>
        
        <div className="preview-node-icon">
          {getFileTypeIcon(proposal.node)}
        </div>
        
        <div className="preview-node-info">
          <div className="preview-node-name">{proposal.node.name}</div>
          <div className="preview-node-path">{formatPath(proposal.targetPath)}</div>
          {(proposal.shot || proposal.task || proposal.version) && (
            <div className="preview-node-metadata">
              {proposal.shot && <span className="metadata-shot">Shot: {proposal.shot}</span>}
              {proposal.task && <span className="metadata-task">Task: {proposal.task}</span>}
              {proposal.version && <span className="metadata-version">v{proposal.version}</span>}
              {proposal.resolution && <span className="metadata-resolution">{proposal.resolution}</span>}
            </div>
          )}
        </div>
        
        <div className="preview-node-actions">
          <button 
            className="action-button edit"
            onClick={handleEdit}
            title="Edit mapping"
          >
            <IconEdit size={12} />
          </button>
        </div>
      </div>
      
      {hasChildren && isExpanded && (
        <div className="preview-node-children">
          <div className="child-placeholder">
            <small>Child items will be shown when hierarchical mapping is implemented</small>
          </div>
        </div>
      )}
    </div>
  );
};

const PreviewTree: React.FC<PreviewTreeProps> = ({ proposals }) => {
  const [selectedProposal, setSelectedProposal] = useState<MappingProposal | null>(null);
  const [activeFilter, setActiveFilter] = useState<MappingProposal['status'] | 'all'>('all');
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProposal, setEditingProposal] = useState<MappingProposal | null>(null);
  const [showBatchEdit, setShowBatchEdit] = useState(false);
  const [batchAsset, setBatchAsset] = useState('');
  const [batchStage, setBatchStage] = useState('');
  const {
    setSelectedProposal: setGlobalSelectedProposal,
    updateProposal,
    batchUpdateProposals,
    selectedProposalIds,
    setSelectedProposalIds,
    selectAllProposals,
    selectNoneProposals
  } = useAppStore();

  // For dropdowns
  const [assetOptions, setAssetOptions] = useState<string[]>([]);
  const [stageOptions, setStageOptions] = useState<string[]>([]);

  // Add state for customAsset and customStage
  const [customAsset, setCustomAsset] = useState('');
  const [customStage, setCustomStage] = useState('');

  useEffect(() => {
    // Load assetPatterns and stagePatterns from backend/config
    const loadPatterns = async () => {
      if (window.electronAPI && window.electronAPI.loadPatternConfig) {
        const result = await window.electronAPI.loadPatternConfig();
        if (result && result.success && result.config) {
          setAssetOptions(Array.isArray(result.config.assetPatterns) ? result.config.assetPatterns : []);
          setStageOptions(Array.isArray(result.config.stagePatterns) ? result.config.stagePatterns : []);
        } else {
          setAssetOptions([]);
          setStageOptions([]);
        }
      } else {
        setAssetOptions([]);
        setStageOptions([]);
      }
    };
    loadPatterns();
  }, []);

  const handleProposalSelect = (proposal: MappingProposal) => {
    setSelectedProposal(proposal);
    setGlobalSelectedProposal(proposal);
  };

  const handleProposalEdit = (proposal: MappingProposal) => {
    setEditingProposal(proposal);
    setShowEditModal(true);
  };

  const handleSaveEdit = () => {
    if (editingProposal) {
      updateProposal(editingProposal.id, {
        ...editingProposal,
        status: 'override'
      });
      setShowEditModal(false);
      setEditingProposal(null);
    }
  };

  const handleCheck = (id: string, checked: boolean) => {
    setSelectedProposalIds(
      checked ? [...selectedProposalIds, id] : selectedProposalIds.filter(x => x !== id)
    );
  };

  const handleSelectAll = () => selectAllProposals();
  const handleSelectNone = () => selectNoneProposals();

  const handleBatchEdit = () => {
    setShowBatchEdit(true);
    setBatchAsset('');
    setBatchStage('');
  };

  const handleApplyBatchEdit = async () => {
    await batchUpdateProposals(selectedProposalIds, batchAsset || customAsset, batchStage || customStage);
    setShowBatchEdit(false);
    setSelectedProposalIds([]);
  };

  const getStatusCounts = () => {
    const counts = {
      auto: 0,
      override: 0,
      unmapped: 0,
      total: proposals.length
    };
    
    proposals.forEach(proposal => {
      counts[proposal.status]++;
    });
    
    return counts;
  };

  const statusCounts = getStatusCounts();

  const filterProposalsByStatus = (status: MappingProposal['status'] | 'all') => {
    if (status === 'all') return proposals;
    return proposals.filter(p => p.status === status);
  };

  const filteredProposals = filterProposalsByStatus(activeFilter);

  const renderEditModal = () => {
    if (!showEditModal || !editingProposal) return null;

    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h3 className="modal-title">Edit Mapping</h3>
            <button className="close-button" onClick={() => setShowEditModal(false)}>
              <IconX size={20} />
            </button>
          </div>
          
          <div className="modal-content">
            <div className="form-group">
              <label>Source Path</label>
              <input
                type="text"
                value={editingProposal.sourcePath}
                disabled
              />
            </div>
            
            <div className="form-group">
              <label>Target Path</label>
              <input
                type="text"
                value={editingProposal.targetPath}
                onChange={(e) => setEditingProposal({
                  ...editingProposal,
                  targetPath: e.target.value
                })}
              />
            </div>
            
            <div className="form-group">
              <label>Shot</label>
              <input
                type="text"
                value={editingProposal.shot || ''}
                onChange={(e) => setEditingProposal({
                  ...editingProposal,
                  shot: e.target.value
                })}
              />
            </div>
            
            <div className="form-group">
              <label>Task</label>
              <input
                type="text"
                value={editingProposal.task || ''}
                onChange={(e) => setEditingProposal({
                  ...editingProposal,
                  task: e.target.value
                })}
              />
            </div>
            
            <div className="form-group">
              <label>Version</label>
              <input
                type="text"
                value={editingProposal.version || ''}
                onChange={(e) => setEditingProposal({
                  ...editingProposal,
                  version: e.target.value
                })}
              />
            </div>
            
            <div className="form-actions">
              <button className="button" onClick={handleSaveEdit}>
                Save Changes
              </button>
              <button className="button secondary" onClick={() => setShowEditModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderBatchEditModal = () => {
    if (!showBatchEdit) return null;
    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h3 className="modal-title">Batch Edit Asset/Stage</h3>
            <button className="close-button" onClick={() => setShowBatchEdit(false)}>
              <IconX size={20} />
            </button>
          </div>
          
          <div className="modal-content">
            <div className="form-group">
              <label>Asset</label>
              <select value={batchAsset} onChange={e => {
                if (e.target.value === '__custom__') {
                  setBatchAsset('');
                } else {
                  setBatchAsset(e.target.value);
                  setCustomAsset('');
                }
              }}>
                <option value="">(No change)</option>
                {assetOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
                <option value="__custom__">Custom...</option>
              </select>
              {batchAsset === '' && (
                <input type="text" placeholder="Custom asset" value={customAsset} onChange={e => setCustomAsset(e.target.value)} />
              )}
            </div>
            
            <div className="form-group">
              <label>Stage</label>
              <select value={batchStage} onChange={e => {
                if (e.target.value === '__custom__') {
                  setBatchStage('');
                } else {
                  setBatchStage(e.target.value);
                  setCustomStage('');
                }
              }}>
                <option value="">(No change)</option>
                {stageOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
                <option value="__custom__">Custom...</option>
              </select>
              {batchStage === '' && (
                <input type="text" placeholder="Custom stage" value={customStage} onChange={e => setCustomStage(e.target.value)} />
              )}
            </div>
            
            <div className="form-actions">
              <button className="button" onClick={handleApplyBatchEdit} disabled={selectedProposalIds.length === 0}>
                Apply to Selected
              </button>
              <button className="button secondary" onClick={() => setShowBatchEdit(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="preview-tree">
      <div className="tree-header">
        <h4>Preview Structure</h4>
        <div className="tree-stats">
          <span className="stat-total">{statusCounts.total} items</span>
          <span className="stat-auto">{statusCounts.auto} auto</span>
          <span className="stat-override">{statusCounts.override} manual</span>
          <span className="stat-unmapped">{statusCounts.unmapped} unmapped</span>
        </div>
      </div>
      
      <div className="tree-filters">
        <button 
          className={`filter-button ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All ({statusCounts.total})
        </button>
        <button 
          className={`filter-button ${activeFilter === 'auto' ? 'active' : ''}`}
          onClick={() => setActiveFilter('auto')}
        >
          Auto ({statusCounts.auto})
        </button>
        <button 
          className={`filter-button ${activeFilter === 'override' ? 'active' : ''}`}
          onClick={() => setActiveFilter('override')}
        >
          Manual ({statusCounts.override})
        </button>
        <button 
          className={`filter-button ${activeFilter === 'unmapped' ? 'active' : ''}`}
          onClick={() => setActiveFilter('unmapped')}
        >
          Unmapped ({statusCounts.unmapped})
        </button>
        <button className="button small" style={{ marginLeft: 16 }} onClick={handleSelectAll}>Select All</button>
        <button className="button small" onClick={handleSelectNone}>Select None</button>
        <button className="button small" style={{ marginLeft: 8 }} onClick={handleBatchEdit} disabled={selectedProposalIds.length === 0}>Batch Edit</button>
      </div>
      
      <div className="tree-content">
        {filteredProposals.length === 0 ? (
          <div className="empty-state">
            {proposals.length === 0 ? (
              <>
                <p>No mappings generated yet</p>
                <p>Select a profile and scan a folder to see preview</p>
              </>
            ) : (
              <p>No items match the current filter</p>
            )}
          </div>
        ) : (
          filteredProposals.map((proposal, index) => (
            <PreviewNode
              key={`${proposal.id}-${index}`}
              proposal={proposal}
              level={0}
              checked={selectedProposalIds.includes(proposal.id)}
              onCheck={handleCheck}
              onSelect={handleProposalSelect}
              onEdit={handleProposalEdit}
            />
          ))
        )}
      </div>
      
      {selectedProposal && (
        <div className="tree-selection-info">
          <div className="selection-header">
            <strong>Selected Mapping</strong>
            <span className={`status-badge ${selectedProposal.status}`}>
              {selectedProposal.status}
            </span>
          </div>
          <div className="selection-details">
            <div className="detail-row">
              <strong>Source:</strong> {selectedProposal.sourcePath}
            </div>
            <div className="detail-row">
              <strong>Target:</strong> {selectedProposal.targetPath}
            </div>
            {selectedProposal.shot && (
              <div className="detail-row">
                <strong>Shot:</strong> {selectedProposal.shot}
              </div>
            )}
            {selectedProposal.task && (
              <div className="detail-row">
                <strong>Task:</strong> {selectedProposal.task}
              </div>
            )}
            {selectedProposal.version && (
              <div className="detail-row">
                <strong>Version:</strong> {selectedProposal.version}
              </div>
            )}
            {selectedProposal.resolution && (
              <div className="detail-row">
                <strong>Resolution:</strong> {selectedProposal.resolution}
              </div>
            )}
          </div>
        </div>
      )}
      
      {renderEditModal()}
      {renderBatchEditModal()}
    </div>
  );
};

export default PreviewTree; 