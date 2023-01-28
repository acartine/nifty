-- link table
-- depends: 20230126_02_8KwAi-short-url-table
CREATE TABLE IF NOT EXISTS link (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  long_url_id BIGINT NOT NULL REFERENCES long_url(id),
  short_url_id BIGINT NOT NULL UNIQUE REFERENCES short_url(id)
);
CREATE INDEX IF NOT EXISTS link_long_url_id_idx
ON link USING HASH (long_url_id);
GRANT SELECT, INSERT, UPDATE, DELETE
ON link
TO flask_rw;
GRANT USAGE
ON SEQUENCE link_id_seq
TO flask_rw;
