# EduTwin AI - Deployment & Orchestration Manual

This document details configurations for containerizing and running the EduTwin AI stack locally and in production environments.

---

## 1. Local Orchestration (Docker Compose)

Create a root `docker-compose.yml` to spin up the local environment.

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:15-pg15
    container_name: edutwin_postgres
    restart: always
    environment:
      POSTGRES_USER: edutwin_admin
      POSTGRES_PASSWORD: secure_password_here
      POSTGRES_DB: edutwin_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: edutwin_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: edutwin_backend
    restart: always
    depends_on:
      - postgres
      - redis
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: edutwin_celery_worker
    restart: always
    depends_on:
      - redis
      - postgres
    env_file:
      - ./backend/.env
    command: celery -A app.core.celery_app worker --loglevel=info

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: edutwin_celery_beat
    restart: always
    depends_on:
      - redis
      - postgres
    env_file:
      - ./backend/.env
    command: celery -A app.core.celery_app beat --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: edutwin_frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## 2. Dockerfile Blueprints

### Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
# Multi-stage build for Python service optimization
FROM python:3.11-slim AS builder

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /code/wheels -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /code/wheels /wheels
COPY --from=builder /code/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY . .

# Run as non-privileged system user for container security hardening
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
```

### Frontend Dockerfile (`frontend/Dockerfile`)
```dockerfile
# Build React application
FROM node:18-alpine AS build-stage

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Nginx web server for production build delivery
FROM nginx:stable-alpine AS production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## 3. Production Nginx Configuration

Save this as `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    # Static file hosting with single page fallback routes
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Proxy REST API requests to FastAPI container
    location /api/v1/ {
        proxy_pass http://backend:8000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy WebSocket connection for streaming dialogue
    location /api/v1/chat/ws {
        proxy_pass http://backend:8000/api/v1/chat/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 4. Production Readiness Checklist

Before pushing this application to production infrastructure (e.g. AWS ECS, GCP Cloud Run, or Kubernetes), complete the following steps:

### Security Setup
- [ ] **SSL/TLS Certificates**: Issue Let's Encrypt certificates using certbot and configure Nginx to force TLS 1.3 encryption.
- [ ] **Environment Secret Isolation**: Use external secret managers (AWS Secrets Manager, HashiCorp Vault) to inject database credentials and third-party LLM API keys. Do not store secrets in standard `.env` files inside repository logs.
- [ ] **CORS Origins**: Set strict whitelist origins in `BACKEND_CORS_ORIGINS` to prevent Cross-Origin vulnerability vectors.
- [ ] **User Permission Check**: Ensure Docker containers execute tasks under non-root system users (`USER appuser` in backend Dockerfile).

### Database Configuration
- [ ] **Relational Scaling**: Enable connection pooling (such as PgBouncer) to handle spikes in request counts without exhausting Postgres connections.
- [ ] **Backup Schedule**: Set cron scripts to trigger database snapshots and save snapshots to secured external Object Storage (S3 / GCS).
- [ ] **Embedding Index Rebuilds**: Ensure pgvector indices (`HNSW`) are regularly monitored and optimized for recall statistics as data volume changes.

### Caching & Background Processing
- [ ] **Memory Allocations**: Set maximum memory allocation boundaries on Redis cache stores (`maxmemory` policies) to prevent Out of Memory failures.
- [ ] **Task Deadlocks**: Set task timeouts on Celery tasks to prevent infinite execution loops from locking resources.
- [ ] **Worker Scaling**: Scale Celery worker instances independently of FastAPI servers based on active job queues.
