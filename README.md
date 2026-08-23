# Vera

**An AI workspace that turns team conversations into structured work.**

Vera is an open-source full-stack prototype for teams that need to capture conversations, extract actionable tasks, organize projects, and retrieve shared context without manually translating every discussion into tickets.

## Highlights

- AI-assisted task extraction from team conversations
- Projects, teams, users, and company workspaces
- Conversation history and in-product messaging
- Retrieval over stored context with PostgreSQL and pgvector
- Typed React interface with dashboards and reusable components
- FastAPI backend with interactive OpenAPI documentation

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Radix UI |
| Data fetching | TanStack Query, Axios |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL, pgvector |
| AI | OpenAI API |
| Observability | Sentry |

## Project structure

```text
vera_frontend/    React and TypeScript client
vera_backend/     FastAPI service, routes, and data access
```

## Run locally

### Backend

```bash
cd vera_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`; Swagger UI is available at `/docs`.

### Frontend

```bash
cd vera_frontend
npm install
npm run dev
```

Configure the frontend API URL for your local backend before starting the client.

## Status

Vera is a research and product prototype. It is useful as an architectural reference, but production deployment requires environment-specific authentication, database, CORS, and secret-management configuration.