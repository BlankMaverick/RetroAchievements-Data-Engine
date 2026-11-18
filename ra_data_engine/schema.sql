CREATE TABLE IF NOT EXISTS collection_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    profile JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_api_responses (
    run_id BIGINT NOT NULL REFERENCES collection_runs(run_id) ON DELETE CASCADE,
    response_name TEXT NOT NULL,
    source_key TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    PRIMARY KEY (run_id, response_name, source_key)
);

CREATE TABLE IF NOT EXISTS games (
    game_id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    console_id BIGINT,
    console_name TEXT
);

CREATE TABLE IF NOT EXISTS game_progress (
    run_id BIGINT NOT NULL REFERENCES collection_runs(run_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    max_possible INTEGER,
    num_awarded INTEGER,
    num_awarded_hardcore INTEGER,
    most_recent_awarded_at TIMESTAMPTZ,
    PRIMARY KEY (run_id, game_id)
);

CREATE TABLE IF NOT EXISTS game_point_progress (
    run_id BIGINT NOT NULL REFERENCES collection_runs(run_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    possible_score INTEGER,
    score_achieved INTEGER,
    PRIMARY KEY (run_id, game_id)
);

CREATE TABLE IF NOT EXISTS achievement_progress (
    run_id BIGINT NOT NULL REFERENCES collection_runs(run_id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(game_id),
    achievement_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    points INTEGER,
    community_awarded_count INTEGER,
    community_player_count INTEGER,
    date_earned TIMESTAMPTZ,
    date_earned_hardcore TIMESTAMPTZ,
    PRIMARY KEY (run_id, game_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_game_progress_run_awarded
    ON game_progress (run_id, num_awarded, max_possible);
CREATE INDEX IF NOT EXISTS idx_point_progress_run
    ON game_point_progress (run_id, score_achieved, possible_score);
