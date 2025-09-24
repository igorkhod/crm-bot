CREATE TABLE IF NOT EXISTS homework_delivery (
  id         INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  user_id    INTEGER NOT NULL,
  link       TEXT NOT NULL,
  sent_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, user_id)
);
