// @ts-ignore
import { create } from 'zustand';
import { AppState, SettingsState, Profile, MappingProposal, LogEntry, ProgressState, AppSettings, MultithreadedSettings } from '../types';

// Default profiles based on patterns.json
const createDefaultProfiles = (): Profile[] => {
  return [
    {
      id: 'normal-internal-2024',
      name: 'Normal Internal Project',
      description: 'Standard internal VFX project structure with department-based organization',
      vfxRootPath: '/vfx/projects/normal',
      userPatterns: {
        shotNames: [
          // Only use shot names that exist in patterns.json or are generic patterns
          'shot_001', 'shot_002', 'shot_003', 'shot_010', 'shot_020', 'shot_030',
          'sh001', 'sh002', 'sh003', 'sequence_01', 'seq01', 'hero_shot', 'finale'
        ],
        resolutions: [
          // Only use resolutions from patterns.json
          '2k', '4k', '8k', '6k', 'uhd', 'hd', '1920x1080', '3840x2160', '1080p', '720p', '480p'
        ],
        tasks: [
          { name: 'comp', aliases: ['comp', 'composite', 'final', 'nuke'] },
          { name: 'render', aliases: ['render', 'beauty', 'rgb', 'main'] },
          { name: 'plate', aliases: ['plate', 'bg', 'background', 'source'] },
          { name: 'roto', aliases: ['roto', 'rotoscope', 'matte'] },
          { name: 'paint', aliases: ['paint', 'cleanup', 'wire_removal'] },
          { name: 'track', aliases: ['track', 'matchmove', 'camera', 'tracking'] },
          { name: 'fx', aliases: ['fx', 'effects', 'sim', 'simulation'] },
          { name: 'light', aliases: ['light', 'lighting', 'lookdev'] },
          { name: 'anim', aliases: ['anim', 'animation', '3d'] },
          { name: 'ae', aliases: ['ae', 'aftereffects', 'motion'] },
          { name: 'premiere', aliases: ['premiere', 'edit', 'cutting'] },
          { name: 'davinci', aliases: ['davinci', 'color', 'grade'] }
        ]
      },
      shotPatterns: [
        '(?i)(?:shot_?)?(\d{3,4})',
        '(?i)sh_?(\d{3,4})',
        '(?i)s(\d{3,4})',
        '(?i)sequence_?(\d{2})',
        '(?i)seq(\d{2})',
        '(?i)(hero_shot|finale)'
      ],
      taskMaps: [
        { regex: '(?i)(comp|composite|final|nuke)', canonical: 'comp', priority: 10 },
        { regex: '(?i)(render|beauty|rgb|main)', canonical: 'render', priority: 9 },
        { regex: '(?i)(plate|bg|background|source)', canonical: 'plate', priority: 8 },
        { regex: '(?i)(roto|rotoscope|matte)', canonical: 'roto', priority: 7 },
        { regex: '(?i)(paint|cleanup|wire_removal)', canonical: 'paint', priority: 6 },
        { regex: '(?i)(track|matchmove|camera|tracking)', canonical: 'track', priority: 5 },
        { regex: '(?i)(fx|effects|sim|simulation)', canonical: 'fx', priority: 4 },
        { regex: '(?i)(light|lighting|lookdev)', canonical: 'light', priority: 3 },
        { regex: '(?i)(anim|animation|3d)', canonical: 'anim', priority: 2 },
        { regex: '(?i)(ae|aftereffects|motion)', canonical: 'ae', priority: 2 },
        { regex: '(?i)(premiere|edit|cutting)', canonical: 'premiere', priority: 2 },
        { regex: '(?i)(davinci|color|grade)', canonical: 'davinci', priority: 2 }
      ],
      resolutionPatterns: [
        '(?i)(\d{3,4}k)',
        '(?i)(\d{3,4}x\d{3,4})',
        '(?i)(uhd|hd|sd)',
        '(?i)(proxy|full_res|half_res|quarter_res)',
        '(?i)(\d{3,4}p)'
      ],
      fileTypeRules: [
        { extensions: ['.exr', '.dpx', '.tiff', '.tif', '.hdr'], category: 'render', priority: 10 },
        { extensions: ['.mov', '.mp4', '.avi', '.mkv', '.r3d', '.braw'], category: 'video', priority: 9 },
        { extensions: ['.nk', '.hip', '.ma', '.mb', '.blend', '.c4d', '.aep', '.prproj'], category: 'project', priority: 8 },
        { extensions: ['.abc', '.bgeo', '.vdb', '.ass', '.usd'], category: 'cache', priority: 7 },
        { extensions: ['.jpg', '.jpeg', '.png', '.psd', '.ai'], category: 'image', priority: 6 }
      ],
      versionPattern: 'v\\d{3}',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date()
    },
    {
      id: 'sphere-project-2024',
      name: 'Sphere Project Structure',
      description: 'Specialized workflow for Sphere projects with numbered pipeline stages',
      vfxRootPath: '/vfx/projects/sphere',
      userPatterns: {
        shotNames: [
          // Only use shot names from patterns.json
          'OLNT0010', 'KITC0010', 'WTFB0010', 'IGB0010', 'SOME0010'
        ],
        resolutions: [
          // Only use resolutions from patterns.json
          '2k', '4k', '8k', '6k', 'uhd', 'hd', '1920x1080', '3840x2160', '1080p', '720p', '480p'
        ],
        tasks: [
          { name: 'plates', aliases: ['plates', 'plate', 'source', '01_plates'] },
          { name: 'support', aliases: ['support', 'reference', '02_support'] },
          { name: 'references', aliases: ['references', 'ref', '03_references'] },
          { name: 'vfx', aliases: ['vfx', 'effects', '04_vfx'] },
          { name: 'comp', aliases: ['comp', 'composite', '05_comp'] },
          { name: 'mograph', aliases: ['mograph', 'motion', '06_mograph'] },
          { name: 'shared', aliases: ['shared', 'assets', '07_shared'] },
          { name: 'output', aliases: ['output', 'delivery', 'final', '08_output'] },
          { name: 'project', aliases: ['project', 'nuke', 'script'] },
          { name: 'render', aliases: ['render', 'beauty', 'rgb'] },
          { name: 'main_arch', aliases: ['main_arch', 'main', 'arch', 'architecture'] },
          { name: 'depth', aliases: ['depth', 'z', 'zdepth'] },
          { name: 'previz', aliases: ['previz', 'previs', 'preview', 'PREVIZ'] },
          { name: 'multipass', aliases: ['multipass', 'multi', 'pass', 'Multipass'] }
        ]
      },
      shotPatterns: [
        '(?i)(DEMO\d{4})',
        '(?i)(FULL\d{4})',
        '(?i)(ANOT\d{4})',
        '(?i)(DEMO)',
        '(?i)(FULL)',
        '(?i)(ANOT)',
        '(?i)(\d{4})'
      ],
      taskMaps: [
        { regex: '(?i)(01_plates|plates|plate|source)', canonical: 'plates', priority: 10 },
        { regex: '(?i)(02_support|support|reference)', canonical: 'support', priority: 9 },
        { regex: '(?i)(03_references|references|ref)', canonical: 'references', priority: 8 },
        { regex: '(?i)(04_vfx|vfx|effects)', canonical: 'vfx', priority: 7 },
        { regex: '(?i)(05_comp|comp|composite)', canonical: 'comp', priority: 6 },
        { regex: '(?i)(06_mograph|mograph|motion)', canonical: 'mograph', priority: 5 },
        { regex: '(?i)(07_shared|shared|assets)', canonical: 'shared', priority: 4 },
        { regex: '(?i)(08_output|output|delivery|final)', canonical: 'output', priority: 3 },
        { regex: '(?i)(project|nuke|script)', canonical: 'project', priority: 2 },
        { regex: '(?i)(render|beauty|rgb)', canonical: 'render', priority: 2 }
      ],
      resolutionPatterns: [
        '(?i)(proxy)',
        '(?i)(full_res)',
        '(?i)(\d{3,4}k)',
        '(?i)(\d{3,4}x\d{3,4})',
        '(?i)(uhd|hd)',
        '(?i)(half_res|quarter_res)',
        '(?i)(preview|delivery)'
      ],
      fileTypeRules: [
        { extensions: ['.exr', '.dpx', '.tiff', '.tif', '.hdr'], category: 'render', priority: 10 },
        { extensions: ['.mov', '.mp4', '.avi', '.mkv', '.r3d', '.braw'], category: 'video', priority: 9 },
        { extensions: ['.nk', '.hip', '.ma', '.mb', '.blend', '.c4d', '.aep'], category: 'project', priority: 8 },
        { extensions: ['.abc', '.bgeo', '.vdb', '.ass', '.usd'], category: 'cache', priority: 7 },
        { extensions: ['.jpg', '.jpeg', '.png', '.psd', '.ai'], category: 'image', priority: 6 }
      ],
      versionPattern: 'v\\d{3}',
      isActive: false,
      createdAt: new Date(),
      updatedAt: new Date()
    }
  ];
};

const createInitialProgressState = (): ProgressState => ({
  isActive: false,
  current: 0,
  total: 0,
  percentage: 0,
  operation: 'idle',
  startTime: undefined,
  estimatedTimeRemaining: undefined,
  filesPerSecond: undefined,
  currentFile: undefined,
  currentFolder: undefined
});

const createDefaultAppSettings = (): AppSettings => ({
  multithreaded: {
    maxWorkers: 8,      // Optimal for most cases
    fileWorkers: 4,     // Good balance
    enabled: true       // Enable by default for better performance
  },
  autoScanOnDrop: true,
  showFileSizeInTree: true,
  enableDebugLogging: false
});

interface AppStoreType extends AppState {
  scanFolderPath: string | null;
  setScanFolderPath: (path: string) => void;
  appSettings: AppSettings;
  setAppSettings: (settings: AppSettings) => void;
  updateMultithreadedSettings: (settings: Partial<MultithreadedSettings>) => void;
  // Actions
  setIncomingTree: (tree: AppState['incomingTree']) => void;
  setProposals: (proposals: AppState['proposals']) => void;
  setSelectedProposal: (proposal: AppState['selectedProposal']) => void;
  setSelectedNode: (node: AppState['selectedNode']) => void;
  setCurrentProfile: (profile: AppState['currentProfile']) => void;
  addProfile: (profile: Profile) => void;
  updateProfile: (id: string, profile: Profile) => void;
  deleteProfile: (id: string) => void;
  setIsScanning: (isScanning: boolean) => void;
  setIsApplying: (isApplying: boolean) => void;
  setProgress: (progress: number) => void;
  setLastError: (error: string | null) => void;
  updateProposal: (id: string, updates: Partial<MappingProposal>) => void;
  batchUpdateProposals: (ids: string[], asset: string, stage: string) => void;
  // Logging methods
  addLog: (level: LogEntry['level'], message: string, details?: string) => void;
  clearLogs: () => void;
  setLogWindowOpen: (isOpen: boolean) => void;
  // Progress tracking methods
  startProgress: (operation: ProgressState['operation'], total: number, batchId?: string) => void;
  updateProgress: (current: number, currentFile?: string, currentFolder?: string) => void;
  finishProgress: () => void;
  calculateETA: () => void;
  destinationRoot: string;
  setDestinationRoot: (newRoot: string) => void;
  selectedProposalIds: string[];
  setSelectedProposalIds: (ids: string[]) => void;
  selectAllProposals: () => void;
  selectNoneProposals: () => void;
}

export const useAppStore = create<AppStoreType>((set, get) => {
  const defaultProfiles = createDefaultProfiles();
  let logIdCounter = 0; // Add counter for unique log IDs
  
  return {
    // Initial state
    incomingTree: null,
    proposals: [],
    selectedProposal: null,
    selectedNode: null,
    currentProfile: defaultProfiles[0], // Automatically select first profile
    profiles: defaultProfiles,
    isScanning: false,
    isApplying: false,
    progress: 0,
    lastError: null,
    logs: [],
    progressState: createInitialProgressState(),
    isLogWindowOpen: false,
    destinationRoot: defaultProfiles[0].vfxRootPath,
    scanFolderPath: null,
    selectedProposalIds: [],
    appSettings: createDefaultAppSettings(),

    // Actions
    setIncomingTree: (tree) => set({ incomingTree: tree }),
    setProposals: (proposals) => set({ proposals }),
    setSelectedProposal: (proposal) => set({ selectedProposal: proposal }),
    setSelectedNode: (node) => set({ selectedNode: node }),
    setCurrentProfile: (profile) => set({ currentProfile: profile }),
    addProfile: (profile) => set((state) => ({ 
      profiles: [...state.profiles, profile] 
    })),
    updateProfile: (id, profile) => set((state) => ({
      profiles: state.profiles.map(p => p.id === id ? profile : p),
      currentProfile: state.currentProfile?.id === id ? profile : state.currentProfile
    })),
    deleteProfile: (id) => set((state) => ({
      profiles: state.profiles.filter(p => p.id !== id),
      currentProfile: state.currentProfile?.id === id ? null : state.currentProfile
    })),
    setIsScanning: (isScanning) => set({ isScanning }),
    setIsApplying: (isApplying) => set({ isApplying }),
    setProgress: (progress) => set({ progress }),
    setLastError: (error) => set({ lastError: error }),
    updateProposal: (id, updates) => set((state) => ({
      proposals: state.proposals.map(p => p.id === id ? { ...p, ...updates } : p)
    })),
    setScanFolderPath: (path) => set({ scanFolderPath: path }),
    setDestinationRoot: async (newRoot) => {
      const state = get();
      const { incomingTree, currentProfile, addLog, setProposals } = state;
      set({ destinationRoot: newRoot });
      if (!incomingTree || !currentProfile) {
        if (addLog) addLog('warning', 'No tree or profile', 'Cannot update mappings without a scan and profile.');
        return;
      }
      try {
        if (addLog) addLog('info', 'Destination root changed', `Regenerating mappings for new root: ${newRoot}`);
        // Call backend mapping generator with new root
        const proposals = await window.electronAPI.generateMapping(incomingTree, {
          ...currentProfile,
          vfxRootPath: newRoot
        });
        setProposals(Array.isArray(proposals) ? proposals : []);
        if (addLog) addLog('success', 'Mappings regenerated', `Proposals updated for new root: ${newRoot}`);
      } catch (err) {
        if (addLog) addLog('error', 'Failed to regenerate mappings', err instanceof Error ? err.message : String(err));
      }
    },
    batchUpdateProposals: async (ids: string[], asset: string, stage: string) => {
      const state = get();
      const { proposals, currentProfile, addLog, setProposals } = state;
      if (!currentProfile) {
        addLog && addLog('warning', 'No profile', 'Cannot batch update without a profile.');
        return;
      }
      // Update asset/stage for selected proposals
      const updated = proposals.map(p => {
        if (!ids.includes(p.id)) return p;
        // Recompute targetPath by calling backend mapping generator for this mapping
        // For now, update in-place and mark as override
        return {
          ...p,
          asset: asset || p.asset,
          stage: stage || p.stage,
          status: 'override' as 'override',
        } as MappingProposal;
      });
      setProposals(updated);
      addLog && addLog('info', 'Batch Edit', `Updated asset/stage for ${ids.length} mappings.`);
    },

    // Logging methods
    addLog: (level, message, details) => {
      const log: LogEntry = {
        id: `${Date.now()}-${++logIdCounter}`, // Use timestamp + counter for unique IDs
        timestamp: new Date(),
        level,
        message,
        details
      };
      
      set((state) => ({
        logs: [...state.logs, log].slice(-1000) // Keep last 1000 logs
      }));
    },
    clearLogs: () => set({ logs: [] }),
    setLogWindowOpen: (isOpen) => set({ isLogWindowOpen: isOpen }),

    // Progress tracking methods
    startProgress: (operation, total, batchId?: string) => {
      set({
        progressState: {
          isActive: true,
          current: 0,
          total,
          percentage: 0,
          operation,
          startTime: Date.now(),
          estimatedTimeRemaining: undefined,
          filesPerSecond: undefined,
          currentFile: undefined,
          currentFolder: undefined,
          batchId
        }
      });
    },

    updateProgress: (current: number, currentFile?: string, currentFolder?: string) =>
      set((state) => {
        const total = state.progressState.total;
        const percentage = total > 0 ? (current / total) * 100 : 0;
        return {
          progressState: {
            ...state.progressState,
            current,
            percentage,
            currentFile,
            currentFolder
          }
        };
      }),

    finishProgress: () => {
      set({
        progressState: createInitialProgressState()
      });
    },

    calculateETA: () => {
      const state = get();
      const { progressState } = state;
      
      if (!progressState.isActive || !progressState.startTime || progressState.current === 0) {
        return;
      }
      
      const now = Date.now();
      const elapsed = (now - progressState.startTime) / 1000;
      const rate = progressState.current / elapsed;
      const remaining = progressState.total - progressState.current;
      const eta = remaining / rate;
      
      set({
        progressState: {
          ...progressState,
          estimatedTimeRemaining: eta,
          filesPerSecond: rate
        }
      });
    },

    setSelectedProposalIds: (ids) => set({ selectedProposalIds: ids }),
    selectAllProposals: () => {
      const proposals = get().proposals || [];
      set({ selectedProposalIds: proposals.map(p => p.id) });
    },
    selectNoneProposals: () => set({ selectedProposalIds: [] }),

    setAppSettings: (settings) => set({ appSettings: settings }),
    updateMultithreadedSettings: (settings) => set((state) => ({
      appSettings: {
        ...state.appSettings,
        multithreaded: {
          ...state.appSettings.multithreaded,
          ...settings
        }
      }
    })),
  };
});

export const useSettingsStore = create<SettingsState & {
  setOpen: (isOpen: boolean) => void;
  setActiveTab: (tab: string) => void;
}>((set) => ({
  isOpen: false,
  activeTab: 'general',
  setOpen: (isOpen) => set({ isOpen }),
  setActiveTab: (activeTab) => set({ activeTab }),
})); 