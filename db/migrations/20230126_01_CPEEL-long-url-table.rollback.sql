-- long url table
-- depends: 20230125_01_ok9bN-create-role
REVOKE SELECT, INSERT, UPDATE, DELETE
ON long_url
FROM flask_rw;
DROP TABLE IF EXISTS long_url;