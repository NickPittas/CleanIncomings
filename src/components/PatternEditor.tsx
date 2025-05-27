import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store';

interface PatternConfig {
  shotPatterns: string[];
  taskPatterns: Record<string, string[]>;
  resolutionPatterns: string[];
  versionPatterns: string[];
  projectTypes: Record<string, Record<string, string>>;
}

const PatternEditor: React.FC = () => {
  const { addLog } = useAppStore();
  const [config, setConfig] = useState<PatternConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'shots' | 'tasks' | 'resolutions' | 'versions' | 'projects'>('shots');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const result = await (window as any).electronAPI.invoke('load-pattern-config');
      if (result.success) {
        setConfig(result.config);
        addLog('info', 'Pattern configuration loaded successfully');
      } else {
        addLog('error', 'Failed to load pattern configuration', result.error || 'Unknown error');
      }
    } catch (error: any) {
      addLog('error', 'Error loading pattern configuration', error?.message || 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;
    
    try {
      setIsSaving(true);
      const result = await (window as any).electronAPI.invoke('save-pattern-config', config);
      if (result.success) {
        addLog('success', 'Pattern configuration saved successfully');
      } else {
        addLog('error', 'Failed to save pattern configuration', result.error || 'Unknown error');
      }
    } catch (error: any) {
      addLog('error', 'Error saving pattern configuration', error?.message || 'Unknown error');
    } finally {
      setIsSaving(false);
    }
  };

  const addPattern = (type: 'shotPatterns' | 'resolutionPatterns' | 'versionPatterns', pattern: string) => {
    if (!config || !pattern.trim()) return;
    
    setConfig({
      ...config,
      [type]: [...config[type], pattern.trim()]
    });
  };

  const removePattern = (type: 'shotPatterns' | 'resolutionPatterns' | 'versionPatterns', index: number) => {
    if (!config) return;
    
    setConfig({
      ...config,
      [type]: config[type].filter((_, i) => i !== index)
    });
  };

  const addTaskPattern = (taskName: string, pattern: string) => {
    if (!config || !taskName.trim() || !pattern.trim()) return;
    
    const currentPatterns = config.taskPatterns[taskName] || [];
    setConfig({
      ...config,
      taskPatterns: {
        ...config.taskPatterns,
        [taskName]: [...currentPatterns, pattern.trim()]
      }
    });
  };

  const removeTaskPattern = (taskName: string, index: number) => {
    if (!config) return;
    
    const currentPatterns = config.taskPatterns[taskName] || [];
    setConfig({
      ...config,
      taskPatterns: {
        ...config.taskPatterns,
        [taskName]: currentPatterns.filter((_, i) => i !== index)
      }
    });
  };

  const addTask = (taskName: string) => {
    if (!config || !taskName.trim()) return;
    
    setConfig({
      ...config,
      taskPatterns: {
        ...config.taskPatterns,
        [taskName.trim()]: []
      }
    });
  };

  const removeTask = (taskName: string) => {
    if (!config) return;
    
    const { [taskName]: removed, ...rest } = config.taskPatterns;
    setConfig({
      ...config,
      taskPatterns: rest
    });
  };

  if (isLoading) {
    return (
      <div className="pattern-editor loading">
        <div className="loading-spinner">Loading pattern configuration...</div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="pattern-editor error">
        <div className="error-message">Failed to load pattern configuration</div>
        <button onClick={loadConfig} className="retry-button">Retry</button>
      </div>
    );
  }

  return (
    <div className="pattern-editor">
      <div className="pattern-editor-header">
        <h2>VFX Pattern Configuration</h2>
        <button 
          onClick={saveConfig} 
          disabled={isSaving}
          className="save-button"
        >
          {isSaving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>

      <div className="pattern-tabs">
        <button 
          className={`tab ${activeTab === 'shots' ? 'active' : ''}`}
          onClick={() => setActiveTab('shots')}
        >
          Shot Patterns
        </button>
        <button 
          className={`tab ${activeTab === 'tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          Task Patterns
        </button>
        <button 
          className={`tab ${activeTab === 'resolutions' ? 'active' : ''}`}
          onClick={() => setActiveTab('resolutions')}
        >
          Resolution Patterns
        </button>
        <button 
          className={`tab ${activeTab === 'versions' ? 'active' : ''}`}
          onClick={() => setActiveTab('versions')}
        >
          Version Patterns
        </button>
        <button 
          className={`tab ${activeTab === 'projects' ? 'active' : ''}`}
          onClick={() => setActiveTab('projects')}
        >
          Project Types
        </button>
      </div>

      <div className="pattern-content">
        {activeTab === 'shots' && (
          <PatternList
            title="Shot Name Patterns"
            patterns={config.shotPatterns}
            onAdd={(pattern) => addPattern('shotPatterns', pattern)}
            onRemove={(index) => removePattern('shotPatterns', index)}
            placeholder="e.g., DEMO\\d{4}"
          />
        )}

        {activeTab === 'tasks' && (
          <TaskPatternEditor
            taskPatterns={config.taskPatterns}
            onAddTask={addTask}
            onRemoveTask={removeTask}
            onAddPattern={addTaskPattern}
            onRemovePattern={removeTaskPattern}
          />
        )}

        {activeTab === 'resolutions' && (
          <PatternList
            title="Resolution Patterns"
            patterns={config.resolutionPatterns}
            onAdd={(pattern) => addPattern('resolutionPatterns', pattern)}
            onRemove={(index) => removePattern('resolutionPatterns', index)}
            placeholder="e.g., 4k, 1920x1080"
          />
        )}

        {activeTab === 'versions' && (
          <PatternList
            title="Version Patterns"
            patterns={config.versionPatterns}
            onAdd={(pattern) => addPattern('versionPatterns', pattern)}
            onRemove={(index) => removePattern('versionPatterns', index)}
            placeholder="e.g., v\\d{3}"
          />
        )}

        {activeTab === 'projects' && (
          <div className="project-types">
            <h3>Project Types</h3>
            <pre className="json-display">
              {JSON.stringify(config.projectTypes, null, 2)}
            </pre>
            <p className="note">
              Project types configuration is currently read-only. 
              Edit the JSON file directly if needed.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

interface PatternListProps {
  title: string;
  patterns: string[];
  onAdd: (pattern: string) => void;
  onRemove: (index: number) => void;
  placeholder: string;
}

const PatternList: React.FC<PatternListProps> = ({ title, patterns, onAdd, onRemove, placeholder }) => {
  const [newPattern, setNewPattern] = useState('');

  const handleAdd = () => {
    if (newPattern.trim()) {
      onAdd(newPattern);
      setNewPattern('');
    }
  };

  return (
    <div className="pattern-list">
      <h3>{title}</h3>
      <div className="add-pattern">
        <input
          type="text"
          value={newPattern}
          onChange={(e) => setNewPattern(e.target.value)}
          placeholder={placeholder}
          onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
        />
        <button onClick={handleAdd}>Add</button>
      </div>
      <div className="patterns">
        {patterns.map((pattern, index) => (
          <div key={index} className="pattern-item">
            <code>{pattern}</code>
            <button onClick={() => onRemove(index)} className="remove-button">×</button>
          </div>
        ))}
      </div>
    </div>
  );
};

interface TaskPatternEditorProps {
  taskPatterns: Record<string, string[]>;
  onAddTask: (taskName: string) => void;
  onRemoveTask: (taskName: string) => void;
  onAddPattern: (taskName: string, pattern: string) => void;
  onRemovePattern: (taskName: string, index: number) => void;
}

const TaskPatternEditor: React.FC<TaskPatternEditorProps> = ({
  taskPatterns,
  onAddTask,
  onRemoveTask,
  onAddPattern,
  onRemovePattern
}) => {
  const [newTaskName, setNewTaskName] = useState('');
  const [newPatterns, setNewPatterns] = useState<Record<string, string>>({});

  const handleAddTask = () => {
    if (newTaskName.trim()) {
      onAddTask(newTaskName);
      setNewTaskName('');
    }
  };

  const handleAddPattern = (taskName: string) => {
    const pattern = newPatterns[taskName];
    if (pattern?.trim()) {
      onAddPattern(taskName, pattern);
      setNewPatterns({ ...newPatterns, [taskName]: '' });
    }
  };

  return (
    <div className="task-pattern-editor">
      <h3>Task Patterns</h3>
      
      <div className="add-task">
        <input
          type="text"
          value={newTaskName}
          onChange={(e) => setNewTaskName(e.target.value)}
          placeholder="New task name (e.g., comp, vfx)"
          onKeyPress={(e) => e.key === 'Enter' && handleAddTask()}
        />
        <button onClick={handleAddTask}>Add Task</button>
      </div>

      <div className="task-groups">
        {Object.entries(taskPatterns).map(([taskName, patterns]) => (
          <div key={taskName} className="task-group">
            <div className="task-header">
              <h4>{taskName}</h4>
              <button onClick={() => onRemoveTask(taskName)} className="remove-task-button">
                Remove Task
              </button>
            </div>
            
            <div className="add-pattern">
              <input
                type="text"
                value={newPatterns[taskName] || ''}
                onChange={(e) => setNewPatterns({ ...newPatterns, [taskName]: e.target.value })}
                placeholder="Add pattern (e.g., composite, final)"
                onKeyPress={(e) => e.key === 'Enter' && handleAddPattern(taskName)}
              />
              <button onClick={() => handleAddPattern(taskName)}>Add</button>
            </div>
            
            <div className="patterns">
              {patterns.map((pattern, index) => (
                <div key={index} className="pattern-item">
                  <span>{pattern}</span>
                  <button onClick={() => onRemovePattern(taskName, index)} className="remove-button">×</button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PatternEditor; 