# AAA WebScraper Setup Instructions

## Prerequisites

- Node.js and npm installed
- Python 3.8+ installed
- Redis server running (for Celery)
- Supabase account and project

## Step 1: Database Setup

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the entire contents of `backend/app/models/schema.sql`
4. Click **Run** to execute the SQL

This creates:
- `users`, `crawls`, `pages`, `links`, `issues`, `summaries` tables
- Row Level Security policies
- Proper indexes and relationships

## Step 2: Create Admin User

1. Go to **Authentication** → **Users** → **Add User**
2. Enter email and password
3. Go to **Table Editor** → **users** table
4. Click **Insert** → **Insert row**
5. Fill in:
   - `id`: Copy UUID from Authentication → Users
   - `email`: The email you used
   - `role`: Set to `admin`
6. Click **Save**

## Step 3: Environment Setup

### Backend (.env)
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# Redis
REDIS_URL=redis://localhost:6379/0

# App
DEBUG=True
SECRET_KEY=your_secret_key
```

### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Step 4: Install Dependencies

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Step 5: Start Services

You can start all services using npm scripts from the frontend directory:

### Option 1: Individual Commands
```bash
# Terminal 1 - FastAPI Backend
npm run start:backend

# Terminal 2 - Celery Worker  
npm run start:worker

# Terminal 3 - React Frontend
npm run start:dev
```

### Option 2: Manual Commands
```bash
# Backend API (Terminal 1)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker (Terminal 2)
cd backend
python -m celery -A app.services.worker.celery_app worker --loglevel=info --pool=solo

# Frontend (Terminal 3)
cd frontend
npm start
```

## Step 6: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Available npm Scripts

From the `frontend/` directory:

- `npm start` - Start React frontend only
- `npm run start:dev` - Start React frontend only  
- `npm run start:backend` - Start FastAPI backend
- `npm run start:worker` - Start Celery worker
- `npm run start:all` - Show startup instructions

## Architecture Overview

The platform consists of 3 main components:

1. **FastAPI Backend** - Handles HTTP requests, authentication, CRUD operations
2. **Celery Worker** - Processes background crawling tasks asynchronously  
3. **React Frontend** - User interface for managing crawls and viewing results

All three services must be running for full functionality.

## Troubleshooting

### Common Issues

1. **Celery worker fails to start**
   - Ensure Redis is running
   - Check Python path and dependencies

2. **Frontend can't connect to backend**
   - Verify backend is running on port 8000
   - Check CORS settings

3. **Database connection errors**
   - Verify Supabase credentials in .env
   - Check RLS policies are properly set

4. **Pages not saving during crawls**
   - Restart Celery worker after code changes
   - Check database schema matches crawler expectations

### Logs

- **Backend logs**: Terminal running uvicorn
- **Worker logs**: Terminal running celery worker  
- **Frontend logs**: Browser developer console
