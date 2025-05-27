import React, { useState, useEffect } from 'react';
import { IconX, IconPlus, IconEdit, IconTrash, IconDownload, IconUpload, IconCpu, IconSettings2 } from '@tabler/icons-react';
import { useSettingsStore, useAppStore } from '../store';
import { Profile } from '../types';

const SettingsModal: React.FC = () => {
  const { setOpen, activeTab, setActiveTab } = useSettingsStore();
  const { profiles, currentProfile, addProfile, updateProfile, deleteProfile, setCurrentProfile, appSettings, updateMultithreadedSettings } = useAppStore();
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // User-friendly pattern management state
  const [shotNames, setShotNames] = useState<string[]>([]);
  const [resolutions, setResolutions] = useState<string[]>([]);
  const [customTasks, setCustomTasks] = useState<Array<{name: string, aliases: string[]}>>([]);

  // Patterns tab state
  const [patternConfig, setPatternConfig] = useState<any>(null);
  const [assetPatterns, setAssetPatterns] = useState<string[]>([]);
  const [stagePatterns, setStagePatterns] = useState<string[]>([]);
  const [isSavingPatterns, setIsSavingPatterns] = useState(false);
  const [patternError, setPatternError] = useState<string | null>(null);

  // Add state for all patterns.json fields
  const [shotPatterns, setShotPatterns] = useState<string[]>([]);
  const [taskPatterns, setTaskPatterns] = useState<Record<string, string[]>>({});
  const [resolutionPatterns, setResolutionPatterns] = useState<string[]>([]);
  const [versionPatterns, setVersionPatterns] = useState<string[]>([]);
  const [showRawJson, setShowRawJson] = useState(false);
  const [rawJson, setRawJson] = useState('');

  const handleCreateProfile = () => {
    const newProfile: Profile = {
      id: Date.now().toString(),
      name: 'New Profile',
      description: '',
      vfxRootPath: '/vfx/projects',
      // User-friendly pattern storage
      userPatterns: {
        shotNames: ['shot_001', 'shot_002', 'shot_003'],
        resolutions: ['2k', '4k', '1920x1080', 'uhd', 'hd'],
        tasks: [
          { name: 'comp', aliases: ['composite', 'final', 'comp'] },
          { name: 'render', aliases: ['beauty', 'rgb', 'render'] },
          { name: 'plate', aliases: ['bg', 'background', 'plate'] },
          { name: 'roto', aliases: ['rotoscope', 'roto'] },
          { name: 'paint', aliases: ['cleanup', 'paint'] },
          { name: 'track', aliases: ['matchmove', 'camera', 'track'] },
          { name: 'fx', aliases: ['effects', 'sim', 'fx'] },
          { name: 'light', aliases: ['lighting', 'light'] },
          { name: 'anim', aliases: ['animation', 'anim'] }
        ]
      },
      // Legacy regex patterns (auto-generated from user patterns)
      shotPatterns: [
        '(?i)(?:shot_?)?(\d{3,4})',
        '(?i)sh_?(\d{3,4})',
        '(?i)s(\d{3,4})',
        '(?i)(\d{3,4})_shot'
      ],
      taskMaps: [
        { regex: '(?i)comp', canonical: 'comp', priority: 10 },
        { regex: '(?i)render', canonical: 'render', priority: 9 },
        { regex: '(?i)plate', canonical: 'plate', priority: 8 },
        { regex: '(?i)roto', canonical: 'roto', priority: 7 },
        { regex: '(?i)paint', canonical: 'paint', priority: 6 },
        { regex: '(?i)track', canonical: 'track', priority: 5 },
        { regex: '(?i)fx', canonical: 'fx', priority: 4 },
        { regex: '(?i)light', canonical: 'light', priority: 3 },
        { regex: '(?i)anim', canonical: 'anim', priority: 2 }
      ],
      resolutionPatterns: [
        '(?i)(\d{3,4}k)',
        '(?i)(\d{3,4}x\d{3,4})',
        '(?i)(uhd|hd|sd)'
      ],
      fileTypeRules: [
        { extensions: ['.exr', '.dpx', '.tiff', '.tif', '.hdr'], category: 'render', priority: 10 },
        { extensions: ['.mov', '.mp4', '.avi', '.mkv', '.r3d', '.braw'], category: 'video', priority: 9 },
        { extensions: ['.nk', '.hip', '.ma', '.mb', '.blend', '.c4d', '.aep'], category: 'project', priority: 8 },
        { extensions: ['.abc', '.bgeo', '.vdb', '.ass', '.usd'], category: 'cache', priority: 7 }
      ],
      versionPattern: 'v\\d{3}',
      isActive: false,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    addProfile(newProfile);
    setEditingProfile(newProfile);
    setShowCreateForm(false);
  };

  // Initialize user-friendly patterns when editing starts
  React.useEffect(() => {
    if (editingProfile?.userPatterns) {
      setShotNames(editingProfile.userPatterns.shotNames || []);
      setResolutions(editingProfile.userPatterns.resolutions || []);
      setCustomTasks(editingProfile.userPatterns.tasks || []);
    }
  }, [editingProfile]);

  const handleSaveProfile = (profile: Profile) => {
    // Convert user-friendly patterns to regex patterns
    const updatedProfile = {
      ...profile,
      userPatterns: {
        shotNames,
        resolutions,
        tasks: customTasks
      },
      // Auto-generate regex patterns from user input
      shotPatterns: generateShotPatterns(shotNames),
      resolutionPatterns: generateResolutionPatterns(resolutions),
      taskMaps: generateTaskMaps(customTasks),
      updatedAt: new Date()
    };
    updateProfile(profile.id, updatedProfile);
    setEditingProfile(null);
  };

  // Helper functions to convert user patterns to regex
  const generateShotPatterns = (names: string[]): string[] => {
    const patterns: string[] = [
      '(?i)(?:shot_?)?(\d{3,4})',  // Default numeric patterns
      '(?i)sh_?(\d{3,4})',
      '(?i)s(\d{3,4})',
    ];
    
    // Add specific shot name patterns
    names.forEach(name => {
      if (name.includes('_')) {
        patterns.push(`(?i)${name.replace('_', '_?')}`);
      } else {
        patterns.push(`(?i)${name}`);
      }
    });
    
    return patterns;
  };

  const generateResolutionPatterns = (resolutions: string[]): string[] => {
    const patterns: string[] = [];
    
    resolutions.forEach(res => {
      if (res.includes('x')) {
        patterns.push(`(?i)${res.replace('x', 'x')}`);
      } else if (res.includes('k')) {
        patterns.push(`(?i)${res}`);
      } else {
        patterns.push(`(?i)${res}`);
      }
    });
    
    return patterns;
  };

  const generateTaskMaps = (tasks: Array<{name: string, aliases: string[]}>): Array<{regex: string, canonical: string, priority: number}> => {
    return tasks.map((task, index) => ({
      regex: `(?i)(${task.aliases.join('|')})`,
      canonical: task.name,
      priority: 10 - index
    }));
  };

  const handleDeleteProfile = (profileId: string) => {
    if (window.confirm('Are you sure you want to delete this profile?')) {
      deleteProfile(profileId);
      if (currentProfile?.id === profileId) {
        setCurrentProfile(null);
      }
    }
  };

  const handleExportProfile = (profile: Profile) => {
    const dataStr = JSON.stringify(profile, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${profile.name.replace(/\s+/g, '_')}_profile.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImportProfile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const profileData = JSON.parse(e.target?.result as string);
          const importedProfile: Profile = {
            ...profileData,
            id: Date.now().toString(),
            createdAt: new Date(),
            updatedAt: new Date()
          };
          addProfile(importedProfile);
        } catch (error) {
          alert('Failed to import profile. Please check the file format.');
        }
      };
      reader.readAsText(file);
    }
  };

  // User-friendly pattern editors
  const renderShotNameEditor = () => (
    <div className="pattern-editor">
      <h4>Shot Names</h4>
      <p className="help-text">Add specific shot names that appear in your files (e.g., shot_001, hero_shot, finale)</p>
      
      <div className="pattern-list">
        {shotNames.map((name, index) => (
          <div key={index} className="pattern-item">
            <input
              type="text"
              value={name}
              onChange={(e) => {
                const newNames = [...shotNames];
                newNames[index] = e.target.value;
                setShotNames(newNames);
              }}
              placeholder="e.g., shot_001"
            />
            <button
              className="button danger small"
              onClick={() => setShotNames(shotNames.filter((_, i) => i !== index))}
            >
              <IconTrash size={14} />
            </button>
          </div>
        ))}
      </div>
      
      <button
        className="button secondary"
        onClick={() => setShotNames([...shotNames, ''])}
      >
        <IconPlus size={16} /> Add Shot Name
      </button>
    </div>
  );

  const renderResolutionEditor = () => (
    <div className="pattern-editor">
      <h4>Resolutions</h4>
      <p className="help-text">Add resolution formats that appear in your files (e.g., 2k, 4k, 1920x1080, uhd)</p>
      
      <div className="pattern-list">
        {resolutions.map((res, index) => (
          <div key={index} className="pattern-item">
            <input
              type="text"
              value={res}
              onChange={(e) => {
                const newRes = [...resolutions];
                newRes[index] = e.target.value;
                setResolutions(newRes);
              }}
              placeholder="e.g., 2k, 1920x1080"
            />
            <button
              className="button danger small"
              onClick={() => setResolutions(resolutions.filter((_, i) => i !== index))}
            >
              <IconTrash size={14} />
            </button>
          </div>
        ))}
      </div>
      
      <button
        className="button secondary"
        onClick={() => setResolutions([...resolutions, ''])}
      >
        <IconPlus size={16} /> Add Resolution
      </button>
    </div>
  );

  const renderTaskEditor = () => (
    <div className="pattern-editor">
      <h4>Tasks & Aliases</h4>
      <p className="help-text">Define task types and their common aliases (e.g., comp might also be called composite or final)</p>
      
      <div className="task-list">
        {customTasks.map((task, index) => (
          <div key={index} className="task-item">
            <div className="task-header">
              <input
                type="text"
                value={task.name}
                onChange={(e) => {
                  const newTasks = [...customTasks];
                  newTasks[index].name = e.target.value;
                  setCustomTasks(newTasks);
                }}
                placeholder="Task name (e.g., comp)"
                className="task-name-input"
              />
              <button
                className="button danger small"
                onClick={() => setCustomTasks(customTasks.filter((_, i) => i !== index))}
              >
                <IconTrash size={14} />
              </button>
            </div>
            
            <div className="aliases">
              <label>Aliases:</label>
              <div className="alias-list">
                {task.aliases.map((alias, aliasIndex) => (
                  <div key={aliasIndex} className="alias-item">
                    <input
                      type="text"
                      value={alias}
                      onChange={(e) => {
                        const newTasks = [...customTasks];
                        newTasks[index].aliases[aliasIndex] = e.target.value;
                        setCustomTasks(newTasks);
                      }}
                      placeholder="e.g., composite"
                    />
                    <button
                      className="button danger small"
                      onClick={() => {
                        const newTasks = [...customTasks];
                        newTasks[index].aliases = newTasks[index].aliases.filter((_, i) => i !== aliasIndex);
                        setCustomTasks(newTasks);
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))}
                <button
                  className="button secondary small"
                  onClick={() => {
                    const newTasks = [...customTasks];
                    newTasks[index].aliases.push('');
                    setCustomTasks(newTasks);
                  }}
                >
                  + Add Alias
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <button
        className="button secondary"
        onClick={() => setCustomTasks([...customTasks, { name: '', aliases: [''] }])}
      >
        <IconPlus size={16} /> Add Task Type
      </button>
    </div>
  );

  const renderProfileList = () => (
    <div className="profile-list">
      <div className="profile-list-header">
        <h3>Profiles</h3>
        <div className="profile-actions">
          <button className="button" onClick={() => setShowCreateForm(true)}>
            <IconPlus size={16} /> New Profile
          </button>
          <label className="button secondary">
            <IconUpload size={16} /> Import
            <input
              type="file"
              accept=".json"
              onChange={handleImportProfile}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>
      
      {showCreateForm && (
        <div className="create-profile-form">
          <p>Create a new profile with default VFX settings?</p>
          <div className="form-actions">
            <button className="button" onClick={handleCreateProfile}>
              Create Profile
            </button>
            <button className="button secondary" onClick={() => setShowCreateForm(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="profile-items">
        {profiles.map(profile => (
          <div key={profile.id} className={`profile-item ${currentProfile?.id === profile.id ? 'active' : ''}`}>
            <div className="profile-info">
              <h4>{profile.name}</h4>
              <p>{profile.description || 'No description'}</p>
              <small>Root: {profile.vfxRootPath}</small>
              {profile.userPatterns && (
                <div className="profile-summary">
                  <small>
                    {profile.userPatterns.shotNames?.length || 0} shots, {' '}
                    {profile.userPatterns.resolutions?.length || 0} resolutions, {' '}
                    {profile.userPatterns.tasks?.length || 0} tasks
                  </small>
                </div>
              )}
            </div>
            <div className="profile-actions">
              <button
                className="action-button"
                onClick={() => setCurrentProfile(profile)}
                title="Set as active profile"
              >
                {currentProfile?.id === profile.id ? '✓' : 'Use'}
              </button>
              <button
                className="action-button"
                onClick={() => setEditingProfile(profile)}
                title="Edit profile"
              >
                <IconEdit size={14} />
              </button>
              <button
                className="action-button"
                onClick={() => handleExportProfile(profile)}
                title="Export profile"
              >
                <IconDownload size={14} />
              </button>
              <button
                className="action-button danger"
                onClick={() => handleDeleteProfile(profile.id)}
                title="Delete profile"
              >
                <IconTrash size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderProfileEditor = () => {
    if (!editingProfile) return null;

    return (
      <div className="profile-editor">
        <div className="profile-editor-header">
          <h3>Edit Profile: {editingProfile.name}</h3>
          <button
            className="button secondary"
            onClick={() => setEditingProfile(null)}
          >
            Back to List
          </button>
        </div>

        <div className="profile-editor-content">
          <div className="form-group">
            <label>Profile Name</label>
            <input
              type="text"
              value={editingProfile.name}
              onChange={(e) => setEditingProfile({ ...editingProfile, name: e.target.value })}
              placeholder="Profile name"
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={editingProfile.description}
              onChange={(e) => setEditingProfile({ ...editingProfile, description: e.target.value })}
              placeholder="Profile description"
              rows={2}
            />
          </div>

          <div className="form-group">
            <label>VFX Root Path</label>
            <input
              type="text"
              value={editingProfile.vfxRootPath}
              onChange={(e) => setEditingProfile({ ...editingProfile, vfxRootPath: e.target.value })}
              placeholder="/vfx/projects"
            />
          </div>

          <div className="pattern-editors">
            {renderShotNameEditor()}
            {renderResolutionEditor()}
            {renderTaskEditor()}
          </div>

          <div className="form-actions">
            <button
              className="button"
              onClick={() => handleSaveProfile(editingProfile)}
            >
              Save Profile
            </button>
            <button
              className="button secondary"
              onClick={() => setEditingProfile(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderPerformanceSettings = () => (
    <div className="performance-settings">
      <h3>Performance Settings</h3>
      
      <div className="setting-section">
        <h4>
          <IconCpu size={18} />
          Multithreaded Copy Operations
        </h4>
        <p className="setting-description">
          Configure multithreaded copy settings for maximum 10G network performance. 
          These settings apply to copy operations and large file transfers.
        </p>
        
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={appSettings.multithreaded.enabled}
              onChange={(e) => updateMultithreadedSettings({ enabled: e.target.checked })}
            />
            Enable multithreaded copy operations
          </label>
          <small className="help-text">
            Uses parallel processing for faster file transfers on high-speed networks
          </small>
        </div>

        {appSettings.multithreaded.enabled && (
          <div className="multithreaded-controls">
            <div className="form-group">
              <label>
                Max Workers (Threads per file)
                <span className="setting-value">{appSettings.multithreaded.maxWorkers}</span>
              </label>
              <input
                type="range"
                min="1"
                max="32"
                step="1"
                value={appSettings.multithreaded.maxWorkers}
                onChange={(e) => updateMultithreadedSettings({ maxWorkers: parseInt(e.target.value) })}
                className="slider"
              />
              <div className="slider-labels">
                <span>1 (Single)</span>
                <span>8 (Optimal)</span>
                <span>16 (High)</span>
                <span>32 (Extreme)</span>
              </div>
              <small className="help-text">
                Number of parallel threads per file. 8 is optimal for most cases, 16+ for extreme performance.
              </small>
            </div>

            <div className="form-group">
              <label>
                File Workers (Concurrent files)
                <span className="setting-value">{appSettings.multithreaded.fileWorkers}</span>
              </label>
              <input
                type="range"
                min="1"
                max="16"
                step="1"
                value={appSettings.multithreaded.fileWorkers}
                onChange={(e) => updateMultithreadedSettings({ fileWorkers: parseInt(e.target.value) })}
                className="slider"
              />
              <div className="slider-labels">
                <span>1 (Sequential)</span>
                <span>4 (Balanced)</span>
                <span>8 (High)</span>
                <span>16 (Maximum)</span>
              </div>
              <small className="help-text">
                Number of files processed simultaneously. 4 provides good balance, higher values for more parallelism.
              </small>
            </div>

            <div className="performance-preview">
              <h5>Expected Performance</h5>
              <div className="performance-metrics">
                <div className="metric">
                  <span className="metric-label">Configuration:</span>
                  <span className="metric-value">
                    {appSettings.multithreaded.maxWorkers} threads × {appSettings.multithreaded.fileWorkers} files
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Total threads:</span>
                  <span className="metric-value">
                    {appSettings.multithreaded.maxWorkers * appSettings.multithreaded.fileWorkers}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Best for:</span>
                  <span className="metric-value">
                    {appSettings.multithreaded.maxWorkers <= 4 && appSettings.multithreaded.fileWorkers <= 2 
                      ? "Standard networks, lower CPU usage"
                      : appSettings.multithreaded.maxWorkers <= 8 && appSettings.multithreaded.fileWorkers <= 4
                      ? "10G networks, balanced performance"
                      : "High-speed networks, maximum throughput"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderGeneralSettings = () => (
    <div className="general-settings">
      <h3>General Settings</h3>
      <div className="form-group">
        <label>Default Profile</label>
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
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input 
            type="checkbox" 
            checked={appSettings.autoScanOnDrop}
            onChange={(e) => {
              const { setAppSettings } = useAppStore.getState();
              setAppSettings({
                ...appSettings,
                autoScanOnDrop: e.target.checked
              });
            }}
          />
          Auto-scan on folder drop
        </label>
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input 
            type="checkbox" 
            checked={appSettings.showFileSizeInTree}
            onChange={(e) => {
              const { setAppSettings } = useAppStore.getState();
              setAppSettings({
                ...appSettings,
                showFileSizeInTree: e.target.checked
              });
            }}
          />
          Show file size in tree
        </label>
      </div>
      
      <div className="form-group">
        <label className="checkbox-label">
          <input 
            type="checkbox" 
            checked={appSettings.enableDebugLogging}
            onChange={(e) => {
              const { setAppSettings } = useAppStore.getState();
              setAppSettings({
                ...appSettings,
                enableDebugLogging: e.target.checked
              });
            }}
          />
          Enable debug logging
        </label>
      </div>
    </div>
  );

  useEffect(() => {
    if (activeTab === 'patterns') {
      const load = async () => {
        if (window.electronAPI && window.electronAPI.loadPatternConfig) {
          const result = await window.electronAPI.loadPatternConfig();
          if (result && result.success && result.config) {
            setPatternConfig(result.config);
            setShotPatterns(Array.isArray(result.config.shotPatterns) ? result.config.shotPatterns : []);
            setTaskPatterns(result.config.taskPatterns || {});
            setResolutionPatterns(Array.isArray(result.config.resolutionPatterns) ? result.config.resolutionPatterns : []);
            setVersionPatterns(Array.isArray(result.config.versionPatterns) ? result.config.versionPatterns : []);
            setAssetPatterns(Array.isArray(result.config.assetPatterns) ? result.config.assetPatterns : []);
            setStagePatterns(Array.isArray(result.config.stagePatterns) ? result.config.stagePatterns : []);
            setRawJson(JSON.stringify(result.config, null, 2));
          } else {
            setPatternError('Failed to load pattern config');
          }
        }
      };
      load();
    }
  }, [activeTab]);

  const handleSavePatterns = async () => {
    setIsSavingPatterns(true);
    setPatternError(null);
    try {
      let newConfig;
      if (showRawJson) {
        try {
          newConfig = JSON.parse(rawJson);
        } catch (e) {
          setPatternError('Invalid JSON');
          setIsSavingPatterns(false);
          return;
        }
      } else {
        newConfig = {
          ...patternConfig,
          shotPatterns,
          taskPatterns,
          resolutionPatterns,
          versionPatterns,
          assetPatterns,
          stagePatterns
        };
      }
      if (window.electronAPI && window.electronAPI.savePatternConfig) {
        const result = await window.electronAPI.savePatternConfig(newConfig);
        if (result && result.success) {
          setPatternConfig(newConfig);
          setRawJson(JSON.stringify(newConfig, null, 2));
        } else {
          setPatternError('Failed to save pattern config');
        }
      }
    } catch (err) {
      setPatternError('Failed to save pattern config');
    } finally {
      setIsSavingPatterns(false);
    }
  };

  const renderArrayEditor = (label: string, arr: string[], setArr: (a: string[]) => void) => (
    <div className="pattern-editor">
      <h4>{label}</h4>
      <div className="pattern-list">
        {arr.map((pattern, idx) => (
          <div key={idx} className="pattern-item">
            <input
              type="text"
              value={pattern}
              onChange={e => {
                const copy = [...arr];
                copy[idx] = e.target.value;
                setArr(copy);
              }}
            />
            <button className="button danger small" onClick={() => setArr(arr.filter((_, i) => i !== idx))}>×</button>
          </div>
        ))}
      </div>
      <button className="button secondary small" onClick={() => setArr([...arr, ''])}>+ Add</button>
    </div>
  );

  const renderTaskPatternsEditor = () => (
    <div className="pattern-editor">
      <h4>Task Patterns</h4>
      <div className="pattern-list">
        {Object.entries(taskPatterns).map(([task, aliases], _) => (
          <div key={task} className="pattern-item">
            <input
              type="text"
              value={task}
              onChange={e => {
                const newKey = e.target.value;
                const newObj = { ...taskPatterns };
                delete newObj[task];
                newObj[newKey] = aliases;
                setTaskPatterns(newObj);
              }}
              placeholder="Task name"
              style={{ width: 100 }}
            />
            <input
              type="text"
              value={aliases.join(', ')}
              onChange={e => {
                const newObj = { ...taskPatterns };
                newObj[task] = e.target.value.split(',').map(s => s.trim());
                setTaskPatterns(newObj);
              }}
              placeholder="Aliases (comma separated)"
              style={{ width: 220 }}
            />
            <button className="button danger small" onClick={() => {
              const newObj = { ...taskPatterns };
              delete newObj[task];
              setTaskPatterns(newObj);
            }}>×</button>
          </div>
        ))}
      </div>
      <button className="button secondary small" onClick={() => setTaskPatterns({ ...taskPatterns, '': [''] })}>+ Add Task</button>
    </div>
  );

  const renderPatternsTab = () => (
    <div className="patterns-tab">
      <h3>Edit All Pattern Config</h3>
      {patternError && <div className="error-toast">{patternError}</div>}
      <button className="button small" onClick={() => setShowRawJson(v => !v)} style={{ marginBottom: 12 }}>
        {showRawJson ? 'Hide Raw JSON' : 'Show Raw JSON'}
      </button>
      {showRawJson ? (
        <textarea
          style={{ width: '100%', minHeight: 300, fontFamily: 'monospace', fontSize: 14 }}
          value={rawJson}
          onChange={e => setRawJson(e.target.value)}
        />
      ) : (
        <>
          {renderArrayEditor('Shot Patterns', shotPatterns, setShotPatterns)}
          {renderTaskPatternsEditor()}
          {renderArrayEditor('Resolution Patterns', resolutionPatterns, setResolutionPatterns)}
          {renderArrayEditor('Version Patterns', versionPatterns, setVersionPatterns)}
          {renderArrayEditor('Asset Patterns', assetPatterns, setAssetPatterns)}
          {renderArrayEditor('Stage Patterns', stagePatterns, setStagePatterns)}
        </>
      )}
      <div className="form-actions" style={{ marginTop: 16 }}>
        <button className="button" onClick={handleSavePatterns} disabled={isSavingPatterns}>Save All</button>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay">
      <div className="modal settings-modal">
        <div className="modal-header">
          <h2 className="modal-title">Settings</h2>
          <button className="close-button" onClick={() => setOpen(false)}>
            <IconX size={20} />
          </button>
        </div>
        
        <div className="modal-content">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'general' ? 'active' : ''}`}
              onClick={() => setActiveTab('general')}
            >
              General
            </button>
            <button
              className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
              onClick={() => setActiveTab('performance')}
            >
              <IconCpu size={16} />
              Performance
            </button>
            <button
              className={`tab ${activeTab === 'profiles' ? 'active' : ''}`}
              onClick={() => setActiveTab('profiles')}
            >
              Profiles
            </button>
            <button
              className={`tab ${activeTab === 'patterns' ? 'active' : ''}`}
              onClick={() => setActiveTab('patterns')}
            >
              Patterns
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'general' && renderGeneralSettings()}
            {activeTab === 'performance' && renderPerformanceSettings()}
            {activeTab === 'profiles' && (editingProfile ? renderProfileEditor() : renderProfileList())}
            {activeTab === 'patterns' && renderPatternsTab()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal; 