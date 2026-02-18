@echo off
setlocal

echo ===================================================
echo   Starting Prospect App (Backend + Frontend)
echo ===================================================

:: Check for .venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found. Assuming global python or manual setup.
)

:: Start Backend in new window
echo [INFO] Starting Backend API (Port 8000)...
start "Prospect Backend" cmd /k "python -m uvicorn src.admin.app:app --port 8000 --reload"

:: Start Frontend in new window
echo [INFO] Starting Frontend Dashboard (Port 3000)...
cd admin-dashboard
start "Prospect Frontend" cmd /k "npm run dev"

echo.
echo [SUCCESS] Services started!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo Close the new windows to stop the servers.
pause
