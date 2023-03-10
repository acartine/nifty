-- short url table
-- depends: 20230126_01_CPEEL-long-url-table
CREATE TABLE IF NOT EXISTS short_url(
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  url TEXT NOT NULL UNIQUE
);
GRANT SELECT, INSERT, UPDATE, DELETE
ON short_url
TO flask_rw;
GRANT USAGE
ON SEQUENCE short_url_id_seq
TO flask_rw;
