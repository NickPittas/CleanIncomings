import React, { useState, useEffect } from 'react';
import { 
  IconPlayerPlay, 
  IconPlayerPause, 
  IconPlayerStop, 
  IconRefresh, 
  IconCheck, 
  IconAlertTriangle,
  IconCopy,
  IconCut,
  IconSettings
} from '@tabler/icons-react';
import { useAppStore } from '../store';
import { MappingProposal, BatchProgress, BatchValidationResult } from '../types';

interface OperationsControlProps {
  proposals: MappingProposal[];
  onApply: (options: any) => Promise<any>;
  onUndo: () => Promise<any>;
}

const OperationsControl: React.FC<OperationsControlProps> = ({ proposals, onApply, onUndo }) => {
  const { addLog, isApplying, setIsApplying, startProgress, finishProgress } = useAppStore();
  const [operationType, setOperationType] = useState<'move' | 'copy'>('move');
  const [validateSequences, setValidateSequences] = useState(true);
  const [currentBatchId, setCurrentBatchId] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
  const [validationResult, setValidationResult] = useState<BatchValidationResult | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  // Get multithreaded settings from store
  const { appSettings } = useAppStore();
  const { multithreaded } = appSettings;

  // Progress polling
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (currentBatchId && isApplying) {
      interval = setInterval(async () => {
        try {
          const progress = await window.electronAPI.getProgress(currentBatchId);
          if (progress && !progress.error) {
            setBatchProgress(progress);
            setIsPaused(progress.isPaused);
            
            // Stop polling if operation is complete
            if (['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(progress.status)) {
              setIsApplying(false);
              setCurrentBatchId(null);
              finishProgress();
              
              // Auto-validate sequences if enabled
              if (validateSequences && progress.status === 'completed') {
                handleValidateSequences(currentBatchId);
              }
            }
          }
        } catch (error) {
          console.error('Failed to get progress:', error);
        }
      }, 500); // Poll every 500ms for more responsive updates
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentBatchId, isApplying, validateSequences]);

  const getApplicableProposals = () => {
    return proposals.filter(p => p.status === 'auto' || p.status === 'override');
  };

  const getSequenceCount = () => {
    return getApplicableProposals().filter(p => p.isSequence).length;
  };

  const getSingleFileCount = () => {
    return getApplicableProposals().filter(p => !p.isSequence).length;
  };

  const handleApply = async () => {
    if (isApplying) return;
    
    const applicableProposals = getApplicableProposals();
    if (applicableProposals.length === 0) {
      addLog('warning', 'No applicable proposals', 'Please ensure you have valid mappings to apply.');
      return;
    }

    try {
      setIsApplying(true);
      setValidationResult(null);
      
      addLog('info', `Starting ${operationType} operation`, `Processing ${applicableProposals.length} mappings`);
      
      // Prepare options with multithreaded settings
      const options = {
        mappings: applicableProposals,
        operationType,
        validateSequences,
        // Include multithreaded settings
        multithreaded: {
          enabled: multithreaded.enabled,
          maxWorkers: multithreaded.maxWorkers,
          fileWorkers: multithreaded.fileWorkers
        }
      };

      addLog('info', 'Multithreaded settings', 
        `Enabled: ${multithreaded.enabled}, Max Workers: ${multithreaded.maxWorkers}, File Workers: ${multithreaded.fileWorkers}`);

      const result = await onApply(options);
      
      if (result.success) {
        addLog('success', 'Operation completed successfully', 
          `${result.success_count} operations completed${result.error_count > 0 ? `, ${result.error_count} errors` : ''}`);
        
        if (result.batch_id) {
          setCurrentBatchId(result.batch_id);
          
          if (validateSequences) {
            addLog('info', 'Starting sequence validation', 'Checking sequence integrity...');
            await handleValidateSequences(result.batch_id);
          }
        }
      } else {
        addLog('error', 'Operation failed', result.message || 'Unknown error occurred');
      }
    } catch (error: any) {
      addLog('error', 'Operation error', error?.message || 'An unexpected error occurred');
    } finally {
      setIsApplying(false);
      setBatchProgress(null);
    }
  };

  const handlePause = async () => {
    try {
      await window.electronAPI.pauseOperations();
      setIsPaused(true);
      addLog('info', 'Operations paused', 'You can resume or cancel the operation');
    } catch (error) {
      addLog('error', 'Failed to pause operations', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleResume = async () => {
    try {
      await window.electronAPI.resumeOperations();
      setIsPaused(false);
      addLog('info', 'Operations resumed', 'Continuing with file operations');
    } catch (error) {
      addLog('error', 'Failed to resume operations', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleCancel = async () => {
    try {
      await window.electronAPI.cancelOperations();
      setIsApplying(false);
      setCurrentBatchId(null);
      setBatchProgress(null);
      setIsPaused(false);
      addLog('warning', 'Operations cancelled', 'File operations have been cancelled');
    } catch (error) {
      addLog('error', 'Failed to cancel operations', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const handleValidateSequences = async (batchId: string) => {
    try {
      addLog('info', 'Validating sequences', 'Checking sequence integrity...');
      const result = await window.electronAPI.validateSequences(batchId);
      
      if (result && !result.error) {
        setValidationResult(result);
        
        const completeSequences = result.validations.filter((v: any) => v.validation_status === 'complete').length;
        const totalSequences = result.validations.length;
        
        if (result.overall_status === 'complete') {
          addLog('success', 'Sequence validation complete', 
            `All ${totalSequences} sequences are complete and valid`);
        } else {
          addLog('warning', 'Sequence validation issues found', 
            `${completeSequences}/${totalSequences} sequences are complete`);
        }
      }
    } catch (error) {
      addLog('error', 'Failed to validate sequences', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`;
  };

  const applicableCount = getApplicableProposals().length;
  const sequenceCount = getSequenceCount();
  const singleFileCount = getSingleFileCount();

  return (
    <div className="operations-control">
      <div className="operations-header">
        <h3>File Operations</h3>
        <button 
          className="button secondary small"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          <IconSettings size={14} />
          {showAdvanced ? 'Hide' : 'Show'} Advanced
        </button>
      </div>

      {showAdvanced && (
        <div className="operations-settings">
          <div className="setting-group">
            <label>Operation Type</label>
            <div className="operation-type-selector">
              <button 
                className={`operation-button ${operationType === 'move' ? 'active' : ''}`}
                onClick={() => setOperationType('move')}
                disabled={isApplying}
              >
                <IconCut size={16} />
                Move Files
              </button>
              <button 
                className={`operation-button ${operationType === 'copy' ? 'active' : ''}`}
                onClick={() => setOperationType('copy')}
                disabled={isApplying}
              >
                <IconCopy size={16} />
                Copy Files
              </button>
            </div>
          </div>

          <div className="setting-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={validateSequences}
                onChange={(e) => setValidateSequences(e.target.checked)}
                disabled={isApplying}
              />
              Validate sequence integrity after operations
            </label>
          </div>

          <div className="setting-group">
            <label>Performance Settings</label>
            <div className="performance-indicator">
              <div className="performance-status">
                <span className={`status-badge ${multithreaded.enabled ? 'enabled' : 'disabled'}`}>
                  {multithreaded.enabled ? 'Multithreaded' : 'Single-threaded'}
                </span>
                {multithreaded.enabled && (
                  <span className="performance-details">
                    {multithreaded.maxWorkers} workers × {multithreaded.fileWorkers} files
                  </span>
                )}
              </div>
              <small className="performance-note">
                {multithreaded.enabled 
                  ? `Using ${multithreaded.maxWorkers * multithreaded.fileWorkers} total threads for maximum performance`
                  : 'Change in Settings → Performance to enable multithreading'
                }
              </small>
            </div>
          </div>
        </div>
      )}

      <div className="operations-summary">
        <div className="summary-item">
          <span className="summary-label">Ready to apply:</span>
          <span className="summary-value">{applicableCount} mappings</span>
        </div>
        {sequenceCount > 0 && (
          <div className="summary-item">
            <span className="summary-label">Sequences:</span>
            <span className="summary-value">{sequenceCount}</span>
          </div>
        )}
        {singleFileCount > 0 && (
          <div className="summary-item">
            <span className="summary-label">Single files:</span>
            <span className="summary-value">{singleFileCount}</span>
          </div>
        )}
      </div>

      {batchProgress && (
        <div className="batch-progress">
          <div className="progress-header">
            <span className="progress-title">
              {operationType === 'move' ? 'Moving' : 'Copying'} Files
            </span>
            <span className="progress-status">{batchProgress.status}</span>
          </div>
          
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${batchProgress.progressPercentage}%` }}
            />
          </div>
          
          <div className="progress-details">
            <div className="progress-stats">
              <span>{batchProgress.completedOperations} / {batchProgress.totalOperations} operations</span>
              <span>{batchProgress.progressPercentage.toFixed(1)}%</span>
            </div>
            
            {batchProgress.totalSize > 0 && (
              <div className="progress-size">
                <span>{formatFileSize(batchProgress.processedSize)} / {formatFileSize(batchProgress.totalSize)}</span>
              </div>
            )}
            
            {batchProgress.etaSeconds > 0 && (
              <div className="progress-eta">
                <span>ETA: {formatDuration(batchProgress.etaSeconds)}</span>
              </div>
            )}
            
            {batchProgress.failedOperations > 0 && (
              <div className="progress-errors">
                <IconAlertTriangle size={14} />
                <span>{batchProgress.failedOperations} errors</span>
              </div>
            )}
          </div>
        </div>
      )}

      {validationResult && (
        <div className="validation-result">
          <div className="validation-header">
            <IconCheck size={16} />
            <span>Sequence Validation</span>
            <span className={`validation-status ${validationResult.overallStatus}`}>
              {validationResult.overallStatus}
            </span>
          </div>
          
          <div className="validation-summary">
            <span>{validationResult.sequenceCount} sequences validated</span>
            {validationResult.overallStatus === 'incomplete' && (
              <span className="validation-warning">Some sequences have missing frames</span>
            )}
          </div>
        </div>
      )}

      <div className="operations-actions">
        {!isApplying ? (
          <>
            <button 
              className="button primary"
              onClick={handleApply}
              disabled={applicableCount === 0}
            >
              <IconPlayerPlay size={16} />
              {operationType === 'move' ? 'Move' : 'Copy'} {applicableCount} Mappings
            </button>
            
            <button 
              className="button secondary"
              onClick={onUndo}
            >
              <IconRefresh size={16} />
              Undo Last Operation
            </button>
          </>
        ) : (
          <div className="operation-controls">
            {!isPaused ? (
              <button 
                className="button warning"
                onClick={handlePause}
              >
                <IconPlayerPause size={16} />
                Pause
              </button>
            ) : (
              <button 
                className="button primary"
                onClick={handleResume}
              >
                <IconPlayerPlay size={16} />
                Resume
              </button>
            )}
            
            <button 
              className="button danger"
              onClick={handleCancel}
            >
              <IconPlayerStop size={16} />
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperationsControl; 