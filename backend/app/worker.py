# Legacy worker entry point — selector-based scraping is disabled in v1.
# The primary crawl worker is at app/services/worker.py and uses
# FastAPI BackgroundTasks (no Celery/Redis dependency).
