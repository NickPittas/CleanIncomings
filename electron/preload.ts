import { contextBridge, ipcRenderer } from 'electron';

export interface ElectronAPI {
  selectFolder: () => Promise<string | null>;
  scanFolder: (folderPath: string) => Promise<any>;
  scanFolderWithProgress: (folderPath: string) => Promise<{ batchId: string }>;
  getScanProgress: (batchId: string) => Promise<any>;
  generateMapping: (tree: any, profile: any) => Promise<any>;
  applyMappings: (mappings: any[]) => Promise<any>;
  applyMappingsEnhanced: (data: any) => Promise<any>;
  getProgress: (batchId: string) => Promise<any>;
  pauseOperations: () => Promise<any>;
  resumeOperations: () => Promise<any>;
  cancelOperations: () => Promise<any>;
  cancelOperation: (batchId: string) => Promise<any>;
  validateSequences: (batchId: string) => Promise<any>;
  undoLastBatch: () => Promise<any>;
  processDroppedFiles: (filePaths: string[]) => Promise<string | null>;
  loadPatternConfig: () => Promise<any>;
  savePatternConfig: (config: any) => Promise<any>;
  getWebSocketPort: () => Promise<number | null>;
  cancelScan: (batchId: string) => Promise<any>;
}

const electronAPI: ElectronAPI = {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  scanFolder: (folderPath: string) => ipcRenderer.invoke('python-scan-folder', folderPath),
  scanFolderWithProgress: (folderPath: string) => ipcRenderer.invoke('python-scan-folder-with-progress', folderPath),
  getScanProgress: (batchId: string) => ipcRenderer.invoke('python-get-scan-progress', batchId),
  generateMapping: (tree: any, profile: any) => ipcRenderer.invoke('python-generate-mapping', tree, profile),
  applyMappings: (mappings: any[]) => ipcRenderer.invoke('python-apply-mappings', mappings),
  applyMappingsEnhanced: (data: any) => ipcRenderer.invoke('python-apply-mappings-enhanced', data),
  getProgress: (batchId: string) => ipcRenderer.invoke('python-get-progress', batchId),
  pauseOperations: () => ipcRenderer.invoke('python-pause-operations'),
  resumeOperations: () => ipcRenderer.invoke('python-resume-operations'),
  cancelOperations: () => ipcRenderer.invoke('python-cancel-operations'),
  cancelOperation: (batchId: string) => ipcRenderer.invoke('python-cancel-operation', batchId),
  validateSequences: (batchId: string) => ipcRenderer.invoke('python-validate-sequences', batchId),
  undoLastBatch: () => ipcRenderer.invoke('python-undo-last-batch'),
  processDroppedFiles: (filePaths: string[]) => ipcRenderer.invoke('process-dropped-files', filePaths),
  loadPatternConfig: () => ipcRenderer.invoke('load-pattern-config'),
  savePatternConfig: (config: any) => ipcRenderer.invoke('save-pattern-config', config),
  getWebSocketPort: () => ipcRenderer.invoke('python-get-websocket-port'),
  cancelScan: (batchId: string) => ipcRenderer.invoke('python-cancel-scan', batchId),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI); 