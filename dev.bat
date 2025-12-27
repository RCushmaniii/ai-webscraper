@echo off
setlocal

set "ROOT=%~dp0"
echo Starting AI WebScraper dev stack...
echo.
echo Make sure Redis is running on localhost:6379 (Celery broker).
echo.

set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

set "PYTHON_CMD=python"
if exist "%ROOT%backend\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT%backend\.venv\Scripts\python.exe"
)

echo Using Python: %PYTHON_CMD%

set "PYTHONHOME="
set "PYTHONNOUSERSITE=1"
set "PYTHONPATH=%BACKEND_DIR%"

start "backend" /D "%BACKEND_DIR%" cmd /k ""%PYTHON_CMD%" -m uvicorn app.main:app --app-dir "%BACKEND_DIR%" --reload --reload-dir "%BACKEND_DIR%" --host 0.0.0.0 --port 8000 & echo. & echo [backend] exited & pause"
start "worker" /D "%BACKEND_DIR%" cmd /k ""%PYTHON_CMD%" -m celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo & echo. & echo [worker] exited & pause"
start "frontend" /D "%FRONTEND_DIR%" cmd /k "npm start"

echo.
echo Started:
echo - Backend:  http://localhost:8000
echo - Health:   http://localhost:8000/health
echo - Frontend: http://localhost:3000 (or next available port if prompted)
echo.
echo Close the opened terminal windows to stop services.
echo.
endlocal
