-- long url table
-- depends: 20230125_01_ok9bN-create-role
CREATE TABLE IF NOT EXISTS long_url(
  id BIGSERIAL PRIMARY KEY,
  url TEXT NOT NULL UNIQUE
);
GRANT SELECT, INSERT, UPDATE, DELETE
ON long_url
TO flask_rw;
