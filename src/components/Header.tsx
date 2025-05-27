import React from 'react';
import { IconSettings, IconTerminal, IconRefresh } from '@tabler/icons-react';
import { useSettingsStore, useAppStore } from '../store';

const Header: React.FC = () => {
  const { setOpen } = useSettingsStore();
  const { 
    isLogWindowOpen, 
    setLogWindowOpen, 
    incomingTree, 
    currentProfile, 
    destinationRoot,
    setProposals,
    addLog,
    isScanning,
    isApplying
  } = useAppStore();

  const handleRefresh = async () => {
    if (!incomingTree || !currentProfile) {
      addLog('warning', 'Cannot refresh', 'Please scan a folder and select a profile first');
      return;
    }

    try {
      addLog('info', 'Refreshing mappings', `Using profile: ${currentProfile.name}`);
      
      const mappingResult = await window.electronAPI.generateMapping(incomingTree, {
        ...currentProfile,
        vfxRootPath: destinationRoot
      });
      
      const proposals = Array.isArray(mappingResult) ? mappingResult : [];
      setProposals(proposals);
      
      addLog('success', 'Mappings refreshed', `Generated ${proposals.length} proposals with updated settings`);
      
      const autoMapped = proposals.filter(p => p.status === 'auto').length;
      const unmapped = proposals.filter(p => p.status === 'unmapped').length;
      addLog('info', 'Refresh statistics', `Auto-mapped: ${autoMapped}, Unmapped: ${unmapped}`);
    } catch (error) {
      addLog('error', 'Failed to refresh mappings', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const canRefresh = incomingTree && currentProfile && !isScanning && !isApplying;

  return (
    <div className="app-header">
      <div className="header-left">
        <h1>VFX Folder Normalizer</h1>
        <span className="version">v1.0.0</span>
      </div>
      <div className="header-right">
        <button 
          className="button secondary small" 
          onClick={handleRefresh}
          disabled={!canRefresh}
          title="Refresh mappings with current profile settings"
        >
          <IconRefresh size={14} />
          Refresh
        </button>
        <button 
          className="button secondary small" 
          onClick={() => setLogWindowOpen(!isLogWindowOpen)}
          title="Toggle Log Window (Debug)"
        >
          <IconTerminal size={14} />
          Logs
        </button>
        <button 
          className="button secondary small" 
          onClick={() => setOpen(true)}
          title="Settings"
        >
          <IconSettings size={14} />
          Settings
        </button>
      </div>
    </div>
  );
};

export default Header; 