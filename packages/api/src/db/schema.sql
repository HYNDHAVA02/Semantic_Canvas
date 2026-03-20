-- ============================================================
-- SEMANTIC CANVAS: PostgreSQL Schema
-- A project memory layer for AI agents
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- PROJECTS
-- ============================================================

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    description     TEXT,
    repo_url        TEXT,
    default_branch  TEXT DEFAULT 'main',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ENTITIES: services, databases, functions, classes, modules
-- ============================================================

CREATE TABLE entities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL,  -- service | database | queue | frontend | function | class | module | endpoint | table
    source          TEXT NOT NULL DEFAULT 'manual',  -- axon | github | manual | agent | upload
    source_ref      TEXT,
    metadata        JSONB DEFAULT '{}',
    embedding       vector(384),
    is_active       BOOLEAN DEFAULT true,
    last_seen_at    TIMESTAMPTZ DEFAULT now(),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, name, kind)
);

CREATE INDEX idx_entities_project ON entities(project_id);
CREATE INDEX idx_entities_kind ON entities(project_id, kind);
CREATE INDEX idx_entities_source ON entities(project_id, source);
CREATE INDEX idx_entities_name_trgm ON entities USING gin(name gin_trgm_ops);
CREATE INDEX idx_entities_embedding ON entities USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ============================================================
-- RELATIONSHIPS: entity A relates to entity B
-- ============================================================

CREATE TABLE relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    from_entity_id  UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id    UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,  -- calls | depends_on | imports | inherits | implements | owns | reads_from | writes_to
    source          TEXT NOT NULL DEFAULT 'manual',
    source_ref      TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_id, from_entity_id, to_entity_id, kind)
);

CREATE INDEX idx_rel_project ON relationships(project_id);
CREATE INDEX idx_rel_from ON relationships(from_entity_id);
CREATE INDEX idx_rel_to ON relationships(to_entity_id);
CREATE INDEX idx_rel_kind ON relationships(project_id, kind);

-- ============================================================
-- DECISIONS: why the team chose X over Y
-- ============================================================

CREATE TABLE decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    decided_by      TEXT,
    decided_at      DATE,
    entity_ids      UUID[] DEFAULT '{}',
    source          TEXT DEFAULT 'manual',
    source_ref      TEXT,
    embedding       vector(384),
    tags            TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_decisions_project ON decisions(project_id);
CREATE INDEX idx_decisions_embedding ON decisions USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_decisions_title_trgm ON decisions USING gin(title gin_trgm_ops);

-- ============================================================
-- CONVENTIONS: living rules the team follows
-- ============================================================

CREATE TABLE conventions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    scope           TEXT,  -- global | backend | frontend | database | <service-name>
    source          TEXT DEFAULT 'manual',
    source_ref      TEXT,
    embedding       vector(384),
    tags            TEXT[] DEFAULT '{}',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conventions_project ON conventions(project_id);
CREATE INDEX idx_conventions_embedding ON conventions USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ============================================================
-- ACTIVITY LOG: what changed, when, why
-- ============================================================

CREATE TABLE activity_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    summary         TEXT NOT NULL,
    detail          TEXT,
    entity_ids      UUID[] DEFAULT '{}',
    source          TEXT NOT NULL,  -- github | axon | manual | agent
    source_ref      TEXT,
    actor           TEXT,
    embedding       vector(384),
    occurred_at     TIMESTAMPTZ DEFAULT now(),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_activity_project ON activity_log(project_id);
CREATE INDEX idx_activity_time ON activity_log(project_id, occurred_at DESC);
CREATE INDEX idx_activity_embedding ON activity_log USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ============================================================
-- DOCUMENTS: uploaded PRDs, runbooks, architecture docs
-- ============================================================

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    file_name       TEXT,
    mime_type       TEXT,
    uploaded_by     TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    chunk_index     INT NOT NULL,
    embedding       vector(384),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chunks_doc ON document_chunks(document_id);
CREATE INDEX idx_chunks_project ON document_chunks(project_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
