# 🎓 Smart University Management System

> A modern, multi-service university management platform built with a microservice-oriented architecture.

![React](https://img.shields.io/badge/Frontend-React-blue?logo=react)
![Django](https://img.shields.io/badge/Backend-Django-092E20?logo=django)
![FastAPI](https://img.shields.io/badge/AI_Service-FastAPI-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/DevOps-Docker-2496ED?logo=docker)

This project integrates a **React** frontend, a **Django** backend, an AI service powered by **FastAPI**, and an **Nginx** reverse proxy for seamless service orchestration.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started (Setup)](#-getting-started--setup)
- [Environment Variables](#-environment-variables)
- [CI/CD & Testing](#-cicd--testing)
- [Team & Acknowledgments](#-team--acknowledgments)

---

## 📖 Overview

**Smart University Management System** is a fully containerized full-stack application designed to support core university operations using scalable, independent services:

- 🖥️ **Frontend**: React-based intuitive user interface.
- ⚙️ **Backend**: Django application handling core business logic and APIs.
- 🧠 **AI Service**: FastAPI-based microservice for smart, ML-driven capabilities.
- 🔀 **Nginx**: Reverse proxy to route client requests securely and efficiently.

---

## 🏗️ Architecture

**High-Level Flow:**

1. Users access the system via **Nginx**.
2. The **Frontend** serves the UI components.
3. The **Backend** processes operational data and university management tasks.
4. The **AI Service** handles specialized machine learning workloads independently.

---

## 💻 Tech Stack

| Category           | Technologies                                    |
| :----------------- | :---------------------------------------------- |
| **Frontend**       | React, React DOM, TypeScript                    |
| **Backend**        | Django, Django REST Framework, Gunicorn, Pytest |
| **AI Service**     | FastAPI, Uvicorn, TensorFlow, Pytest            |
| **Infrastructure** | Docker, Docker Compose, Nginx, GitHub Actions   |

---

## 🚀 Getting Started & Setup

Follow these instructions to get your local environment up and running.

### 📋 Prerequisites

Ensure you have the following installed:

- [Git](https://git-scm.com/)
- [Docker & Docker Compose](https://www.docker.com/)
- _(Optional for local dev)_ Node.js $\ge 20$, Python $\ge 3.11$

### 🐳 Method 1: Run with Docker Compose (Recommended)

This is the fastest and most reliable way to launch the entire ecosystem.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ghazalees/smart-university-management-system.git
   cd smart-university-management-system
   ```
2. **Build and start all services:**
   ```bash
   docker compose up --build
   ```
3. **Access the application:** Open your browser and navigate to `http://localhost`.
4. **Stop the services:**
   ```bash
   docker compose down
   ```

### 💻 Method 2: Run Services Locally (Without Docker)

<details>
<summary><strong>🖥️ Setup Frontend</strong></summary>

```bash
cd frontend
npm install
npm start
```

</details>

<details>
<summary><strong>⚙️ Setup Backend</strong></summary>

```bash
cd backend
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

</details>

<details>
<summary><strong>🧠 Setup AI Service</strong></summary>

```bash
cd ai-service
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements/development.txt
uvicorn api.main:app --host 0.0.0.0 --port 9000
```

</details>

---

## 🔐 Environment Variables

The backend requires an environment file to run securely. Create a `.env` file in the `backend/` directory:

# backend/.env

DEBUG=True
SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

> ⚠️ **Warning:** Never use `DEBUG=True` or expose your `SECRET_KEY` in a production environment.

---

## ⚙️ CI/CD & Testing

This repository uses **GitHub Actions** to enforce code quality and automate builds.

- **Frontend CI:** Installs dependencies (`npm ci`), runs tests, and verifies the build.
- **Backend CI:** Installs Python packages, runs Django checks, and executes `pytest-django`.
- **AI Service CI:** Runs independent FastAPI/TensorFlow tests.
- **Docker CI:** Verifies successful image builds for all services.

### Running Tests Locally

- **Frontend:** `cd frontend && npm test`
- **Backend:** `cd backend && python manage.py test`
- **AI Service:** `cd ai-service && python -m pytest`

---

## 👥 Team & Acknowledgments

**Development Team:**

- Gh. Eslami
- M. Mokhtari
- A. Rajabi
- A. Gheyratmand

**Course:** Advanced Software Engineering  
**Professor:** Dr. Lotfi  
**University:** Tarbiat Modares University
