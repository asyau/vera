# Vera

**An AI workspace that turns team conversations into structured work.**

Vera is an open-source full-stack prototype for capturing conversations, extracting actionable tasks, organizing teams and projects, and retrieving shared context from one workspace.

## Problem

Important decisions and assignments are often buried in chat. Teams then spend time rewriting conversations into tasks, checking ownership manually, and rebuilding context across separate tools.

## Approach

Vera combines a typed web client, a domain-oriented API, and AI-assisted workflows:

- Team conversations can be summarized or converted into structured tasks.
- Tasks include status, priority, due date, creator, assignee, project, and conversation context.
- Company, project, team, user, conversation, and messaging modules provide the surrounding workspace model.
- PostgreSQL stores relational records; pgvector-backed columns are available for document chunks and memory vectors.
- OpenAI-powered services handle chat, task extraction, summaries, briefings, and audio transcription.
- The React client provides protected routes for dashboards, tasks, users, profiles, settings, chat, and daily briefings.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Radix UI |
| Client state and data | TanStack Query, Axios, React Context |
| Backend | FastAPI, Pydantic, SQLAlchemy, Uvicorn |
| Database | PostgreSQL, pgvector, Alembic |
| AI and audio | OpenAI API, Whisper API, optional ElevenLabs TTS |
| Auth and monitoring | JWT, bcrypt, Sentry |

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL with the `vector` extension
- An OpenAI API key

### Backend

```bash
git clone https://github.com/asyau/vera.git
cd vera/vera_backend

python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

Create `vera_backend/.env` with your own development credentials:

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/vera
JWT_SECRET_KEY=replace_with_a_long_random_value
```

Initialize the schema and start the API:

```bash
python -m app.init_db
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

### Frontend

In another terminal:

```bash
cd vera/vera_frontend
npm install
npm run dev
```

The client expects the API at `http://localhost:8000/api`. To enable text-to-speech, provide `VITE_ELEVEN_LABS_API_KEY` in a local frontend environment file. Never commit real credentials.

## Demo

Check the running backend:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"healthy","message":"Backend is running"}
```

Interactive API demos are available at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

A representative product flow is:

```text
Conversation → AI task extraction → assignee and due-date resolution → task dashboard
```

No hosted public demo or product screenshot is currently included in the repository.

## Results

- The prototype implements nine frontend pages and reusable dashboard, messaging, task, briefing, and authentication components.
- The data model covers 12 entities, including companies, projects, teams, users, tasks, conversations, messages, documents, memory vectors, notifications, and integrations.
- Backend route modules expose CRUD workflows plus AI response, summarization, transcription, team chat, and briefing operations.
- Basic database/authentication scripts and OpenAI integration tests exist, but the repository does not yet include isolated end-to-end tests, CI results, or a production benchmark.

## Project Structure

```text
vera_frontend/
  src/components/     Product and reusable UI components
  src/pages/          Route-level application pages
  src/lib/api.ts      Typed API client and domain interfaces
  src/contexts/       Authentication and session state

vera_backend/
  app/main.py         FastAPI application and router registration
  app/routes/         Domain, messaging, authentication, and AI endpoints
  app/services/       OpenAI workflow implementation
  app/models/         SQLAlchemy and Pydantic models
  alembic/            Database migrations
  tests/              Integration-oriented tests
```

## Next Steps

- Move every runtime credential and endpoint into environment-only configuration and enable repository secret scanning.
- Make the frontend API base URL configurable instead of hard-coding localhost.
- Add Docker Compose for PostgreSQL/pgvector, the API, and the frontend.
- Add isolated unit tests, end-to-end workflow tests, CI, and test fixtures that do not call paid external APIs.
- Consolidate the authentication implementations and enforce authorization consistently across routes.
- Implement and benchmark retrieval over the existing document and memory-vector schema.
- Add product screenshots and publish a stable hosted demo.

## Status

Vera is a research and product prototype. Production deployment requires hardened authentication, secret management, CORS policy, database migrations, and operational monitoring.
