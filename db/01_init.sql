CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE IF NOT EXISTS candidates (
    id          UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    tg_id       BIGINT       NOT NULL, -- ID пользователя в Telegram
    vacancy     TEXT         NOT NULL, -- код вакансии из deeplink
    answers     JSONB        NOT NULL DEFAULT '{}'::jsonb, -- все ответы анкеты
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_candidates_vacancy_created
    ON candidates (vacancy, created_at DESC);