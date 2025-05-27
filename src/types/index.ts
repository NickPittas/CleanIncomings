export interface FileSystemNode {
  name: string;
  path: string;
  type: 'file' | 'folder' | 'sequence';
  size?: number;
  extension?: string;
  children?: FileSystemNode[];
  frame_range?: [number, number];
  frame_count?: number;
  total_size?: number;
  sequence_info?: SequenceInfo;
}

export interface SequenceInfo {
  base_name: string;
  frame_range: [number, number];
  extension: string;
  pattern: string;
  frame_count: number;
  total_size: number;
}

export interface MappingProposal {
  id: string;
  sourcePath: string;
  targetPath: string;
  status: 'auto' | 'override' | 'unmapped';
  shot?: string;
  task?: string;
  version?: string;
  resolution?: string;
  fileType?: string;
  node: FileSystemNode;
  isSequence?: boolean;
  sequenceInfo?: SequenceInfo;
  asset?: string;
  stage?: string;
}

export interface BatchOperation {
  id: string;
  batchId: string;
  oldPath: string;
  newPath: string;
  operation: 'move' | 'copy';
  timestamp: Date;
  isSequence: boolean;
  sequenceInfo?: SequenceInfo;
  fileSize: number;
  status: 'pending' | 'completed' | 'failed';
  errorMessage?: string;
}

export interface BatchProgress {
  batchId: string;
  totalOperations: number;
  completedOperations: number;
  failedOperations: number;
  progressPercentage: number;
  totalSize: number;
  processedSize: number;
  etaSeconds: number;
  status: 'running' | 'paused' | 'cancelled' | 'completed' | 'completed_with_errors' | 'failed';
  isPaused: boolean;
  isCancelled: boolean;
}

export interface SequenceValidation {
  sequenceName: string;
  expectedFrames: number;
  actualFrames: number;
  missingFrames: string[];
  validationStatus: 'complete' | 'incomplete';
  integrityPercentage: number;
}

export interface BatchValidationResult {
  batchId: string;
  sequenceCount: number;
  validations: SequenceValidation[];
  overallStatus: 'complete' | 'incomplete';
}

export interface EnhancedApplyOptions {
  mappings: MappingProposal[];
  operationType: 'move' | 'copy';
  validateSequences: boolean;
  progressCallback?: (progress: any) => void;
}

export interface UserPatterns {
  shotNames: string[];
  resolutions: string[];
  tasks: Array<{
    name: string;
    aliases: string[];
  }>;
}

export interface Profile {
  id: string;
  name: string;
  description?: string;
  vfxRootPath: string;
  userPatterns?: UserPatterns;
  shotPatterns: string[];
  taskMaps: TaskMap[];
  resolutionPatterns: string[];
  fileTypeRules: FileTypeRule[];
  versionPattern: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface TaskMap {
  regex: string;
  canonical: string;
  priority: number;
}

export interface FileTypeRule {
  extensions: string[];
  category: string;
  priority: number;
}

export interface ActionRecord {
  id: string;
  batchId: string;
  oldPath: string;
  newPath: string;
  timestamp: Date;
  operation: 'move' | 'rename' | 'copy';
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
  details?: string;
  progress?: number;
}

export interface ProgressState {
  isActive: boolean;
  current: number;
  total: number;
  percentage: number;
  currentFile?: string;
  currentFolder?: string;
  operation: 'applying' | 'validating' | 'idle';
  startTime?: number;
  estimatedTimeRemaining?: number;
  filesPerSecond?: number;
  batchId?: string;
  canPause?: boolean;
  canCancel?: boolean;
  isPaused?: boolean;
  isCancelled?: boolean;
}

export interface AppState {
  incomingTree: FileSystemNode | null;
  proposals: MappingProposal[];
  selectedProposal: MappingProposal | null;
  selectedNode: FileSystemNode | null;
  currentProfile: Profile | null;
  profiles: Profile[];
  isScanning: boolean;
  isApplying: boolean;
  progress: number;
  lastError: string | null;
  logs: LogEntry[];
  progressState: ProgressState;
  isLogWindowOpen: boolean;
}

export interface SettingsState {
  isOpen: boolean;
  activeTab: string;
}

export interface MultithreadedSettings {
  maxWorkers: number;      // Threads per file (default: 8, optimal for most cases)
  fileWorkers: number;     // Concurrent files (default: 4, good balance)
  enabled: boolean;        // Whether to use multithreaded copy
}

export interface AppSettings {
  multithreaded: MultithreadedSettings;
  autoScanOnDrop: boolean;
  showFileSizeInTree: boolean;
  enableDebugLogging: boolean;
} 