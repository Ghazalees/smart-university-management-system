FROM python:3.11-slim

WORKDIR /app

COPY requirements ./requirements

RUN pip install -r requirements/production.txt

COPY . .

EXPOSE 9000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
