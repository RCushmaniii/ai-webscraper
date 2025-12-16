# AAA Web Scraper

A full-stack web application for scraping websites with a React frontend, Python FastAPI backend, and Supabase for data storage.

## Features

- **Web Scraping**: Extract data from any website using CSS selectors
- **Pagination Support**: Scrape multiple pages with URL patterns or next button clicks
- **Task Management**: Track and monitor scraping tasks
- **Data Export**: Download scraped data in JSON or CSV format
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Node.js (v14 or later)
- Python (3.8 or later)
- npm or yarn
- Supabase account (for data storage)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/aaa-webscraper.git
cd aaa-webscraper
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 3. Set up the frontend

```bash
cd ../frontend
npm install

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API and Supabase URLs
```

### 4. Start the development servers

In one terminal (backend):
```bash
cd backend
uvicorn app.main:app --reload
```

In another terminal (frontend):
```bash
cd frontend
npm start
```

The application should now be running at `http://localhost:3000`

## Project Structure

```
aaa-webscraper/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   ├── .env.example        # Example environment variables
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React frontend
│   ├── public/             # Static files
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── styles/         # Global styles
│   ├── .env.example        # Example environment variables
│   └── package.json        # Node dependencies
│
├── .gitignore
├── README.md
└── setup.sh                # Setup script
```

## Environment Variables

### Backend (`.env`)

```
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend (`.env`)

```
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_KEY=your_supabase_anon_key
```

## Running Tests

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

### Backend

The backend can be deployed to any platform that supports Python/ASGI applications, such as:
- Heroku
- Google Cloud Run
- AWS Elastic Beanstalk
- DigitalOcean App Platform

### Frontend

The frontend can be deployed to any static hosting service, such as:
- Vercel
- Netlify
- GitHub Pages
- Firebase Hosting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Supabase](https://supabase.io/)
- [Tailwind CSS](https://tailwindcss.com/)
