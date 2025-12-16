#!/bin/bash

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Create .env files if they don't exist
if [ ! -f "../backend/.env" ]; then
    cp ../backend/.env.example ../backend/.env
    echo "Created backend/.env. Please update with your configuration."
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created frontend/.env. Please update with your configuration."
fi

echo "Setup complete! Don't forget to update the .env files with your configuration."
