-- link table
-- depends: 20230126_02_8KwAi-short-url-table
REVOKE USAGE
ON SEQUENCE link_id_seq
FROM flask_rw;
REVOKE SELECT, INSERT, UPDATE, DELETE
ON link
FROM flask_rw;
DROP INDEX link_long_url_id_idx;
DROP TABLE link;
