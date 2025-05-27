@echo off
ECHO Starting CleanIncomings application...

:: Set up Node.js environment variables if not already set
IF "%PATH:node.js=%"=="%PATH%" (
    ECHO Node.js not found in PATH. Checking standard locations...
    
    :: Check common installation locations
    IF EXIST "%ProgramFiles%\nodejs" (
        SET "PATH=%PATH%;%ProgramFiles%\nodejs"
        ECHO Added Node.js from Program Files to PATH
    ) ELSE IF EXIST "%ProgramFiles(x86)%\nodejs" (
        SET "PATH=%PATH%;%ProgramFiles(x86)%\nodejs"
        ECHO Added Node.js from Program Files (x86) to PATH
    ) ELSE IF EXIST "%LOCALAPPDATA%\Programs\nodejs" (
        SET "PATH=%PATH%;%LOCALAPPDATA%\Programs\nodejs"
        ECHO Added Node.js from Local AppData to PATH
    ) ELSE (
        ECHO Node.js not found in common locations.
        ECHO Please install Node.js or add it to your PATH manually.
        PAUSE
        EXIT /B 1
    )
)

:: First start the WebSocket progress server
ECHO Starting WebSocket progress server...
CD /D "%~dp0python"
START /B CMD /C py progress_server.py start

:: Wait a moment for the server to start
TIMEOUT /T 2 > NUL

:: Now start the Electron app
ECHO Starting Electron app...
CD /D "%~dp0"
npm run dev

ECHO CleanIncomings application terminated.
PAUSE 