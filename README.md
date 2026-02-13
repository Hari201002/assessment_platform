# Assessment Ops Mini Platform

## Tech Stack
- Backend: FastAPI
- Database: PostgreSQL
- Frontend: React
- Logging: Structured JSON (Monolog-style)
- Migrations: Alembic
- Containerization: Docker Compose

---

## Features

- Ingest student attempt events (batch)
- Normalize student identity (gmail alias handling)
- Deduplicate attempts (time + similarity threshold)
- Compute scores based on negative_marking JSON
- Leaderboard with ranking rules
- Manual Recompute & Flag
- Structured JSON logs with request_id
- React dashboard

---

## Run Without Docker

### Backend

```bash
cd backend
alembic upgrade head
uvicorn main:app --reload

```

### Frontend

```bash
cd frontend
npm install
npm start

```

### Run with docker

```bash
docker-compose up --build