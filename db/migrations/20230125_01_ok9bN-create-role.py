"""
create role
"""

from yoyo import step
import os

__depends__ = {}

apply_sql = """
DO
$do$
BEGIN
   IF EXISTS (
  SELECT
  FROM
    pg_catalog.pg_roles
  WHERE
    rolname = 'flask_rw'
) THEN
      RAISE NOTICE 'Role "flask_rw" already exists. Skipping.';
ELSE
      CREATE ROLE flask_rw LOGIN PASSWORD '$PG_PWD$';
END IF;
END
$do$;
"""


def get_pwd():
    # TODO this should probably be pulled from secrets manager
    pwd = os.environ.get("NIFTY_PG_PWD")
    if not pwd:
        raise Exception("PG_PWD must be set")
    return pwd


def apply_step(conn):
    cursor = conn.cursor()
    cursor.execute(apply_sql.replace("$PG_PWD$", get_pwd()))


rollback_sql = """
DO
$do$
BEGIN
   IF EXISTS (
  SELECT
  FROM
    pg_catalog.pg_roles
  WHERE
    rolname = 'flask_rw'
) THEN
      DROP ROLE flask_rw;
ELSE
      RAISE NOTICE 'Role "flask_rw" does not exist. Skipping.';
END IF;
END
$do$;
"""


def rollback_step(conn):
    cursor = conn.cursor()
    cursor.execute(rollback_sql)


steps = [step(apply_step, rollback_step)]
