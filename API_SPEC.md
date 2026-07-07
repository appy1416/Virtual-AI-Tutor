# EduTwin AI - API Specification

This document details the HTTP REST endpoints and WebSocket protocols for the EduTwin AI Virtual Tutor. All APIs are prefixed with `/api/v1/` and exchange data using JSON payloads unless specified otherwise.

---

## 1. Authentication Endpoints

### Register User
* **Endpoint**: `POST /auth/register`
* **Description**: Create a new student account.
* **Request Body**:
  ```json
  {
    "email": "student@example.com",
    "password": "StrongPassword123!"
  }
  ```
* **Responses**:
  * **201 Created**:
    ```json
    {
      "id": "a3b9c8d7-e2f4-4d8b-9a1c-3b5f7e9a8b1c",
      "email": "student@example.com",
      "is_active": true,
      "created_at": "2026-07-05T19:00:00Z"
    }
    ```
  * **400 Bad Request** (Email already exists or validation fails).

---

### Login User
* **Endpoint**: `POST /auth/login`
* **Description**: Authenticate credentials and receive access + refresh tokens.
* **Request Body**: Form-data (`username` as email, `password`).
* **Responses**:
  * **200 OK**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJsYXN0X3VwZGF0ZSI6IjIwMjYtMDctMDUi...",
      "token_type": "bearer"
    }
    ```
  * **401 Unauthorized** (Invalid email or password).

---

### Refresh Authentication Token
* **Endpoint**: `POST /auth/refresh`
* **Description**: Issue a new short-lived access token using a valid refresh token.
* **Request Body**:
  ```json
  {
    "refresh_token": "eyJsYXN0X3VwZGF0ZSI6IjIwMjYtMDctMDUi..."
  }
  ```
* **Responses**:
  * **200 OK**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
  * **401 Unauthorized** (Expired or malformed refresh token).

---

## 2. User Profiles

### Get My Profile
* **Endpoint**: `GET /users/me`
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **200 OK**:
    ```json
    {
      "id": "e98e4f1a-6df2-4217-bc45-e2f3a61d8bf2",
      "user_id": "a3b9c8d7-e2f4-4d8b-9a1c-3b5f7e9a8b1c",
      "full_name": "Jane Doe",
      "preferred_language": "en",
      "learning_level": "intermediate",
      "learning_goals": "Master quantum physics basics and calculus",
      "study_streak_days": 5,
      "last_active_at": "2026-07-05T19:02:00Z"
    }
    ```
  * **401 Unauthorized**

---

### Update My Profile
* **Endpoint**: `PATCH /users/me`
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "full_name": "Jane Doe",
    "learning_level": "advanced",
    "learning_goals": "Advanced orbital mechanics formulations"
  }
  ```
* **Responses**:
  * **200 OK**: Profile updated successfully.

---

## 3. Learning Sessions

### List Sessions
* **Endpoint**: `GET /sessions`
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **200 OK**:
    ```json
    [
      {
        "id": "c8d1f2e3-4b5a-6d7e-8f90-1c2b3a4e5f6d",
        "title": "Quantum Mechanics Intro",
        "subject": "Physics",
        "created_at": "2026-07-05T15:30:00Z",
        "updated_at": "2026-07-05T18:45:00Z"
      }
    ]
    ```

---

### Create Session
* **Endpoint**: `POST /sessions`
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "title": "Electromagnetism Lesson 1",
    "subject": "Physics"
  }
  ```
* **Responses**:
  * **201 Created**: Returns the created session resource.

---

### Delete Session
* **Endpoint**: `DELETE /sessions/{id}`
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **204 No Content**
  * **404 Not Found**

---

## 4. Chat & Dialogue

### List Chat History
* **Endpoint**: `GET /sessions/{id}/messages`
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **200 OK**:
    ```json
    [
      {
        "id": "e8c2f1a3-b4d5-6e7f-8a90-b1c2d3e4f5a6",
        "sender": "user",
        "content": "Explain Maxwell's Equations simply.",
        "token_count": 8,
        "created_at": "2026-07-05T18:40:00Z"
      },
      {
        "id": "d2a3f4e5-b1c2-6d7e-8a90-f5a6b7c8d9e0",
        "sender": "ai",
        "content": "Maxwell's Equations are four mathematical laws...",
        "token_count": 210,
        "referenced_chunk_ids": ["c1e2d3b4-f5a6-7b8c-9d0e-1f2a3b4c5d6e"],
        "created_at": "2026-07-05T18:41:12Z"
      }
    ]
    ```

---

### Real-time Voice & Text Stream (WebSockets)
* **Endpoint**: `WSS /sessions/{session_id}/chat/ws`
* **Headers**: Passed via protocol sub-protocol or query parameters (`token=JWT_ACCESS_TOKEN`).
* **Connection Lifecycle**:
  - **Connection Open**: Client connects. Server validates JWT.
  - **Client Message**: Send JSON block representing text query or audio buffer:
    ```json
    {
      "type": "text_query",
      "text": "What is Gauss's Law?"
    }
    ```
  - **Server Stream**: Streams answers in real-time chunks (SSE format over WebSocket frames):
    ```json
    {
      "type": "chat_chunk",
      "message_id": "d2a3f4e5-b1c2-6d7e-8a90-f5a6b7c8d9e0",
      "chunk": "Gauss's law relates "
    }
    ```
  - **Server Citation**: Sends RAG resources matched:
    ```json
    {
      "type": "citation",
      "document_title": "Physics Volume 2",
      "page": 432
    }
    ```
  - **Server Message Complete**: Ends the execution segment.
    ```json
    {
      "type": "complete",
      "total_tokens": 143
    }
    ```

---

## 5. Spaced Repetition (Flashcards)

### List Cards Due
* **Endpoint**: `GET /flashcards`
* **Description**: Retrieve active cards where `next_review_at` is less than or equal to current timestamp.
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **200 OK**:
    ```json
    [
      {
        "id": "f5a6b7c8-d9e0-1f2a-3b4c-5d6e7f8a9b0c",
        "subject": "Physics",
        "question": "What is the speed of light in vacuum?",
        "answer": "299,792,458 meters per second",
        "repetitions": 3,
        "interval_days": 8,
        "next_review_at": "2026-07-05T00:00:00Z"
      }
    ]
    ```

---

### Record Review Score (SM-2 Logic)
* **Endpoint**: `POST /flashcards/{id}/review`
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "rating": 5
  }
  ```
  *Note: Rating scale 0 (forgot completely) to 5 (excellent response delay).*
* **Responses**:
  * **200 OK**: Updates intervals and returns details:
    ```json
    {
      "card_id": "f5a6b7c8-d9e0-1f2a-3b4c-5d6e7f8a9b0c",
      "repetitions": 4,
      "easiness_factor": 2.6,
      "interval_days": 16,
      "next_review_at": "2026-07-21T19:02:00Z"
    }
    ```

---

## 6. Analytics & Telemetry

### Get Analytics Overview
* **Endpoint**: `GET /analytics/overview`
* **Headers**: `Authorization: Bearer <access_token>`
* **Responses**:
  * **200 OK**:
    ```json
    {
      "streak": 5,
      "total_study_minutes": 240,
      "flashcard_mastery_pct": 82.5,
      "subject_mastery": {
        "Physics": 74.0,
        "Mathematics": 91.0
      },
      "retention_history": [
        {"date": "2026-07-01", "score": 0.8},
        {"date": "2026-07-05", "score": 0.85}
      ]
    }
    ```

---

### Track Telemetry Event
* **Endpoint**: `POST /analytics/event`
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "event_type": "flashcard_view",
    "event_details": {
      "card_id": "f5a6b7c8-d9e0-1f2a-3b4c-5d6e7f8a9b0c",
      "time_spent_ms": 4200
    }
  }
  ```
* **Responses**:
  * **202 Accepted**: Telemetry event accepted for queuing.
