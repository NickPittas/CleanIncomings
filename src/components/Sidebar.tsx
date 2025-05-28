import React, { useState } from 'react';
import { IconFolder, IconPlayerPlay, IconRefresh, IconPlus, IconEdit } from '@tabler/icons-react';
import { useAppStore, useSettingsStore } from '../store';
import { MappingProposal } from '../types';

// The electronAPI interface is defined in src/types/index.d.ts

// Generates mapping proposals by calling the backend
async function generateMappingProposals(tree: any, profile: any): Promise<MappingProposal[]> {
  if (!window.electronAPI.generateMapping) {
    throw new Error('generateMapping API not available');
  }
  const result = await window.electronAPI.generateMapping(tree, profile);
  
  // Check if result is an array directly (old format)
  if (Array.isArray(result)) {
    console.log('[INFO] Processing mapping results:', `Found ${result.length} mapping proposals (array format)`);
    return result;
  }
  
  // Check if result has a 'mappings' property (new format from Python backend)
  if (result && result.success && Array.isArray(result.mappings)) {
    console.log('[INFO] Processing mapping results:', `Found ${result.mappings.length} mapping proposals (mappings format)`);
    return result.mappings;
  }
  
  // Check if result has a 'proposals' property (alternative format)
  if (result && Array.isArray(result.proposals)) {
    console.log('[INFO] Processing mapping results:', `Found ${result.proposals.length} mapping proposals (proposals format)`);
    return result.proposals;
  }
  
  // If we get here, the format is invalid
  console.error('Invalid mapping result format:', result);
  throw new Error('Invalid response format from generateMapping');
}

const Sidebar: React.FC = () => {
  const {
    proposals,
    currentProfile,
    profiles,
    isScanning,
    isApplying,
    setIsScanning,
    setLastError,
    setIncomingTree,
    setProposals,
    setCurrentProfile,
    addLog,
    startProgress,
    finishProgress,
    destinationRoot,
    setDestinationRoot,
    selectedProposalIds
  } = useAppStore();
  
  const { setOpen, setActiveTab } = useSettingsStore();

  const [operationType, setOperationType] = useState<'move' | 'copy'>('move');

  // Debug logging for operation type changes
  const handleOperationTypeChange = (newType: 'move' | 'copy') => {
    console.log('[DEBUG] Operation type changing from', operationType, 'to', newType);
    addLog('info', `[DEBUG] Operation type changed`, `From: ${operationType} → To: ${newType}`);
    setOperationType(newType);
  };

  const handleFolderSelect = async () => {
    if (!currentProfile) {
      addLog('error', 'No profile selected', 'Please select a profile first');
      return;
    }

    try {
      const result = await window.electronAPI.selectFolder();
      if (result) {
        addLog('info', 'Folder selected', result);
        await scanFolder(result);
      }
    } catch (error) {
      addLog('error', 'Error selecting folder', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const scanFolder = async (folderPath: string) => {
    try {
      setIsScanning(true);
      setLastError(null);
      addLog('info', 'Starting folder scan', folderPath);
      startProgress('applying', 100); // Use 'applying' as the operation type and 100 as a placeholder total
      
      // Perform a regular scan without progress tracking
      const result = await window.electronAPI.scanFolder(folderPath);
      
      // Process the scan results
      if (result && result.tree) {
        addLog('success', 'Folder scan completed', `Found ${result.stats?.total_files || 0} files and ${result.stats?.total_folders || 0} folders`);
        setIncomingTree(result.tree);
        // Generate mapping proposals using backend
        try {
          const proposals = await generateMappingProposals(result.tree, currentProfile);
          setProposals(proposals);
        } catch (mappingError) {
          addLog('error', 'Proposal generation failed', mappingError instanceof Error ? mappingError.message : 'Unknown error');
          setProposals([]);
        }
      } else {
        throw new Error('Invalid scan result');
      }
      setIsScanning(false);
      finishProgress();
    } catch (error) {
      const errorMessage = `Failed to scan folder: ${error}`;
      addLog('error', 'Scan failed', errorMessage);
      setLastError(errorMessage);
      setIsScanning(false);
      finishProgress();
    }
  };

  // Button handler for cancelling a scan
  const handleCancelScan = async () => {
    try {
      addLog('info', 'Cancelling scan');
      await window.electronAPI.cancelScan('current-scan');
      console.log(' Scan cancelled');
      
      // Clear the scanning state
      setIsScanning(false);
    } catch (error) {
      addLog('error', 'Failed to cancel scan', error instanceof Error ? error.message : 'Unknown error');
      setIsScanning(false);
    }
  };


  const handleApply = async () => {
    if (applicableCount === 0) {
      setLastError('No mappings selected');
      addLog('error', 'No mappings selected', 'Please select files/sequences to copy or move.');
      return;
    }
    try {
      setLastError(null);
      
      // Get multithreaded settings from store
      const { appSettings } = useAppStore.getState();
      const { multithreaded } = appSettings;
      
      // Debug logging
      console.log('[DEBUG] Operation type selected:', operationType);
      addLog('info', `[DEBUG] Operation type: ${operationType}`, 'Checking what operation is being sent to backend');
      addLog('info', 'Multithreaded settings', 
        `Enabled: ${multithreaded.enabled}, Max Workers: ${multithreaded.maxWorkers}, File Workers: ${multithreaded.fileWorkers}`);
      
      const requestData = {
        mappings: getApplicableProposals(),
        operation_type: operationType,
        // Include multithreaded settings
        multithreaded: {
          enabled: multithreaded.enabled,
          max_workers: multithreaded.maxWorkers,
          file_workers: multithreaded.fileWorkers
        }
      };
      
      console.log('[DEBUG] Request data being sent:', requestData);
      addLog('info', `[DEBUG] Request data`, JSON.stringify(requestData, null, 2));
      
      addLog('info', `Attempting to ${operationType} ${applicableCount} mappings`, 
        `Using ${multithreaded.enabled ? 'multithreaded' : 'single-threaded'} mode`);
      
      // Start progress tracking immediately to show the progress bar
      startProgress('applying', applicableCount);
      
      const result = await window.electronAPI.applyMappingsEnhanced(requestData);
      
      addLog('info', 'Backend response', JSON.stringify(result, null, 2));
      
      if (result.success) {
        // Update progress tracking with the batchId from the backend
        if (result.batch_id) {
          // Update the existing progress state with the batchId
          const { progressState } = useAppStore.getState();
          useAppStore.setState({
            progressState: {
              ...progressState,
              batchId: result.batch_id
            }
          });
          addLog('info', 'Progress tracking updated with batchId', `Batch ID: ${result.batch_id}`);
          
          // Don't call finishProgress here - let the ProgressBar component handle it
          // when it detects the operation is complete via polling
        } else {
          // No batch_id means operation completed immediately
          addLog('warning', 'No batch_id in response', 'Operation may have completed immediately');
          finishProgress();
        }
        
        setLastError(null);
        addLog('success', `${operationType === 'copy' ? 'Copy' : 'Move'} operation completed`, `${result.success_count || 0} succeeded, ${result.error_count || 0} errors.`);
      } else {
        finishProgress();
        setLastError(result.error || 'Failed to apply mappings');
        addLog('error', 'Apply operation failed', result.error || 'Unknown error');
      }
    } catch (error) {
      finishProgress();
      setLastError(`Failed to apply mappings: ${error}`);
      addLog('error', 'Apply operation exception', error instanceof Error ? error.message : String(error));
    }
  };

  const handleUndo = async () => {
    try {
      setLastError(null);
      const result = await window.electronAPI.undoLastBatch();
      if (result.success) {
        setLastError(null);
        // Optionally refresh the tree
      } else {
        setLastError(result.error || 'Failed to undo operations');
      }
    } catch (error) {
      setLastError(`Failed to undo: ${error}`);
    }
  };

  const handleCreateProfile = () => {
    setActiveTab('profiles');
    setOpen(true);
    // The settings modal will handle profile creation
  };

  const getApplicableProposals = () => {
    return (proposals || []).filter(p => selectedProposalIds.includes(p.id));
  };

  const applicableCount = getApplicableProposals().length;

  const autoMappedCount = (proposals || []).filter(p => p.status === 'auto').length;
  const overrideCount = (proposals || []).filter(p => p.status === 'override').length;
  const unmappedCount = (proposals || []).filter(p => p.status === 'unmapped').length;

  const handlePickDestinationRoot = async () => {
    if (window.electronAPI && window.electronAPI.selectFolder) {
      const folder = await window.electronAPI.selectFolder();
      if (folder) {
        setDestinationRoot(folder);
        addLog('info', 'Destination root changed', `All proposals updated to: ${folder}`);
      }
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-section">
        <h3>Profile</h3>
        {profiles.length === 0 ? (
          <div className="no-profiles">
            <p>No profiles available</p>
            <button className="button" onClick={handleCreateProfile}>
              <IconPlus size={16} />
              Create Profile
            </button>
          </div>
        ) : (
          <select
            value={currentProfile?.id || ''}
            onChange={(e) => {
              const profile = profiles.find(p => p.id === e.target.value);
              setCurrentProfile(profile || null);
            }}
          >
            <option value="">Select a profile...</option>
            {profiles.map(profile => (
              <option key={profile.id} value={profile.id}>
                {profile.name}
              </option>
            ))}
          </select>
        )}
        
        <button 
          className="button secondary" 
          onClick={() => {
            setActiveTab('profiles');
            setOpen(true);
          }}
        >
          <IconEdit size={16} />
          Manage Profiles
        </button>
      </div>

      <div className="sidebar-section">
        <h3>Import</h3>
        
        <button 
          className="button" 
          onClick={isScanning ? handleCancelScan : handleFolderSelect}
          disabled={!currentProfile && !isScanning}
        >
          <IconFolder size={16} />
          {isScanning ? 'Cancel Scan' : 'Select Folder'}
        </button>
      </div>

      <div className="sidebar-section">
        <h3>Actions</h3>
        <div className="form-row">
          <label>Operation:</label>
          <select
            value={operationType}
            onChange={e => handleOperationTypeChange(e.target.value as 'move' | 'copy')}
            disabled={isApplying}
          >
            <option value="move">Move</option>
            <option value="copy">Copy</option>
          </select>
        </div>
        
        <div className="form-row">
          <label>Destination:</label>
          <div className="input-with-button">
            <input
              type="text"
              value={destinationRoot}
              onChange={e => setDestinationRoot(e.target.value)}
              placeholder="Select destination folder..."
            />
            <button
              className="button small"
              onClick={handlePickDestinationRoot}
              title="Browse for folder"
            >
              <IconFolder size={14} />
            </button>
          </div>
        </div>
        
        <button 
          className="button primary" 
          onClick={handleApply}
          disabled={isApplying || applicableCount === 0}
        >
          <IconPlayerPlay size={16} />
          {isApplying ? 'Applying...' : `${operationType === 'copy' ? 'Copy' : 'Move'} ${applicableCount} Mappings`}
        </button>
        
        <button 
          className="button secondary" 
          onClick={handleUndo}
          disabled={isApplying}
        >
          <IconRefresh size={16} />
          Undo Last Operation
        </button>
      </div>

      {currentProfile && (
        <div className="sidebar-section">
          <h3>Current Profile</h3>
          <div className="profile-summary">
            <strong>{currentProfile.name}</strong>
            {currentProfile.description && (
              <p>{currentProfile.description}</p>
            )}
            <small>Root: {currentProfile.vfxRootPath}</small>
          </div>
        </div>
      )}

      {(proposals || []).length > 0 && (
        <div className="sidebar-section">
          <h3>Mapping Summary</h3>
          <div className="mapping-summary">
            <div className="summary-item">
              <span>Auto-mapped</span>
              <span>{autoMappedCount}</span>
            </div>
            <div className="summary-item">
              <span>Manual overrides</span>
              <span>{overrideCount}</span>
            </div>
            <div className="summary-item">
              <span>Unmapped</span>
              <span>{unmappedCount}</span>
            </div>
          </div>
        </div>
      )}

      {/* No dialog needed */}

    </div>
  );
};

export default Sidebar; 