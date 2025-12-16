@echo off
setlocal

set "ROOT=%~dp0"
echo Starting AAA WebScraper dev stack...
echo.
echo Make sure Redis is running on localhost:6379 (Celery broker).
echo.

start "backend" cmd /k "cd /d "%ROOT%backend" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "worker" cmd /k "cd /d "%ROOT%backend" && python -m celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo"
start "frontend" cmd /k "cd /d "%ROOT%frontend" && npm start"

echo.
echo Started:
echo - Backend:  http://localhost:8000
echo - Health:   http://localhost:8000/health
echo - Frontend: http://localhost:3000
echo.
echo Close the opened terminal windows to stop services.
echo.
endlocal
