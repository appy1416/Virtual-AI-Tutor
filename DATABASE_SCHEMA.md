# EduTwin AI - Database Schema Specification

This document provides the database schema for PostgreSQL including pgvector extensions. All SQL DDL statements conform to production requirements (constraints, indices, proper types, and automatic timestamp updates).

---

## Enabled Database Extensions

```sql
-- For generating secure UUIDs (Universally Unique Identifiers)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- For handling high-dimensional vector embeddings of text chunks
CREATE EXTENSION IF NOT EXISTS "vector";
```

---

## DDL Schema Definitions

Below is the complete SQL creation script. Run this in your database initialization process or configure it inside Alembic migrations.

```sql
-- =============================================================================
-- 1. USERS & PROFILES
-- =============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    full_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en' NOT NULL,
    learning_level VARCHAR(50) DEFAULT 'beginner' NOT NULL, -- beginner, intermediate, advanced
    learning_goals TEXT,
    study_streak_days INTEGER DEFAULT 0 NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- =============================================================================
-- 2. KNOWLEDGE BASE & DOCUMENT RAG STORAGE
-- =============================================================================

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(512),
    file_type VARCHAR(50) NOT NULL, -- pdf, txt, markdown
    uploaded_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_doc_uploader FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    -- 1536 is standard dimension size for OpenAI text-embedding-3-small / text-embedding-ada-002
    embedding VECTOR(1536), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_chunk_document FOREIGN KEY (document_id) REFERENCES knowledge_documents (id) ON DELETE CASCADE,
    CONSTRAINT uq_chunk_index UNIQUE (document_id, chunk_index)
);

-- =============================================================================
-- 3. TUTOR SESSIONS & DIALOGUES
-- =============================================================================

CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255) DEFAULT 'New Chat Session' NOT NULL,
    subject VARCHAR(100), -- Physics, Maths, Computer Science
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    sender VARCHAR(20) NOT NULL, -- user, system, ai
    content TEXT NOT NULL,
    -- Tracks token count for optimization and analytics billing
    token_count INTEGER DEFAULT 0 NOT NULL,
    -- Stores specific database references (UUIDs) of documents referenced by the tutor during search
    referenced_chunk_ids UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_message_session FOREIGN KEY (session_id) REFERENCES learning_sessions (id) ON DELETE CASCADE,
    CONSTRAINT chk_sender CHECK (sender IN ('user', 'system', 'ai'))
);

-- =============================================================================
-- 4. SPACED REPETITION (FLASHCARDS)
-- =============================================================================

CREATE TABLE spaced_repetition_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    subject VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    -- SuperMemo-2 (SM-2) scheduling variables
    easiness_factor DOUBLE PRECISION DEFAULT 2.5 NOT NULL,
    repetitions INTEGER DEFAULT 0 NOT NULL,
    interval_days INTEGER DEFAULT 0 NOT NULL,
    next_review_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_card_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE card_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL,
    user_id UUID NOT NULL,
    rating INTEGER NOT NULL, -- 0 to 5 SM-2 rating scale
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_review_card FOREIGN KEY (card_id) REFERENCES spaced_repetition_cards (id) ON DELETE CASCADE,
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT chk_rating CHECK (rating >= 0 AND rating <= 5)
);

-- =============================================================================
-- 5. ANALYTICS & TELEMETRY
-- =============================================================================

CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- page_view, chat_prompt, flashcard_review, quiz_submit
    event_details JSONB, -- metadata properties
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_event_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

---

## Performance & Optimization Indexes

To support low latency queries, we implement indexes on foreign keys, text search vectors, and spatial cosine distance operations:

```sql
-- Authentication Lookups
CREATE INDEX idx_users_email ON users(email);

-- Session Queries
CREATE INDEX idx_sessions_user ON learning_sessions(user_id);
CREATE INDEX idx_messages_session ON chat_messages(session_id);

-- Flashcard Scheduling Lookups
CREATE INDEX idx_flashcards_user_review ON spaced_repetition_cards(user_id, next_review_at);

-- Telemetry Event Queries
CREATE INDEX idx_analytics_user_event ON analytics_events(user_id, event_type);

-- Vector Similarity Search Index (HNSW - Hierarchical Navigable Small World)
-- Using cosine distance metrics (<=>) for high dimension embedding search
CREATE INDEX idx_chunks_embedding_hnsw 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops);
```

---

## DDL Schema Architecture Rules

1. **UUID Core Identifiers**: Ensure all tables use `UUID` rather than auto-incrementing integers. This avoids primary key collisions during distributed processing and prevents id-enumeration security vulnerabilities.
2. **Cascading Deletes**: Cascading deletes are enforced on user dependencies (`user_profiles`, `learning_sessions`, `spaced_repetition_cards`, `analytics_events`).
3. **Optimized Embedding Retrieval**: The `HNSW` index on `document_chunks.embedding` is chosen over `IVFFlat` because it offers better recall accuracy and doesn't require regular rebuilding as the knowledge base scale changes.
4. **JSONB Data Types**: We use standard PostgreSQL `JSONB` format for analytics metadata. This allows backend engineers to append ad-hoc tracking keys (e.g. device configurations, browser strings, specific button classes clicked) without requiring frequent schema alterations.
