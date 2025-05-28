@echo off
echo Starting VFX Folder Normalizer Development Environment...
echo.

echo Starting Vite development server...
start "Vite Dev Server" cmd /k "yarn dev:renderer"

echo Waiting for Vite to start (10 seconds)...
timeout /t 3 /nobreak > nul

echo Starting Electron application...
start "Electron App" cmd /k "yarn dev:electron"

echo.
echo Both processes started!
echo - Vite Dev Server: http://localhost:3001
echo - Electron App: Should open automatically
echo.
echo To stop both processes, close both terminal windows or press Ctrl+C in each.