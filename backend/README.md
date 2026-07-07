# EduTwin AI Backend - FastAPI Service

The backend is built with FastAPI (Python), offering async database operations, built-in validation schemas, Celery tasks, and tight integration with AI providers.

## Project Structure

```text
backend/
├── app/
│   ├── api/          # Route handlers (auth, chat, analytics)
│   ├── core/         # Global configuration, database sessions, security modules
│   ├── models/       # SQLAlchemy relational database models
│   ├── schemas/      # Pydantic serialization & request/response schemas
│   ├── services/     # Core logic (AI/LLM pipelines, recommendations)
│   └── tasks/        # Celery worker background tasks
├── tests/            # Integration & unit test suites
├── requirements.txt  # Python package dependencies
├── alembic.ini       # DB migration config file
└── README.md         # This manual
```

---

## Local Setup Instructions (Without Docker)

### 1. Set Up a Virtual Environment
```bash
cd backend
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment variables
Copy `.env.example` to `.env` and fill in:
- Postgres credentials
- Redis broker paths
- OpenAI/Gemini/Anthropic API keys

### 4. Apply Database Migrations (Alembic)
```bash
alembic upgrade head
```

### 5. Start the FastAPI Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

---

## Celery & Redis Setup

The backend utilizes Celery for async computations (e.g., scoring text, generating lesson plans, compiling user performance).

### Run Celery Worker
Ensure Redis is running, then launch:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

### Run Celery Beat (Scheduler)
For scheduled tasks (like daily reviews or email digests):
```bash
celery -A app.core.celery_app beat --loglevel=info
```

---

## Testing

We use pytest for unit and integration testing:
```bash
pytest
```
Add coverage metrics:
```bash
pytest --cov=app tests/
```
