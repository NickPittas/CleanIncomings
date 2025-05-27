// Global type definitions

export interface MappingProposal {
  id: string;
  node: {
    name: string;
    path: string;
    type: 'file' | 'folder';
    [key: string]: any;
  };
  destinationPath: string;
  status: 'auto' | 'override' | 'unmapped';
  reason?: string;
  meta?: {
    shot?: string;
    task?: string;
    version?: string;
    resolution?: string;
    [key: string]: any;
  };
}

export interface Profile {
  id: string;
  name: string;
  description?: string;
  vfxRootPath: string;
  structure: any;
  patterns: {
    shotPatterns: string[];
    taskPatterns: Record<string, string[]>;
    resolutionPatterns: string[];
    [key: string]: any;
  };
}

// Define the global Window interface to include electronAPI
declare global {
  interface Window {
    electronAPI: {
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
  }
} 