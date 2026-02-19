@echo off
setlocal

echo ===================================================
echo   Starting The Uprising Hunter (Backend + Frontend)
echo ===================================================

:: Check for .venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found. Assuming global python or manual setup.
)

:: Ensure Node.js is in PATH for this session
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\nodejs\node.exe" (
        echo [INFO] Adding Node.js to session PATH...
        set "PATH=C:\Program Files\nodejs;%PATH%"
    )
)

:: Start Backend in new window
echo [INFO] Starting Backend API (Port 8000)...
start "The Uprising Hunter - Backend" cmd /k "python -m uvicorn src.admin.app:app --port 8000 --reload"

:: Start Frontend in new window
echo [INFO] Starting Frontend Dashboard (Port 3000)...
cd admin-dashboard

:: Check if npm is in PATH
where npm >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "The Uprising Hunter - Frontend" cmd /k "npm run dev"
) else (
    :: Try default install path
    if exist "C:\Program Files\nodejs\npm.cmd" (
        echo [INFO] Using absolute path for npm...
        start "The Uprising Hunter - Frontend" cmd /k ""C:\Program Files\nodejs\npm.cmd" run dev"
    ) else (
        echo [ERROR] npm was not found. Please ensure Node.js is installed.
        pause
        exit /b 1
    )
)

echo.
echo [SUCCESS] Services started!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo Close the new windows to stop the servers.
pause
