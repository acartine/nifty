-- link table
-- depends: 20230126_02_8KwAi-short-url-table
REVOKE SELECT, INSERT, UPDATE, DELETE
ON link
FROM flask_rw;
DROP INDEX link_long_url_id_idx;
DROP TABLE link;
