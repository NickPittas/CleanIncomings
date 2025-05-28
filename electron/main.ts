import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import { join } from 'path';
import { spawn } from 'child_process';
import { isDev } from './utils';
import * as fs from 'fs';
import * as path from 'path';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import * as http from 'http';

// Helper function to get resource paths that works in all environments
function getResourcePath(relativePath: string): string {
  let resourcePath: string;
  
  if (isDev) {
    resourcePath = join(__dirname, '..', relativePath);
  } else {
    // In production, use the resources directory
    const appPath = app.getAppPath();
    const resourcesPath = process.resourcesPath || appPath;
    
    // First try the resources path (for packaged app)
    resourcePath = join(resourcesPath, relativePath);
    
    // If not found, try the app path (for development)
    if (!existsSync(resourcePath)) {
      resourcePath = join(appPath, relativePath);
    }
    
    // If still not found, try one level up (for ASAR unpacked files)
    if (!existsSync(resourcePath) && resourcesPath.endsWith('resources')) {
      resourcePath = join(resourcesPath, '..', relativePath);
    }
  }
  
  console.log(`🔍 Resource path for "${relativePath}": ${resourcePath}`);
  if (!existsSync(resourcePath)) {
    console.error(`❌ Resource not found: ${resourcePath}`);
  } else {
    console.log(`✅ Resource exists: ${resourcePath}`);
  }
  
  return resourcePath;
}

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
    const DEFAULT_PORT = 3001;
    let viteUrl = `http://localhost:${DEFAULT_PORT}`; // Default fallback
    
    // Function to check if server is responding
    const isServerReady = async (url: string): Promise<boolean> => {
      try {
        const response = await fetch(`${url}/__port`);
        return response.ok;
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.log(`❌ Server not ready at ${url}:`, errorMessage);
        return false;
      }
    };

    try {
      // Try to read the port from Vite's port file
      const portFilePath = join(__dirname, '../.vite-port');
      if (existsSync(portFilePath)) {
        try {
          const portData = JSON.parse(readFileSync(portFilePath, 'utf8'));
          if (portData && portData.url) {
            viteUrl = portData.url;
            console.log(`📖 Read Vite URL from port file: ${viteUrl}`);
          }
        } catch (e) {
          console.error('❌ Error parsing port file, using default port');
        }
      } else {
        console.log('📄 No .vite-port file found, using default port 3001');
      }

      // Wait for the server to be ready with retries
      const MAX_RETRIES = 10;
      let retries = 0;
      let serverReady = false;

      console.log(`⏳ Waiting for Vite server to be ready at ${viteUrl}...`);
      
      while (retries < MAX_RETRIES && !serverReady) {
        serverReady = await isServerReady(viteUrl);
        if (!serverReady) {
          retries++;
          console.log(`⏳ Waiting for Vite server (attempt ${retries}/${MAX_RETRIES})...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      if (!serverReady) {
        console.error(`❌ Vite server not ready after ${MAX_RETRIES} attempts`);
        // Fall back to default port if different
        if (!viteUrl.includes(`:${DEFAULT_PORT}`)) {
          viteUrl = `http://localhost:${DEFAULT_PORT}`;
          console.log(`🔄 Trying fallback URL: ${viteUrl}`);
        }
      } else {
        console.log(`✅ Vite server is ready at ${viteUrl}`);
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      console.error('❌ Error initializing Vite connection:', errorMessage);
    }
    
    // Load the URL with retries
    console.log(`🔗 Loading: ${viteUrl}`);
    
    const MAX_LOAD_ATTEMPTS = 10;
    let loaded = false;
    let attempts = 0;
    
    while (!loaded && attempts < MAX_LOAD_ATTEMPTS) {
      attempts++;
      try {
        console.log(`🔄 Load attempt ${attempts}/${MAX_LOAD_ATTEMPTS}...`);
        
        // Clear any existing navigation state
        mainWindow.webContents.stop();
        
        // Load the URL with a timeout
        await Promise.race([
          mainWindow.loadURL(viteUrl),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Load timeout')), 10000)
          )
        ]);
        
        // Verify the page loaded correctly
        const pageTitle = await mainWindow.webContents.getTitle();
        if (pageTitle && !pageTitle.includes('Error')) {
          console.log(`✅ Successfully loaded: ${viteUrl} on attempt ${attempts}`);
          loaded = true;
          break;
        } else {
          throw new Error('Page loaded but title indicates an error');
        }
        
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`❌ Attempt ${attempts} failed:`, errorMessage);
        
        if (attempts < MAX_LOAD_ATTEMPTS) {
          // Exponential backoff with jitter
          const baseDelay = Math.min(1000 * Math.pow(2, attempts), 10000);
          const jitter = Math.random() * 1000;
          const delay = Math.floor(baseDelay + jitter);
          
          console.log(`⏳ Waiting ${delay}ms before next attempt...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          
          // Try to reconnect to the dev server
          if (attempts % 3 === 0) {
            console.log('🔄 Attempting to reconnect to dev server...');
            try {
              await fetch(`${viteUrl}/__port`, { method: 'HEAD' });
              console.log('✅ Dev server is responding');
            } catch (e) {
              console.error('❌ Dev server is not responding, will retry...');
            }
          }
        }
      }
    }
    
    if (!loaded) {
      console.error(`❌ All ${MAX_LOAD_ATTEMPTS} load attempts failed`);
      
      // Fallback to default port if different
      if (viteUrl !== 'http://localhost:3001' && mainWindow && !mainWindow.isDestroyed()) {
        try {
          console.log('⏳ Trying fallback URL: http://localhost:3001');
          await mainWindow.loadURL('http://localhost:3001');
          console.log('✅ Fallback successful');
        } catch (fallbackError) {
          console.error('❌ Fallback also failed');
          
          // Show error page as last resort
          const errorHtml = `
            <html>
              <head>
                <title>Connection Error</title>
                <style>
                  body { font-family: Arial, sans-serif; background-color: #f5f5f5; color: #333; text-align: center; padding: 50px; }
                  .error-container { background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                  h1 { color: #e74c3c; }
                  .buttons { margin-top: 30px; }
                  button { background-color: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; margin: 0 10px; }
                  button:hover { background-color: #2980b9; }
                </style>
              </head>
              <body>
                <div class="error-container">
                  <h1>Connection Error</h1>
                  <p>Could not connect to the development server.</p>
                  <p>Make sure the Vite development server is running.</p>
                  <div class="buttons">
                    <button onclick="window.location.reload()">Retry Connection</button>
                    <button onclick="window.electronAPI.restart()">Restart App</button>
                  </div>
                </div>
              </body>
            </html>
          `;
          mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHtml)}`);
        }
      }
    }
    
    // Show window after a delay regardless of load status
    setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show();
        mainWindow.focus();
        console.log('🪟 Window force-shown after delay');
      }
    }, 500);
    
    mainWindow.webContents.openDevTools();
  } else {
    try {
      // In production, try multiple possible locations for the renderer files
      const possiblePaths = [
        path.join(process.resourcesPath, 'app.asar.unpacked', 'dist', 'renderer', 'index.html'),
        path.join(process.resourcesPath, 'app', 'dist', 'renderer', 'index.html'),
        path.join(__dirname, '..', 'dist', 'renderer', 'index.html'),
        path.join(app.getAppPath(), 'dist', 'renderer', 'index.html'),
        path.join(process.cwd(), 'dist', 'renderer', 'index.html')
      ];

      let rendererPath = '';
      for (const possiblePath of possiblePaths) {
        console.log(`🔍 Checking for renderer at: ${possiblePath}`);
        if (existsSync(possiblePath)) {
          rendererPath = possiblePath;
          console.log(`✅ Found renderer at: ${rendererPath}`);
          break;
        }
      }

      if (!rendererPath) {
        throw new Error('Could not find renderer index.html in any expected location');
      }

      console.log(`🔗 Loading production file: ${rendererPath}`);
      await mainWindow.loadFile(rendererPath);
      console.log('✅ Successfully loaded renderer');
    } catch (error) {
      console.error('❌ Failed to load renderer:', error);
      
      // Define paths for error display
      const errorPaths = [
        path.join(process.resourcesPath, 'app.asar.unpacked', 'dist', 'renderer', 'index.html'),
        path.join(process.resourcesPath, 'app', 'dist', 'renderer', 'index.html'),
        path.join(__dirname, '..', 'dist', 'renderer', 'index.html'),
        path.join(app.getAppPath(), 'dist', 'renderer', 'index.html'),
        path.join(process.cwd(), 'dist', 'renderer', 'index.html')
      ];
      
      // Show error page
      const errorHtml = `
        <html>
          <head>
            <title>Error Loading App</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; }
              pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow: auto; }
              .error { color: #d32f2f; }
            </style>
          </head>
          <body>
            <h1>Error Loading Application</h1>
            <p>The application failed to load. Please check the logs for more details.</p>
            <h2>Error Details:</h2>
            <pre>${error instanceof Error ? error.stack : String(error)}</pre>
            <h3>Paths checked:</h3>
            <pre>${JSON.stringify(errorPaths, null, 2)}</pre>
            <h3>Current working directory:</h3>
            <pre>${process.cwd()}</pre>
            <h3>__dirname:</h3>
            <pre>${__dirname}</pre>
            <h3>app.getAppPath():</h3>
            <pre>${app.getAppPath()}</pre>
            <h3>process.resourcesPath:</h3>
            <pre>${process.resourcesPath}</pre>
          </body>
        </html>
      `;
      
      if (mainWindow && !mainWindow.isDestroyed()) {
        await mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHtml)}`);
      }
    }
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
    // [REMOVED] Electron WebSocket server startup (now handled by Python)
    // const result = startWebSocketServer();
    // if (result.running) {
    //   console.log(`[ELECTRON] WebSocket server started successfully on port ${result.port}`);
    //   setupProgressFileWatcher();
    // } else {
    //   console.error('[ELECTRON] Failed to start WebSocket server');
    // }
  } catch (e) {
    console.error('[ELECTRON] Error starting progress server:', e);
  }
}

// App restart handler
ipcMain.handle('app-restart', () => {
  console.log('🔄 Restarting application...');
  app.relaunch();
  app.exit(0);
});

// Clean up resources
app.on('before-quit', () => {
  console.log('Cleaning up before quitting...');
});

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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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

// Helper function to read mapping progress
async function getMappingProgress(batchId: string): Promise<any> {
  try {
    // First check if we have WebSocket progress data
    const progressDir = join(process.env.TEMP || '/tmp', 'folder_normalizer');
    const progressFile = join(progressDir, `mapping_progress_${batchId}.json`);
    
    // Try to get the progress from the WebSocket server first
    try {
      // Check if we can get progress from the FileOperations class
      const result = await new Promise((resolve, reject) => {
        const pythonPath = getResourcePath('python/normalizer.py');
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
              reject(new Error(`Failed to parse progress output: ${e}`));
            }
          } else {
            reject(new Error(`Python process exited with code ${code}: ${error}`));
          }
        });
        
        // Add timeout
        setTimeout(() => {
          reject(new Error('Timeout getting progress from Python'));
        }, 3000);
      });
      
      // If we got a valid result with the batch ID, return it
      const typedResult = result as { batch_id?: string; [key: string]: any };
      if (typedResult && typedResult.batch_id === batchId) {
        return {
          ...typedResult,
          success: true
        };
      }
    } catch (error: unknown) {
      const wsError = error instanceof Error ? error : new Error(String(error));
      console.log(`WebSocket progress not available: ${wsError.message}`);
      // Continue to file-based fallback
    }
    
    // Fallback to file-based progress
    if (existsSync(progressFile)) {
      const progressData = JSON.parse(readFileSync(progressFile, 'utf8'));
      return {
        ...progressData,
        success: true
      };
    } else {
      return {
        success: false,
        error: 'Progress data not found',
        current: 0,
        total: 100,
        percentage: 0,
        status: 'unknown'
      };
    }
  } catch (error) {
    console.error('Error reading mapping progress:', error);
    return {
      success: false,
      error: String(error),
      current: 0,
      total: 100,
      percentage: 0,
      status: 'error'
    };
  }
}

// Handler to check mapping progress
ipcMain.handle('python-get-mapping-progress', async (_, batchId: string) => {
  return getMappingProgress(batchId);
});

ipcMain.handle('python-generate-mapping', async (_, tree: any, profile: any) => {
  return new Promise((resolve, reject) => {
    // Generate a unique batch ID for tracking progress
    const batchId = `map_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
    
    const pythonPath = getResourcePath('python/normalizer.py');
    
    console.log('Python mapping - isDev:', isDev);
    console.log('Python path:', pythonPath);
    console.log('Batch ID:', batchId);
    console.log('Profile:', profile.name);
    
    // Prepare the input data
    const inputData = {
      tree,
      profile,
      batchId
    };
    
    // Convert to JSON string
    const inputJson = JSON.stringify(inputData);
    
    console.log('Command:', 'py', [
      pythonPath,
      'map'
    ]);
    
    // Debug the tree structure
    console.log('Tree being sent to Python:');
    console.log('  Tree type:', typeof tree);
    console.log('  Tree keys:', Object.keys(tree));
    console.log('  Tree name:', tree.name);
    console.log('  Tree type field:', tree.type);
    console.log('  Tree children count:', tree.children?.length || 0);
    console.log('  First few children:');
    if (tree.children && tree.children.length > 0) {
      tree.children.slice(0, 3).forEach((child: any, index: number) => {
        console.log(`    Child ${index + 1}: ${child.name} (type: ${child.type}, children: ${child.children?.length || 0})`);
      });
    }
    
    // Log the size of the input data
    console.log('Input data size:', inputJson.length, 'characters');
    console.log('Input data preview:', inputJson.substring(0, 500) + '...');
    
    const python = spawn('py', [pythonPath, 'map']);
    
    let stdoutData = '';
    let stderrData = '';
    let progressCheckInterval: NodeJS.Timeout | null = null;
    let lastProgressUpdate = Date.now();
    let isProcessingStuck = false;
    
    // Write the input data to the Python process stdin
    python.stdin.write(inputJson);
    python.stdin.end(); // Close the stdin stream to signal the end of input
    console.log('Sent input data to Python process');
    
    // Setup progress checking
    progressCheckInterval = setInterval(async () => {
      try {
        // Check if we have progress updates
        const progress = await getMappingProgress(batchId);
        if (progress && progress.timestamp) {
          lastProgressUpdate = Date.now();
          console.log(`Mapping progress: ${progress.percentage}% - ${progress.status} - ${progress.current_file || 'N/A'}`);
        } else {
          // Check if we haven't received updates for a while
          const timeSinceLastUpdate = Date.now() - lastProgressUpdate;
          if (timeSinceLastUpdate > 60000) { // 1 minute without updates
            console.log(`No progress updates for ${timeSinceLastUpdate/1000} seconds, process may be stuck`);
            isProcessingStuck = true;
          }
        }
      } catch (error) {
        console.log(`Error checking progress: ${error}`);
      }
    }, 5000); // Check every 5 seconds
    
    python.stdout.on('data', (data) => {
      const chunk = data.toString();
      stdoutData += chunk;
    });
    
    python.stderr.on('data', (data) => {
      const chunk = data.toString();
      stderrData += chunk;
      console.log('Python mapping stderr:', chunk);
      // Reset the stuck timer if we're getting stderr output
      lastProgressUpdate = Date.now();
    });

    python.on('close', (code) => {
      // Clear the progress check interval
      if (progressCheckInterval) {
        clearInterval(progressCheckInterval);
      }
      
      console.log('Python mapping process closed with code:', code);
      console.log('Mapping output length:', stdoutData.length);
      console.log('Mapping error length:', stderrData.length);
      
      if (code === 0) {
        try {
          // Clean the output - remove any stderr messages that might be mixed in
          const lines = stdoutData.split('\n');
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
          let mappings = result.proposals || result.mappings || result || [];
          console.log('Returning mappings array with length:', Array.isArray(mappings) ? mappings.length : 'not an array');
          
          // Group sequences and transform mappings to include the node structure expected by the UI
          if (Array.isArray(mappings)) {
            // Improved sequence detection - look for sequence properties in multiple places
            // Check all the different ways a sequence might be identified in the mapping data
            const sequenceMappings = mappings.filter(mapping => {
              // Check multiple possible locations for sequence identification
              return mapping.type === 'sequence' || 
                     (mapping.node && mapping.node.type === 'sequence') ||
                     mapping.sequence || 
                     (mapping.frameRange && mapping.frameCount);
            });
            
            // Everything else is a single file
            const singleFileMappings = mappings.filter(mapping => {
              return !sequenceMappings.includes(mapping);
            });
            
            console.log(`Found ${sequenceMappings.length} sequences and ${singleFileMappings.length} single files`);
            console.log('Sample sequence mapping:', sequenceMappings.length > 0 ? JSON.stringify(sequenceMappings[0]).substring(0, 500) : 'none');
            
            // Process sequences
            const processedSequences = sequenceMappings.map(sequence => {
              // Extract sequence info from wherever it exists in the data structure
              const seqData = sequence.sequence || sequence;
              const baseName = seqData.base_name || sequence.name || '';
              const frameRange = seqData.frame_range || sequence.frameRange || '';
              const frameCount = seqData.frame_count || sequence.frameCount || 0;
              const suffix = seqData.suffix || '';
              
              console.log(`Processing sequence: ${baseName} [${frameRange}]`);
              
              // Create a proper mapping object for the sequence
              return {
                id: `seq-${baseName}-${Date.now()}`,
                sourcePath: sequence.sourcePath || seqData.directory || '',
                targetPath: sequence.targetPath || sequence.destination || '',
                status: sequence.status || 'auto',
                type: 'sequence',
                isSequence: true,
                frameRange: frameRange,
                frameCount: frameCount,
                // Store all the original sequence properties
                ...sequence,
                // Create the node structure expected by the UI
                node: {
                  name: `${baseName}${suffix} [${frameRange}]`,
                  path: sequence.sourcePath || seqData.directory || '',
                  type: 'sequence',
                  extension: seqData.extension || '',
                  children: [], // Empty array for safety
                  frameRange: frameRange,
                  frameCount: frameCount
                }
              };
            });
            
            // Process single files
            const processedSingleFiles = singleFileMappings.map(mapping => {
              // Create a valid mapping object with all required properties
              const enhancedMapping = {
                ...mapping,
                // Ensure targetPath exists and is a string
                targetPath: mapping.destination || mapping.targetPath || '',
                // Add source path if missing
                source: mapping.source || ''
              };
              
              // If mapping doesn't have a node property, create one
              if (!enhancedMapping.node) {
                // Extract filename from source path
                const filename = enhancedMapping.source ? 
                  (enhancedMapping.source.split('/').pop() || 
                   enhancedMapping.source.split('\\').pop() || 'Unknown') : 'Unknown';
                   
                // Get file extension
                const extMatch = filename.match(/\.[^.\\/:*?"<>|]+$/i);
                const extension = extMatch ? extMatch[0].toLowerCase() : '';
                
                enhancedMapping.node = {
                  name: filename,
                  path: enhancedMapping.source || '',
                  type: 'file',
                  extension: extension, // Add extension for file type detection
                  children: [] // Empty array to prevent null reference errors
                };
              }
              
              return enhancedMapping;
            });
            
            // Combine sequences and single files
            mappings = [...processedSequences, ...processedSingleFiles];
            console.log(`Returning ${mappings.length} total mappings with ${processedSequences.length} sequences`);
          }
          
          resolve(Array.isArray(mappings) ? mappings : []);
        } catch (e) {
          console.error('Mapping JSON parse error:', e);
          console.log('Raw mapping output preview:', stdoutData.substring(0, 1000));
          if (isProcessingStuck) {
            reject(new Error(`Mapping process appears to be stuck. The operation was terminated. This may happen with very large folders or when there are issues with file access.`));
          } else {
            resolve([]); // Return empty array instead of rejecting
          }
        }
      } else {
        console.error('Python mapping process failed with code:', code);
        console.error('Mapping error output:', stderrData);
        if (isProcessingStuck) {
          reject(new Error(`Mapping process appears to be stuck. The operation was terminated. This may happen with very large folders or when there are issues with file access.`));
        } else {
          resolve([]); // Return empty array instead of rejecting
        }
      }
    });

    python.on('error', (err) => {
      // Clear the progress check interval
      if (progressCheckInterval) {
        clearInterval(progressCheckInterval);
      }
      console.error('Python mapping process spawn error:', err);
      reject(new Error(`Failed to start Python mapping process: ${err.message}`));
    });

    // Add timeout to prevent hanging
    const timeoutDuration = 180000; // 3 minutes timeout
    setTimeout(() => {
      if (!python.killed) {
        console.log(`Killing Python mapping process due to timeout after ${timeoutDuration/1000} seconds`);
        // Clear the progress check interval
        if (progressCheckInterval) {
          clearInterval(progressCheckInterval);
        }
        python.kill();
        reject(new Error(`Mapping process timed out after ${timeoutDuration/1000} seconds. This may happen with very large folders or when there are issues with file access.`));
      }
    }, timeoutDuration);
  });
});

ipcMain.handle('python-apply-mappings', async (_, mappings: any[]) => {
  return new Promise((resolve, reject) => {
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
    console.log('[ELECTRON] Starting python-apply-mappings-enhanced');
    console.log('[ELECTRON] Data keys:', Object.keys(data));
    console.log('[ELECTRON] Operation type:', data.operation_type);
    console.log('[ELECTRON] Number of mappings:', data.mappings?.length);
    console.log('[ELECTRON] WebSocket port requested:', data.websocket_port || 8765);
    
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

    // Add timeout to prevent hanging
    const timeoutId = setTimeout(() => {
      if (!python.killed) {
        console.log('[ELECTRON] Killing Python apply process due to timeout');
        python.kill();
        resolve({ 
          success: false, 
          success_count: 0, 
          error_count: data.mappings?.length || 0,
          error: 'Operation timed out after 5 minutes'
        });
      }
    }, 300000); // 5 minutes timeout

    python.on('close', (code) => {
      // Clear the timeout since the process has completed
      clearTimeout(timeoutId);
      
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');
    
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
    const pythonPath = getResourcePath('python/normalizer.py');

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
    const pythonPath = getResourcePath('python/normalizer.py');

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
  // Always return the Python WebSocket server port
  return 8765;
});

// Add handler for progress updates - python can call this through IPC or polling a file
ipcMain.handle('send-progress-update', async (_, batchId, filesProcessed, totalFiles, currentFile, status) => {
  // Only log occasionally to reduce spam
  if (filesProcessed % 500 === 0 || status === 'completed' || status === 'failed') {
    console.log(`[ELECTRON] Sending progress update for batch ${batchId}: ${filesProcessed}/${totalFiles} - ${status}`);
  }
  return { success: false, message: 'sendProgressUpdate is deprecated; use Python WebSocket server.' };
});

// Add file watcher for progress updates (alternative to direct IPC)
const setupProgressFileWatcher = () => {
  // This function is now a no-op
};

// Add handlers for WebSocket server status and progress monitoring
ipcMain.handle('get-websocket-status', async () => {
  return { running: false, message: 'getServerStatus is deprecated; use Python WebSocket server.' };
});

// End of IPC handlers