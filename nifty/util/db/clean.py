import psycopg
from psycopg import sql
from redis import Redis


def clean_postgres():
    conninfo = "postgresql://postgres:mypassword@localhost/postgres"
    tables = ["link", "long_url", "short_url"]
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            for t in tables:
                cur.execute(sql.SQL("DELETE FROM {0}").format(sql.Identifier(t)))
                print(f"{t} -> deleted SQL row count [{cur.rowcount}]")


def clean_redis(name: str, port: int):
    with Redis(
        host="localhost", password="mypassword", decode_responses=True, port=port
    ) as redis:
        # hack until we get trending size straightened out
        keys = [k for k in redis.keys() if k != "nifty:trending:size"]
        with redis.pipeline() as p:
            for k in keys:
                p.delete(k)
            result = p.execute()
            print(f"Deleted Redis({name})row count [{sum(result)}]")
            print(f"Remaining redis keys: {redis.keys()}")


def clean():
    clean_postgres()
    clean_redis("std", 6379)
    clean_redis("cache", 6380)


if __name__ == "__main__":
    clean()
