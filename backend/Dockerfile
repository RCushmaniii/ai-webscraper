FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port (Render uses PORT env var, default 10000)
EXPOSE 10000

# Command to run the application - use shell form so $PORT is expanded
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
