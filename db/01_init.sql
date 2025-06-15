CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE candidates (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    tg_id        BIGINT      NOT NULL,
    vacancy      TEXT        NOT NULL,
    full_name    TEXT        NOT NULL,
    phone        TEXT        NOT NULL,
    experience   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

docker compose exec db psql -U hr -d hrdb -c "SELECT * FROM candidates ORDER BY created_at DESC;"
