@echo off
setlocal enabledelayedexpansion

:: ===================================================
::   The Uprising Hunter - Smart Launcher
:: ===================================================

set "BASE_LOG=%~dp0startup"
set "LAUNCHER_LOG=%BASE_LOG%_launcher.log"
set "BACKEND_LOG=%BASE_LOG%_backend.log"
set "FRONTEND_LOG=%BASE_LOG%_frontend.log"

:: ---------------------------------------------------
:: 0. Cleanup / Reset
:: ---------------------------------------------------
echo [INFO] Cleaning up previous sessions...

:: 1. Force kill by Ports (8000 = Backend, 3000 = Frontend)
:: This is the most reliable way to stop the specific services
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000 " ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000 " ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

:: 2. Force kill by Window Title (Clean up wrapper/cmd windows)
taskkill /FI "WINDOWTITLE eq The Uprising Hunter - Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq The Uprising Hunter - Frontend" /T /F >nul 2>&1

:: 3. Clear logs
if exist "%LAUNCHER_LOG%" del "%LAUNCHER_LOG%" >nul 2>&1
if exist "%BACKEND_LOG%" del "%BACKEND_LOG%" >nul 2>&1
if exist "%FRONTEND_LOG%" del "%FRONTEND_LOG%" >nul 2>&1

echo [INFO] Launcher started at %DATE% %TIME% > "%LAUNCHER_LOG%"

echo ===================================================
echo   Starting The Uprising Hunter (Backend + Frontend)
echo ===================================================
echo.

:: ---------------------------------------------------
:: 1. Python Environment Setup
:: ---------------------------------------------------
echo [STEP 1/4] Checking Python environment...

if exist ".venv\Scripts\activate.bat" goto :ActivateVenv

echo [WARNING] .venv not found. Attempting to create one...
python -m venv .venv >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment. See startup_errors.log.
    echo [ERROR] Failed to create virtual environment. >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [INFO] Virtual environment created. Activating...
call .venv\Scripts\activate.bat

echo [INFO] Installing dependencies (this may take a minute)...
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1

if exist "requirements.txt" (
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies. See startup_errors.log.
        echo [ERROR] Failed to install Python dependencies. >> "%LOG_FILE%"
        pause
        exit /b 1
    )
    echo [SUCCESS] Python dependencies installed.
) else (
    echo [WARNING] requirements.txt not found. Skipping pip install. >> "%LOG_FILE%"
)
goto :NodeSetup

:ActivateVenv
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:NodeSetup
:: ---------------------------------------------------
:: 2. Node.js Environment Setup
:: ---------------------------------------------------
echo [STEP 2/4] Checking Node.js environment...

:: Ensure Node.js is in PATH
where node >nul 2>&1
if %ERRORLEVEL% equ 0 goto :CheckFrontendDeps

if exist "C:\Program Files\nodejs\node.exe" (
    echo [INFO] Adding Node.js to session PATH...
    set "PATH=C:\Program Files\nodejs;%PATH%"
) else (
     echo [ERROR] Node.js not found in PATH or standard location.
     echo [ERROR] Node.js not found. >> "%LOG_FILE%"
     pause
     exit /b 1
)

:CheckFrontendDeps
:: Check frontend dependencies
if not exist "admin-dashboard\package.json" goto :StartBackend

if exist "admin-dashboard\node_modules" goto :StartBackend

echo [INFO] node_modules not found in admin-dashboard. Installing...
pushd admin-dashboard
call npm install >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
     echo [ERROR] npm install failed. See startup_errors.log.
     popd
     pause
     exit /b 1
)
echo [SUCCESS] Frontend dependencies installed.
popd

:StartBackend
:: ---------------------------------------------------
:: 3. Start Backend
:: ---------------------------------------------------
echo [STEP 3/4] Starting Backend (Port 8000)...
:: Use a temporary variable to hold the command to avoid complex quoting in 'start'
set BACKEND_COMMAND=python -m uvicorn src.admin.app:app --host 127.0.0.1 --port 8000 --reload
start "The Uprising Hunter - Backend" cmd /c ^"%BACKEND_COMMAND% 2^> ^"%BACKEND_LOG%^"^"

:: ---------------------------------------------------
:: 4. Start Frontend
:: ---------------------------------------------------
echo [STEP 4/4] Starting Frontend (Port 3000)...
pushd admin-dashboard
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to enter admin-dashboard directory.
    pause
    exit /b !ERRORLEVEL!
)

set FRONTEND_COMMAND=npm run dev
where npm >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "The Uprising Hunter - Frontend" cmd /c ^"%FRONTEND_COMMAND% 2^> ^"%FRONTEND_LOG%^"^"
) else (
    if exist "C:\Program Files\nodejs\npm.cmd" (
        start "The Uprising Hunter - Frontend" cmd /c ^"^\^"C:\Program Files\nodejs\npm.cmd^\^" run dev 2^> ^"%FRONTEND_LOG%^"^"
    ) else (
        echo [ERROR] npm command not found. >> "%LAUNCHER_LOG%"
        echo [ERROR] npm command not found.
    )
)
popd

echo.
echo [SUCCESS] Services launched! 
echo - Backend Log:  %BACKEND_LOG%
echo - Frontend Log: %FRONTEND_LOG%
echo - Launcher Log: %LAUNCHER_LOG%
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo Close this window to keep servers running in background windows.
pause
