@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

set "PYTHON_CMD=python"
if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%BACKEND_DIR%\.venv\Scripts\python.exe"
)

set "PYTHONHOME="
set "PYTHONNOUSERSITE=1"
set "PYTHONPATH=%BACKEND_DIR%"

where wt >nul 2>nul
if errorlevel 1 (
    echo Windows Terminal (wt) not found. Falling back to dev.bat.
    call "%ROOT%dev.bat"
    exit /b %errorlevel%
)

echo Starting AI WebScraper dev stack in Windows Terminal...

echo Using Python: %PYTHON_CMD%

echo.
echo Make sure Redis is running on localhost:6379 (Celery broker).
echo.

wt -w 0 ^
  new-tab --title backend -d "%BACKEND_DIR%" cmd /k ""%PYTHON_CMD%" -m uvicorn app.main:app --app-dir "%BACKEND_DIR%" --reload --reload-dir "%BACKEND_DIR%" --host 0.0.0.0 --port 8000 ^& echo. ^& echo [backend] exited ^& pause" ^
  ; new-tab --title worker -d "%BACKEND_DIR%" cmd /k ""%PYTHON_CMD%" -m celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo ^& echo. ^& echo [worker] exited ^& pause" ^
  ; new-tab --title frontend -d "%FRONTEND_DIR%" cmd /k "npm start"

endlocal
