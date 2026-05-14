#!/bin/bash

cd backend || exit

if [ ! -d "venv" ]; then
    echo "Virtual environment not found"
    exit 1
fi

source venv/bin/activate

python manage.py runserver
