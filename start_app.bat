@echo off
echo Starting the application...

REM Start the progress monitoring server first
echo Starting progress monitoring server...
start cmd /k "cd python && python progress_monitor.py --start-servers"

REM Wait a moment for the server to initialize
timeout /t 3

REM Run the main application
echo Starting the main application...
cd electron
start cmd /k "yarn electron ..\dist\main.js"

echo Application started! You can view progress at http://localhost:7800
start http://localhost:7800
