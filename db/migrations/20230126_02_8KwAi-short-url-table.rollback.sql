-- short url table
-- depends: 20230126_01_CPEEL-long-url-table
REVOKE USAGE
ON SEQUENCE short_url_id_seq
FROM flask_rw;
REVOKE SELECT, INSERT, UPDATE, DELETE
ON short_url
FROM flask_rw;
DROP TABLE short_url;
