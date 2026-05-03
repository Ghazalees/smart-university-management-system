# Smart University Management System
**AI‑Powered Academic Support & University Workflow Automation Platform**

A smart, modular, scalable university management system designed to provide **AI‑driven support**, **automated workflows**, and **centralized rule management** for students, professors, administrative staff, and university managers.

---

# 📌 Overview

Modern universities face common challenges:

- Information scattered across multiple systems
- Slow responses to questions (sometimes **24+ hours**)
- Difficulty accessing rules and regulations
- Repetitive administrative tasks
- Limited transparency and monitoring
- Inefficient communication between departments

The **Smart University Management System (SUMS)** solves these by combining:

- Large Language Models (LLM)
- Automated workflow processing
- Centralized rule management
- Scalable API-driven backend
- Modern frontend UI/UX
- Full observability via ELK
- Automated deployment with CI/CD

---

# 🎯 Project Objectives

- Provide **instant, accurate answers** to university-related questions
- Automate academic & administrative workflows
- Centralize and digitize university regulations
- Improve communication and transparency
- Reduce workload for administrative staff
- Enable scalable, secure, maintainable university systems
- Fully integrate modern AI capabilities inside university operations

---

# 👥 Target Users

The system supports multiple user classes:

- Students
- Professors
- Administrative Staff
- University Managers / System Admins

Each role receives **custom access, features, and permissions**.

---

# ✨ Key Features

## Student & Professor Features

- User registration & login
- AI-powered question answering (university rules, academic processes, deadlines)
- Access to regulations & FAQs
- Course schedule and academic data
- Submitting administrative requests

---

## Workflow Automation

The system supports intelligent automated processing for:

- Leave requests
- Certificate issuance
- Tuition discount requests
- Academic/administrative approvals
- Multi-step workflow routing
- Status tracking & notifications

Workflows are **rule-driven and customizable by admins without editing code**.

---

## System Administration

- Admin dashboard
- Rule, policy & workflow editor
- User access control
- Monitoring panels (via ELK)
- Reporting & analytics
- AI fine-tuning and dataset management

---

# System Architecture

A scalable multi-layer architecture:
frontend → backend → ai-service → database

↓

rules engine

↓

monitoring (ELK)

### Frontend
Modern web application UI

- User interaction
- Dashboards
- Forms
- Workflow interfaces

### Backend
- REST API
- Authentication (RBAC)
- Business logic
- Workflow automation
- Integration layer

### AI Service
- LLM-based Q&A
- NLP processing
- Rule-aware responses
- Model updating & fine‑tuning

### Database
Stores:

- users
- roles
- logs
- workflows
- rules
- queries

### ELK Stack

Provides:

- centralized logging
- monitoring
- analytics
- observability

### CI/CD

Automated pipeline:
build → test → dockerize → deploy

---

# AI Capabilities

- Natural Language Understanding
- University rule-aware Q&A
- Policy‑driven reasoning
- Context extraction from documents
- Custom dataset fine‑tuning
- Text classification & validation

The AI model interprets user queries, applies university rules, validates conditions, and generates accurate responses.

---

# Access Control (RBAC)

The system enforces **Role‑Based Access Control**:

- **Student:** limited user operations
- **Professor:** academic-level access
- **Admin Staff:** workflow processing
- **System Administrator:** full system management

Permissions are **fully configurable via the backend**.

---

# Technology Stack

## Frontend
- React.js (or Vue / Next.js)
- Tailwind CSS / Material UI

## Backend
- Python
- Django or FastAPI
- REST API
- Workflow Engine

## AI Service
- Python
- FastAPI
- LLM / NLP models (GPT, Llama, fine‑tuned models)

## Monitoring
- Elasticsearch
- Logstash
- Kibana

## CI/CD
- GitHub Actions
- Docker
- GitHub Container Registry (GHCR)
- Automated deployment to server

---

# 🚀 CI/CD Pipeline (Production Ready)

Implemented using **GitHub Actions**

### CI Includes

- Backend linting, formatting, tests, coverage
- Frontend linting & testing
- AI service linting & tests
- Dependency caching
- Coverage artifact uploads

### CD Includes

- Docker image build using Buildx
- Push images to **GitHub Container Registry**
- Automatic deployment via **SSH to VPS**
- Concurrency control for safe deployments

Pipeline configuration file:
.github/workflows/ci.yml

---

# 📁 Repository Structure
smart-university-management-system/

│

├── backend/

├── frontend/

├── ai-service/

├── elk/

├── docker-compose.yml

├── .github/

│ └── workflows/

│ └── ci.yml

└── README.md

---

# 📥 Installation & Setup

Clone the project:
```bash
git clone <https://github.com/Ghazalees/smart-university-management-system.git>
cd smart-university-management-system
```

Run all services:
```bash
docker compose up -d
```

This will start:
Backend
Frontend
AI Service
ELK Stack

# 👨‍💻 Contributors
Ghazale Eslami, Masoumeh Mokhtari, Ali Rajabi, Arya Gheyratmand

Supervisor: Dr. Lotfi

Tarbiat Modares University

# 📄 License
This project is developed for academic and research purposes as part of the:
Advanced Software Engineering Course — Tarbiat Modares University