import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import { join } from 'path';
import { spawn } from 'child_process';
import { isDev } from './utils';
import * as fs from 'fs';
import * as path from 'path';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import * as http from 'http';
import { startWebSocketServer, stopWebSocketServer, getWebSocketPort, sendProgressUpdate, getServerStatus } from './websocket-server';

let mainWindow: BrowserWindow | null = null;

async function createWindow(): Promise<void> {
  console.log('🪟 Creating BrowserWindow...');
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js'),
      webSecurity: false,
    },
    titleBarStyle: 'default',
    show: true, // Show immediately
    alwaysOnTop: true, // Force to front
  });
  
  console.log('🪟 BrowserWindow created, should be visible now');
  
  // Add error handling for preload script
  mainWindow.webContents.on('preload-error', (event, preloadPath, error) => {
    console.error('❌ Preload script error:', error);
  });
  
  // Force show window after a delay regardless of load status
  setTimeout(() => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.setAlwaysOnTop(false); // Remove always on top after showing
      console.log('🪟 Window force-shown after delay');
    }
  }, 2000);

  if (isDev) {
    let viteUrl = 'http://localhost:3001'; // Default fallback
    
    try {
      // Try to read the port from Vite's port file
      const portFilePath = join(__dirname, '../.vite-port');
      if (existsSync(portFilePath)) {
        const portData = JSON.parse(readFileSync(portFilePath, 'utf8'));
        viteUrl = portData.url || `http://localhost:${portData.port}`;
        console.log(`📖 Read Vite URL from port file: ${viteUrl}`);
        
        // Add small delay to ensure Vite is fully ready
        console.log('⏳ Waiting for Vite server to be ready...');
        await new Promise(resolve => setTimeout(resolve, 1000));
      } else {
        console.log('📄 No .vite-port file found, using default port 3001');
        // Add delay even for default port
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (error) {
      console.error('❌ Error reading Vite port file:', error);
    }
    
        // Load the URL directly
    console.log(`🔗 Loading: ${viteUrl}`);
    
    try {
      await mainWindow.loadURL(viteUrl);
      console.log(`✅ Successfully loaded: ${viteUrl}`);
      
      // Force show the window after successful load
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.show();
          mainWindow.focus();
          console.log('🪟 Window forced to show and focus');
        }
      }, 500);
      
    } catch (error) {
      console.error(`❌ Failed to load ${viteUrl}:`, error);
      // Simple fallback
      try {
        await mainWindow.loadURL('http://localhost:3001');
        console.log('🔄 Fallback to default port successful');
        
        // Force show window for fallback too
        setTimeout(() => {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.show();
            mainWindow.focus();
            console.log('🪟 Fallback window forced to show');
          }
        }, 500);
        
      } catch (fallbackError) {
        console.error('💥 Complete failure:', fallbackError);
      }
    }
    
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  // Window shows immediately now

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle file drops at the OS level
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.protocol === 'file:') {
      event.preventDefault();
    }
  });

  // Enable file drops
  mainWindow.webContents.on('dom-ready', () => {
    mainWindow?.webContents.executeJavaScript(`
      document.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const files = Array.from(e.dataTransfer.files);
        const filePaths = files.map(file => file.path).filter(Boolean);
        
        if (filePaths.length > 0) {
          window.electronAPI.processDroppedFiles(filePaths).then(folderPath => {
            if (folderPath) {
              // Trigger a custom event that the React app can listen to
              window.dispatchEvent(new CustomEvent('electron-folder-dropped', { 
                detail: { folderPath } 
              }));
            }
          });
        }
      });
      
      document.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    `);
  });

  // Start built-in WebSocket server for progress updates
  try {
    console.log('[ELECTRON] Starting built-in WebSocket server...');
    const result = startWebSocketServer();
    if (result.running) {
      console.log(`[ELECTRON] WebSocket server started successfully on port ${result.port}`);
      
      // Set up file watcher for progress updates
      setupProgressFileWatcher();
    } else {
      console.error('[ELECTRON] Failed to start WebSocket server');
    }
  } catch (e) {
    console.error('[ELECTRON] Error starting WebSocket server:', e);
  }
}

app.whenReady().then(async () => {
  await createWindow();

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for Python bridge
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openDirectory'],
    title: 'Select Folder to Normalize',
  });
  
  return result.canceled ? null : result.filePaths[0];
});

// Handle dropped files/folders
ipcMain.handle('process-dropped-files', async (_, filePaths: string[]) => {
  const fs = require('fs');
  const path = require('path');
  
  console.log('[ELECTRON] Processing dropped files:', filePaths);
  
  // First, check if any of the dropped items is a directory
  for (const filePath of filePaths) {
    try {
      const stats = fs.statSync(filePath);
      if (stats.isDirectory()) {
        console.log('[ELECTRON] Found directory:', filePath);
        return filePath; // Return the first directory found
      }
    } catch (error) {
      console.error('[ELECTRON] Error checking dropped file:', filePath, error);
    }
  }
  
  // If no directories found, try to get parent directory of first file
  if (filePaths.length > 0) {
    try {
      const firstPath = filePaths[0];
      const stats = fs.statSync(firstPath);
      
      if (stats.isFile()) {
        const parentDir = path.dirname(firstPath);
        console.log('[ELECTRON] No directory found, using parent of file:', parentDir);
        
        // Verify parent directory exists and is accessible
        const parentStats = fs.statSync(parentDir);
        if (parentStats.isDirectory()) {
          return parentDir;
        }
      }
    } catch (error) {
      console.error('[ELECTRON] Error getting parent directory:', error);
    }
  }
  
  console.log('[ELECTRON] No valid folder path found from dropped files');
  return null; // No directories found
});

ipcMain.handle('python-scan-folder', async (_, folderPath: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    console.log('Python scan - isDev:', isDev);
    console.log('Python path:', pythonPath);
    console.log('Folder path:', folderPath);
    console.log('Command:', 'py', [pythonPath, 'scan', folderPath]);
    
    const python = spawn('py', [pythonPath, 'scan', folderPath]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      const chunk = data.toString();
      console.log('Python stdout chunk:', chunk.substring(0, 200) + (chunk.length > 200 ? '...' : ''));
      output += chunk;
    });

    python.stderr.on('data', (data) => {
      const chunk = data.toString();
      console.log('Python stderr:', chunk);
      error += chunk;
    });

    python.on('close', (code) => {
      console.log('Python process closed with code:', code);
      console.log('Output:', output);
      console.log('Error:', error);
      console.log('Output length:', output.length);
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          console.log('Successfully parsed result:', result);
          resolve(result);
        } catch (e) {
          console.error('Failed to parse JSON:', e);
          console.error('Raw output was:', output);
          reject(new Error(`Failed to parse Python output: ${e}. Output: ${output}`));
        }
      } else {
        console.error('Python process failed with code:', code);
        console.error('Error output:', error);
        reject(new Error(`Python process failed with code ${code}: ${error || output}`));
      }
    });

    python.on('error', (err) => {
      console.error('Python process spawn error:', err);
      reject(new Error(`Failed to start Python process: ${err.message}`));
    });

    // Add timeout to prevent hanging
    setTimeout(() => {
      if (!python.killed) {
        console.log('Killing Python process due to timeout');
        python.kill();
        reject(new Error('Python process timeout after 180 seconds'));
      }
    }, 180000); // 3 minutes timeout
  });
});

ipcMain.handle('python-generate-mapping', async (_, tree: any, profile: any) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    console.log('Python mapping - isDev:', isDev);
    console.log('Python path:', pythonPath);
    console.log('Profile:', profile?.name);
    console.log('Command:', 'py', [pythonPath, 'map']);
    
    // Debug the tree being sent
    console.log('Tree being sent to Python:');
    console.log('  Tree type:', typeof tree);
    console.log('  Tree keys:', tree ? Object.keys(tree) : 'null/undefined');
    console.log('  Tree name:', tree?.name || 'NO NAME');
    console.log('  Tree type field:', tree?.type || 'NO TYPE');
    console.log('  Tree children count:', tree?.children?.length || 0);
    
    if (tree?.children && tree.children.length > 0) {
      console.log('  First few children:');
      for (let i = 0; i < Math.min(3, tree.children.length); i++) {
        const child = tree.children[i];
        console.log(`    Child ${i+1}: ${child?.name || 'NO NAME'} (type: ${child?.type || 'NO TYPE'}, children: ${child?.children?.length || 0})`);
      }
    }
    
    // Check if tree has the expected structure
    if (!tree || typeof tree !== 'object') {
      console.error('ERROR: Tree is not a valid object!');
      resolve([]);
      return;
    }
    
    if (!tree.name || !tree.type) {
      console.error('ERROR: Tree missing required fields (name, type)!');
      console.log('Tree object:', JSON.stringify(tree, null, 2).substring(0, 500) + '...');
      resolve([]);
      return;
    }
    
    const python = spawn('py', [pythonPath, 'map']);
    let output = '';
    let error = '';

    const inputData = JSON.stringify({ tree, profile });
    console.log('Input data size:', inputData.length, 'characters');
    console.log('Input data preview:', inputData.substring(0, 500) + '...');
    
    python.stdin.write(inputData);
    python.stdin.end();

    python.stdout.on('data', (data) => {
      const chunk = data.toString();
      console.log('Python mapping stdout chunk:', chunk.substring(0, 200) + (chunk.length > 200 ? '...' : ''));
      output += chunk;
    });

    python.stderr.on('data', (data) => {
      const chunk = data.toString();
      console.log('Python mapping stderr:', chunk);
      error += chunk;
    });

    python.on('close', (code) => {
      console.log('Python mapping process closed with code:', code);
      console.log('Mapping output length:', output.length);
      console.log('Mapping error length:', error.length);
      
      if (code === 0) {
        try {
          // Clean the output - remove any stderr messages that might be mixed in
          const lines = output.split('\n');
          let jsonStart = -1;
          
          // Find the start of JSON output
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim().startsWith('{')) {
              jsonStart = i;
              break;
            }
          }
          
          if (jsonStart === -1) {
            console.error('No JSON output found in mapping result');
            resolve([]); // Return empty array instead of rejecting
            return;
          }
          
          // Extract JSON from the found start point
          const jsonOutput = lines.slice(jsonStart).join('\n').trim();
          console.log('Attempting to parse mapping JSON from line', jsonStart);
          console.log('Mapping JSON output preview:', jsonOutput.substring(0, 200) + '...');
          
          const result = JSON.parse(jsonOutput);
          console.log('Successfully parsed mapping JSON result');
          console.log('Mapping result keys:', Object.keys(result));
          
          // Ensure we return the mappings array
          const mappings = result.mappings || result || [];
          console.log('Returning mappings array with length:', Array.isArray(mappings) ? mappings.length : 'not an array');
          
          resolve(Array.isArray(mappings) ? mappings : []);
        } catch (e) {
          console.error('Mapping JSON parse error:', e);
          console.log('Raw mapping output preview:', output.substring(0, 1000));
          resolve([]); // Return empty array instead of rejecting
        }
      } else {
        console.error('Python mapping process failed with code:', code);
        console.error('Mapping error output:', error);
        resolve([]); // Return empty array instead of rejecting
      }
    });

    python.on('error', (err) => {
      console.error('Python mapping process spawn error:', err);
      resolve([]); // Return empty array instead of rejecting
    });

    // Add timeout to prevent hanging
    setTimeout(() => {
      if (!python.killed) {
        console.log('Killing Python mapping process due to timeout');
        python.kill();
        resolve([]); // Return empty array instead of rejecting
      }
    }, 120000); // 2 minutes timeout
  });
});

ipcMain.handle('python-apply-mappings', async (_, mappings: any[]) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'apply']);
    let output = '';
    let error = '';

    python.stdin.write(JSON.stringify(mappings));
    python.stdin.end();

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Enhanced apply mappings with options
ipcMain.handle('python-apply-mappings-enhanced', async (_, data: any) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    console.log('[ELECTRON] Starting python-apply-mappings-enhanced');
    console.log('[ELECTRON] Data keys:', Object.keys(data));
    console.log('[ELECTRON] Operation type:', data.operation_type);
    console.log('[ELECTRON] Number of mappings:', data.mappings?.length);
    
    const python = spawn('py', [pythonPath, 'apply']);
    let output = '';
    let error = '';

    // Send enhanced data format with options
    python.stdin.write(JSON.stringify(data));
    python.stdin.end();

    python.stdout.on('data', (data) => {
      const chunk = data.toString();
      console.log('[PYTHON STDOUT]', chunk);
      output += chunk;
    });

    python.stderr.on('data', (data) => {
      const chunk = data.toString();
      console.log('[PYTHON STDERR]', chunk);
      error += chunk;
    });

    python.on('close', (code) => {
      console.log('[ELECTRON] Python apply process closed with code:', code);
      console.log('[ELECTRON] Output length:', output.length);
      console.log('[ELECTRON] Error length:', error.length);
      
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          console.log('[ELECTRON] Apply operation result:', result.success ? 'SUCCESS' : 'FAILED');
          console.log('[ELECTRON] Success count:', result.success_count);
          console.log('[ELECTRON] Error count:', result.error_count);
          resolve(result);
        } catch (e) {
          console.error('[ELECTRON] Failed to parse Python output:', e);
          console.log('[ELECTRON] Raw output:', output.substring(0, 500));
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        console.error('[ELECTRON] Python process failed with code:', code);
        console.error('[ELECTRON] Error output:', error);
        reject(new Error(`Python process failed: ${error}`));
      }
    });

    python.on('error', (err) => {
      console.error('[ELECTRON] Python process spawn error:', err);
      reject(err);
    });
  });
});

// Progress tracking
ipcMain.handle('python-get-progress', async (_, batchId: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'progress', batchId]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Pause operations
ipcMain.handle('python-pause-operations', async () => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'pause']);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Resume operations
ipcMain.handle('python-resume-operations', async () => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'resume']);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Cancel operations
ipcMain.handle('python-cancel-operations', async () => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'cancel']);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Cancel specific operation by batch ID
ipcMain.handle('python-cancel-operation', async (_, batchId: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'cancel', batchId]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Add handler for canceling scan operations specifically
// (This is an alias to python-cancel-operation for clarity in the frontend code)
ipcMain.handle('python-cancel-scan', async (_, batchId: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'cancel', batchId]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Validate sequence integrity
ipcMain.handle('python-validate-sequences', async (_, batchId: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'validate', batchId]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

ipcMain.handle('python-undo-last-batch', async () => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');
    
    const python = spawn('py', [pythonPath, 'undo']);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(output));
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}`));
        }
      } else {
        reject(new Error(`Python process failed: ${error}`));
      }
    });
  });
});

// Pattern configuration handlers
ipcMain.handle('load-pattern-config', async () => {
  try {
    const configPath = path.join(__dirname, '..', 'src', 'config', 'patterns.json');
    
    if (!existsSync(configPath)) {
      // Create default config if it doesn't exist
      const defaultConfig = {
        "shotPatterns": [
          "DEMO\\d{4}",
          "FULL\\d{4}",
          "ANOT\\d{4}",
          "OLNT\\d{4}",
          "KITC\\d{4}",
          "WTFB\\d{4}",
          "IGB\\d{4}",
          "SOME\\d{4}",
          "shot_?\\d{3,4}",
          "sh_?\\d{3,4}",
          "\\d{3,4}"
        ],
        "taskPatterns": {
          "comp": ["comp", "composite", "05_comp", "nuke", "final"],
          "vfx": ["vfx", "effects", "04_vfx", "fx"],
          "plates": ["plates", "plate", "source", "01_plates", "footage"],
          "support": ["support", "reference", "02_support"],
          "references": ["references", "ref", "03_references"],
          "mograph": ["mograph", "motion", "06_mograph"],
          "shared": ["shared", "assets", "07_shared"],
          "output": ["output", "delivery", "final", "08_output"],
          "project": ["project", "nuke", "script"],
          "render": ["render", "beauty", "rgb"],
          "main_arch": ["main_arch", "main", "arch", "architecture"],
          "depth": ["depth", "z", "zdepth"],
          "previz": ["previz", "previs", "preview", "PREVIZ"],
          "multipass": ["multipass", "multi", "pass", "Multipass"],
          "3d": ["3d", "models", "textures", "renders"],
          "footage": ["footage", "video", "source"]
        },
        "resolutionPatterns": [
          "proxy", "full_res", "2k", "4k", "uhd", "hd", "1920x1080", "3840x2160",
          "half_res", "quarter_res", "preview", "delivery", "1804k", "LL180", "LL1804k",
          "8k", "6k", "1080p", "720p", "480p"
        ],
        "versionPatterns": [
          "v\\d{3}",
          "ver\\d{3}",
          "version\\d{3}",
          "_v\\d{2,3}",
          "\\.v\\d{2,3}"
        ],
        "projectTypes": {
          "sphere": {
            "vfxFolder": "04_vfx",
            "compFolder": "05_comp"
          },
          "internal": {
            "footageFolder": "footage",
            "3dFolder": "3d"
          }
        }
      };
      
      // Ensure directory exists
      const configDir = path.join(configPath, '..');
      if (!existsSync(configDir)) {
        mkdirSync(configDir, { recursive: true });
      }
      
      writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
      return { success: true, config: defaultConfig };
    }
    
    const configData = readFileSync(configPath, 'utf8');
    const config = JSON.parse(configData);
    return { success: true, config };
    
  } catch (error: any) {
    console.error('Failed to load pattern config:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('save-pattern-config', async (event, config) => {
  try {
    const configPath = path.join(__dirname, '..', 'src', 'config', 'patterns.json');
    
    // Ensure directory exists
    const configDir = path.dirname(configPath);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return { success: true };
    
  } catch (error: any) {
    console.error('Failed to save pattern config:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('python-scan-folder-with-progress', async (_, folderPath: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');

    console.log('Python scan with progress - isDev:', isDev);
    console.log('Python path:', pythonPath);
    console.log('Folder path:', folderPath);
    console.log('Command:', 'py', [pythonPath, 'scan_with_progress', folderPath]);

    const python = spawn('py', [pythonPath, 'scan_with_progress', folderPath]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      console.log('[PYTHON STDOUT]', chunk);
    });

    python.stderr.on('data', (data) => {
      const chunk = data.toString();
      error += chunk;
      console.error('[PYTHON STDERR]', chunk);
    });

    python.on('close', (code) => {
      console.log('Python process closed with code:', code);
      console.log('Output:', output);
      console.log('Error:', error);
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}. Output: ${output}`));
        }
      } else {
        console.error('Python process failed with code:', code);
        console.error('Error output:', error);
        reject(new Error(`Python process failed with code ${code}: ${error || output}`));
      }
    });
  });
});

// Add scan progress polling handler
ipcMain.handle('python-get-scan-progress', async (_, batchId: string) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? join(__dirname, '../python/normalizer.py')
      : join(process.resourcesPath, 'python/normalizer.py');

    const python = spawn('py', [pythonPath, 'progress', batchId]);
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e}. Output: ${output}`));
        }
      } else {
        reject(new Error(`Python process failed with code ${code}: ${error || output}`));
      }
    });
  });
});

// Add WebSocket port handler using the built-in WebSocket server
ipcMain.handle('python-get-websocket-port', async () => {
  const port = getWebSocketPort();
  console.log('[ELECTRON] WebSocket port requested:', port);
  return port;
});

// Add handler for progress updates - python can call this through IPC or polling a file
ipcMain.handle('send-progress-update', async (_, batchId, filesProcessed, totalFiles, currentFile, status) => {
  // Only log occasionally to reduce spam
  if (filesProcessed % 500 === 0 || status === 'completed' || status === 'failed') {
    console.log(`[ELECTRON] Sending progress update for batch ${batchId}: ${filesProcessed}/${totalFiles} - ${status}`);
  }
  return sendProgressUpdate(batchId, filesProcessed, totalFiles, currentFile, status);
});

// Add file watcher for progress updates (alternative to direct IPC)
const setupProgressFileWatcher = () => {
  try {
    const progressDir = path.join(app.getAppPath(), 'python', '_progress');
    if (!fs.existsSync(progressDir)) {
      fs.mkdirSync(progressDir, { recursive: true });
    }
    
    const latestProgressFile = path.join(progressDir, 'latest_progress.json');
    
    // Check if the file exists and process initial content
    if (fs.existsSync(latestProgressFile)) {
      try {
        const content = fs.readFileSync(latestProgressFile, 'utf8');
        const data = JSON.parse(content);
        if (data.batch_id && data.totalFiles) {
          sendProgressUpdate(
            data.batch_id,
            data.filesProcessed,
            data.totalFiles,
            data.currentFile,
            data.status
          );
        }
      } catch (e) {
        console.error('[ELECTRON] Error reading initial progress file:', e);
      }
    }
    
    // Set up watcher for future updates
    fs.watch(progressDir, (eventType, filename) => {
      if (filename === 'latest_progress.json' && eventType === 'change') {
        try {
          const content = fs.readFileSync(latestProgressFile, 'utf8');
          const data = JSON.parse(content);
          if (data.batch_id && data.totalFiles) {
            sendProgressUpdate(
              data.batch_id,
              data.filesProcessed,
              data.totalFiles,
              data.currentFile,
              data.status
            );
          }
        } catch (e) {
          // Ignore file read errors - they can happen when file is being written
        }
      }
    });
    
    console.log('[ELECTRON] Progress file watcher set up successfully');
  } catch (e) {
    console.error('[ELECTRON] Error setting up progress file watcher:', e);
  }
};

// Add handler for WebSocket server status
ipcMain.handle('get-websocket-status', async () => {
  return getServerStatus();
});

// End of IPC handlers