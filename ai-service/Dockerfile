FROM python:3.11-slim

WORKDIR /app

<<<<<<< HEAD
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
=======
COPY requirements ./requirements

RUN pip install -r requirements/production.txt
>>>>>>> 250a4ad97a49ae52d148a351ad88ff7c8ba80cc4

COPY . .

EXPOSE 9000
<<<<<<< HEAD
=======

>>>>>>> 250a4ad97a49ae52d148a351ad88ff7c8ba80cc4
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
