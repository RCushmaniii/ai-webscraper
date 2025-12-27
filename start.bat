@echo off
setlocal enabledelayedexpansion

title AI WebScraper Development Environment
color 0A

echo ========================================
echo    AI WebScraper Development Setup
echo ========================================
echo.
echo This script will start:
echo - FastAPI Backend 
echo - Celery Worker
echo - React Frontend
echo - Using Upstash Redis (cloud)
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo [1/5] Cleaning up existing processes...
call :KillProcessOnPortRange 3000 3010
call :KillProcessOnPortRange 8000 8010
echo Cleanup complete.

echo.
echo [2/5] Finding available ports...
call :FindAvailablePort 3000 3010 FRONTEND_PORT
call :FindAvailablePort 8000 8010 BACKEND_PORT
echo Using ports: Frontend=%FRONTEND_PORT%, Backend=%BACKEND_PORT%

echo.
echo [3/5] Updating environment files...
powershell -Command "(Get-Content 'frontend\.env') -replace 'REACT_APP_API_URL=http://localhost:8000/api/v1', 'REACT_APP_API_URL=http://localhost:%BACKEND_PORT%/api/v1' | Set-Content 'frontend\.env'"
powershell -Command "(Get-Content 'backend\.env') -replace 'API_PORT=8000', 'API_PORT=%BACKEND_PORT%' | Set-Content 'backend\.env'"
echo Environment files updated.

echo.
echo [4/5] Redis Configuration...
echo Using Upstash Redis (cloud) - no local Redis needed.

echo.
echo [5/5] Starting services...
echo Starting FastAPI backend on port %BACKEND_PORT%...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1
start "FastAPI Backend" cmd /k "title FastAPI Backend && cd /d %CD% && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

echo Starting Celery worker...
start "Celery Worker" cmd /k "title Celery Worker && cd /d %CD% && venv\Scripts\activate && celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo"

echo Starting React frontend on port %FRONTEND_PORT%...
cd ..\frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)
set PORT=%FRONTEND_PORT%
start "React Frontend" cmd /k "title React Frontend && cd /d %CD% && npm start"

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
goto :eof

:FindAvailablePort
setlocal
set START_PORT=%1
set END_PORT=%2
set RESULT_VAR=%3

for /l %%i in (%START_PORT%, 1, %END_PORT%) do (
    netstat -an | findstr ":%%i " >nul 2>&1
    if errorlevel 1 (
        set "RETURN_VALUE=%%i"
        goto :break
    )
)
:break
endlocal & set "%RESULT_VAR%=%RETURN_VALUE%"
goto :eof

:KillProcessOnPortRange
setlocal
set START_PORT=%1
set END_PORT=%2

for /l %%p in (%START_PORT%, 1, %END_PORT%) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        if not "%%a"=="" (
            echo Killing process on port %%p (PID: %%a)...
            taskkill /F /PID %%a >nul 2>&1
        )
    )
)
endlocal
goto :eof
