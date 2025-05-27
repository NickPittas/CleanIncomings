// TypeScript declaration for window.electronAPI
export {}; // ensure this file is a module

declare global {
  interface Window {
    electronAPI: {
      selectFolder: () => Promise<string | null>;
      scanFolder: (folderPath: string) => Promise<any>;
      generateMapping?: (incomingTree: any, options?: any) => Promise<any>;
      // Add any other methods you use from electronAPI here
    };
  }
}
