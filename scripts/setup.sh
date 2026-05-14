#!/bin/bash

echo "Setting up backend environment..."

cd backend

python -m venv venv
source venv/bin/activate

pip install -r requirements/development.txt

python manage.py migrate

echo "Setup complete"
