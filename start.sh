#!/bin/bash

# Start Redis server in the background
redis-server --daemonize yes

# Start Celery worker in the background
cd backend
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
celery -A app.services.worker.celery_app worker --loglevel=info &

# Start FastAPI backend
uvicorn app.main:app --reload &

# Start React frontend
cd ../frontend
npm start
