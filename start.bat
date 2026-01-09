@echo off
setlocal enabledelayedexpansion

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

:: Change to script directory (important when running as admin)
cd /d "%~dp0"

title AI WebScraper Development Environment
color 0A

echo ========================================
echo    AI WebScraper Development Setup
echo ========================================
echo.
echo This script will start:
echo - FastAPI Backend (Port 8000)
echo - Celery Worker
echo - React Frontend (Port 3000)
echo - Using Upstash Redis (cloud)
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo [1/4] Killing ALL existing Node and Python processes...
echo Killing Node processes...
taskkill /F /IM node.exe >nul 2>&1
echo Killing Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
echo Killing Celery processes...
taskkill /F /FI "WINDOWTITLE eq Celery*" >nul 2>&1
echo Waiting for processes to fully terminate...
timeout /t 3 /nobreak >nul
echo Cleanup complete.
echo.
echo NOTE: Please manually close any leftover terminal windows before continuing.
echo Press any key when ready...
pause >nul

echo.
echo [2/4] Setting fixed ports...
set BACKEND_PORT=8000
set FRONTEND_PORT=3000
echo Backend will run on port %BACKEND_PORT%
echo Frontend will run on port %FRONTEND_PORT%

echo.
echo [3/4] Updating environment files...
powershell -Command "(Get-Content 'frontend\.env') -replace 'REACT_APP_API_URL=http://localhost:\d+/api/v1', 'REACT_APP_API_URL=http://localhost:%BACKEND_PORT%/api/v1' | Set-Content 'frontend\.env'"
powershell -Command "(Get-Content 'backend\.env') -replace 'API_PORT=\d+', 'API_PORT=%BACKEND_PORT%' | Set-Content 'backend\.env'"
echo Environment files updated.

echo.
echo [4/4] Starting services...
echo Starting FastAPI backend on port %BACKEND_PORT%...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1
start "FastAPI Backend" cmd /c "title FastAPI Backend (Port %BACKEND_PORT%) && cd /d %CD% && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting Celery worker...
start "Celery Worker" cmd /c "title Celery Worker && cd /d %CD% && venv\Scripts\activate && celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo"

echo Starting React frontend on port %FRONTEND_PORT%...
cd ..\frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)
set PORT=%FRONTEND_PORT%
start "React Frontend" cmd /c "title React Frontend (Port %FRONTEND_PORT%) && cd /d %CD% && set PORT=%FRONTEND_PORT% && npm start"

echo.
echo ========================================
echo    All Services Started Successfully!
echo ========================================
echo.
echo Services running in separate windows:
echo - Backend:         http://localhost:%BACKEND_PORT%
echo - Frontend:        http://localhost:%FRONTEND_PORT%
echo - API Docs:        http://localhost:%BACKEND_PORT%/docs
echo - Redis:           Upstash Cloud (configured)
echo.
echo Waiting for frontend to start...
timeout /t 10 >nul

echo.
echo Opening browser...
start http://localhost:%FRONTEND_PORT%

echo.
echo Press any key to exit this setup window...
pause >nul