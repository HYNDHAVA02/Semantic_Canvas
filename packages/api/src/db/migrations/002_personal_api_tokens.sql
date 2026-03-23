-- Personal API tokens for agent authentication.
-- Tokens are stored as SHA-256 hashes; plaintext is returned once on creation.

CREATE TABLE IF NOT EXISTS personal_api_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,
    token_hash  TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    expires_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pat_token_hash ON personal_api_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_pat_project ON personal_api_tokens(project_id);
