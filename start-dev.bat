@echo off
echo Starting VFX Folder Normalizer Development Environment...
echo.

echo Starting Vite development server...
start "Vite Dev Server" cmd /k "npm run dev:renderer"

echo Waiting for Vite to start...
timeout /t 5 /nobreak > nul

echo Starting Electron application...
start "Electron App" cmd /k "npm run dev:electron"

echo.
echo Both processes started!
echo - Vite Dev Server: http://localhost:3000
echo - Electron App: Should open automatically
echo.
echo To stop both processes, close both terminal windows or press Ctrl+C in each. 