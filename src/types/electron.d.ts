/**
 * TypeScript declarations for Electron API
 */

interface ElectronAPI {
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

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {}; 